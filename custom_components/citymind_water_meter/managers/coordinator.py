from asyncio import sleep
import calendar
from datetime import datetime
import logging
import sys
from typing import Callable

from homeassistant.components.homeassistant import SERVICE_RELOAD_CONFIG_ENTRY
from homeassistant.const import ATTR_STATE
from homeassistant.core import Event, callback
from homeassistant.helpers.device_registry import (
    DeviceInfo,
    async_entries_for_config_entry as devices_by_config_entry,
    async_get as async_get_device_registry,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry as entities_by_config_entry,
    async_get as async_get_entity_registry,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import (
    ACTION_ENTITY_SET_NATIVE_VALUE,
    ACTION_ENTITY_TURN_OFF,
    ACTION_ENTITY_TURN_ON,
    ALERT_MAPPING,
    ATTR_ACTIONS,
    ATTR_ALERT_TYPE,
    ATTR_IS_ON,
    ATTR_MEDIA_TYPE,
    DOMAIN,
    ENTITY_CONFIG_ENTRY_ID,
    HA_NAME,
    RECONNECT_INTERVAL,
    SIGNAL_ACCOUNT_ADDED,
    SIGNAL_API_STATUS,
    SIGNAL_DATA_CHANGED,
    SIGNAL_METER_ADDED,
    UPDATE_DATA_INTERVALS,
    WEEKEND_DAYS,
)
from ..common.entity_descriptions import PLATFORMS, IntegrationEntityDescription
from ..common.enums import EntityKeys, EntityType
from ..data_processors.account_processor import AccountProcessor
from ..data_processors.base_processor import BaseProcessor
from ..data_processors.meter_processor import MeterProcessor
from ..models.account_data import AccountData
from .config_manager import ConfigManager
from .rest_api import RestAPI

_LOGGER = logging.getLogger(__name__)


class Coordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    _api: RestAPI
    _processors: dict[EntityType, BaseProcessor] | None = None
    _is_weekend: bool = False

    _data_mapping: (
        dict[
            str,
            Callable[[IntegrationEntityDescription], dict | None]
            | Callable[[IntegrationEntityDescription, str], dict | None],
        ]
        | None
    )
    _system_status_details: dict | None

    _last_update: float

    def __init__(self, hass, config_manager: ConfigManager):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=config_manager.entry_title,
            update_interval=self.current_update_interval,
            update_method=self._async_update_data,
        )

        _LOGGER.debug("Initializing")

        config_data = config_manager.config_data
        analytic_periods = config_manager.analytic_periods
        entry_id = config_manager.entry_id

        self._api = RestAPI(self.hass, config_data, analytic_periods, entry_id)

        self._config_manager = config_manager

        self._data_mapping = None

        self._last_update = 0
        self._is_weekend = False

        self._can_load_components: bool = False

        self._account_processor = AccountProcessor(config_manager)
        self._meter_processor = MeterProcessor(config_manager)

        self._discovered_objects = []

        self._processors = {
            EntityType.ACCOUNT: self._account_processor,
            EntityType.METER: self._meter_processor,
        }

        self._load_signal_handlers()

        _LOGGER.debug("Initializing done")

    @property
    def account(self) -> AccountData | None:
        system = self._account_processor.get()

        return system

    @property
    def api(self) -> RestAPI:
        api = self._api

        return api

    @property
    def config_manager(self) -> ConfigManager:
        config_manager = self._config_manager

        return config_manager

    @property
    def current_update_interval(self):
        current_update_interval = UPDATE_DATA_INTERVALS[self._is_weekend]

        return current_update_interval

    async def on_home_assistant_start(self, _event_data: Event):
        await self.initialize()

    async def initialize(self):
        self._build_data_mapping()

        entry = self.config_manager.entry
        await self.hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info(f"Start loading {DOMAIN} integration, Entry ID: {entry.entry_id}")

        await self.async_request_refresh()

        await self._api.initialize()

    def _load_signal_handlers(self):
        loop = self.hass.loop

        @callback
        def on_api_status_changed(entry_id: str, status: ConnectivityStatus):
            loop.create_task(self._on_api_status_changed(entry_id, status)).__await__()

        @callback
        def on_data_changed(entry_id: str):
            loop.create_task(self._on_data_changed(entry_id)).__await__()

        signal_handlers = {
            SIGNAL_API_STATUS: self._on_api_status_changed,
            SIGNAL_DATA_CHANGED: self._on_data_changed,
        }

        _LOGGER.debug(f"Registering signals for {signal_handlers.keys()}")

        for signal in signal_handlers:
            handler = signal_handlers[signal]

            self._config_manager.entry.async_on_unload(
                async_dispatcher_connect(self.hass, signal, handler)
            )

    def get_debug_data(self) -> dict:
        config_data = self._config_manager.get_debug_data()

        data = {
            "config": config_data,
            "data": {
                "api": self._api.data,
            },
            "processors": {
                EntityType.ACCOUNT: self._account_processor.get().to_dict(),
                EntityType.METER: self._meter_processor.get_all(),
            },
        }

        return data

    async def _on_api_status_changed(self, entry_id: str, status: ConnectivityStatus):
        if entry_id != self._config_manager.entry_id:
            return

        if status == ConnectivityStatus.Connected:
            self.config_manager.analytic_periods.update()

            await self._api.update()

        elif status in [ConnectivityStatus.Failed]:
            await sleep(RECONNECT_INTERVAL.total_seconds())

            await self._api.initialize()

    def _on_account_discovered(self) -> None:
        key = EntityType.ACCOUNT

        if key not in self._discovered_objects:
            self._discovered_objects.append(key)

            async_dispatcher_send(
                self.hass,
                SIGNAL_ACCOUNT_ADDED,
                self._config_manager.entry_id,
                key,
            )

    def _on_meter_discovered(self, meter_id: str) -> None:
        key = f"{EntityType.METER} {meter_id}"

        if key not in self._discovered_objects:
            self._discovered_objects.append(key)

            async_dispatcher_send(
                self.hass,
                SIGNAL_METER_ADDED,
                self._config_manager.entry_id,
                EntityType.METER,
                meter_id,
            )

    async def _on_data_changed(self, entry_id: str):
        if entry_id != self._config_manager.entry_id:
            return

        api_connected = self._api.status == ConnectivityStatus.Connected

        if api_connected:
            for processor_type in self._processors:
                processor = self._processors[processor_type]
                processor.update(self._api.data)

            account = self._account_processor.get()

            if account is None:
                return

            self._on_account_discovered()

            meters = self._meter_processor.get_meters()

            for meter_id in meters:
                self._on_meter_discovered(meter_id)

    async def _async_update_data(self):
        """
        Fetch parameters from API endpoint.

        This is the place to pre-process the parameters to lookup tables
        so entities can quickly look up their parameters.
        """
        try:
            _LOGGER.debug("Updating data")

            self.config_manager.analytic_periods.update()

            await self._api.update()

            self._validate_weekday()

            return {}

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    def _build_data_mapping(self):
        _LOGGER.debug("Building data mappers")

        data_mapping = {
            EntityKeys.CONSUMPTION_FORECAST: self._get_consumption_forecast_data,
            EntityKeys.LAST_READ: self._get_last_read_data,
            EntityKeys.MONTHLY_CONSUMPTION: self._get_monthly_consumption_data,
            EntityKeys.TODAYS_CONSUMPTION: self._get_todays_consumption_data,
            EntityKeys.YESTERDAYS_CONSUMPTION: self._get_yesterdays_consumption_data,
            EntityKeys.HIGH_RATE_CONSUMPTION: self._get_high_rate_consumption_data,
            EntityKeys.LOW_RATE_CONSUMPTION: self._get_low_rate_consumption_data,
            EntityKeys.LOW_RATE_COST: self._get_low_rate_cost_data,
            EntityKeys.LOW_RATE_TOTAL_COST: self._get_low_rate_total_cost_data,
            EntityKeys.HIGH_RATE_COST: self._get_high_rate_cost_data,
            EntityKeys.HIGH_RATE_TOTAL_COST: self._get_high_rate_total_cost_data,
            EntityKeys.SEWAGE_COST: self._get_sewage_cost_data,
            EntityKeys.SEWAGE_TOTAL_COST: self._get_sewage_total_cost_data,
            EntityKeys.LOW_RATE_CONSUMPTION_THRESHOLD: self._get_low_rate_consumption_threshold_data,
            EntityKeys.ALERTS: self._get_alerts_data,
            EntityKeys.ALERT_EXCEEDED_THRESHOLD_SMS: self._get_alert_setting_data,
            EntityKeys.ALERT_EXCEEDED_THRESHOLD_EMAIL: self._get_alert_setting_data,
            EntityKeys.ALERT_LEAK_SMS: self._get_alert_setting_data,
            EntityKeys.ALERT_LEAK_EMAIL: self._get_alert_setting_data,
            EntityKeys.ALERT_LEAK_WHILE_AWAY_SMS: self._get_alert_setting_data,
            EntityKeys.ALERT_LEAK_WHILE_AWAY_EMAIL: self._get_alert_setting_data,
            EntityKeys.USE_UNIQUE_DEVICE_NAMES: self._get_use_unique_device_names_data,
        }

        self._data_mapping = data_mapping

    def get_device_info(
        self,
        entity_description: IntegrationEntityDescription,
        item_id: str | None = None,
    ) -> DeviceInfo:
        processor = self._processors[entity_description.entity_type]

        device_info = processor.get_device_info(item_id)

        return device_info

    def get_data(
        self,
        entity_description: IntegrationEntityDescription,
        item_id: str | None = None,
    ) -> dict | None:
        result = None

        try:
            handler = self._data_mapping.get(entity_description.key)

            if handler is None:
                _LOGGER.warning(
                    f"Handler was not found for {entity_description.key}, Entity Description: {entity_description}"
                )

            else:
                if entity_description.entity_type == EntityType.ACCOUNT:
                    result = handler(entity_description)

                else:
                    result = handler(entity_description, item_id)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to extract data for {entity_description}, Error: {ex}, Line: {line_number}"
            )

        return result

    def get_device_identifiers(
        self, entity_type: EntityType, item_id: str | None = None
    ) -> set[tuple[str, str]]:
        if entity_type == EntityType.METER:
            device_info = self._meter_processor.get_device_info(item_id)

        else:
            device_info = self._account_processor.get_device_info()

        identifiers = device_info.get("identifiers")

        return identifiers

    def get_device_data(self, model: str, identifiers: set[tuple[str, str]]):
        if model == str(EntityType.METER):
            device_data = self._meter_processor.get_meter(identifiers)

        else:
            device_data = self._account_processor.get().to_dict()

        return device_data

    def get_device_action(
        self,
        entity_description: IntegrationEntityDescription,
        item_id: str | None,
        action_key: str,
    ) -> Callable:
        device_data = self.get_data(entity_description, item_id)

        actions = device_data.get(ATTR_ACTIONS)
        async_action = actions.get(action_key)

        return async_action

    def _get_consumption_forecast_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {
            ATTR_STATE: data.consumption_forecast,
        }

        return result

    def _get_last_read_data(self, _entity_description, meter_id: str) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {
            ATTR_STATE: data.last_read,
        }

        return result

    def _get_monthly_consumption_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.monthly_consumption}

        return result

    def _get_todays_consumption_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.today_consumption}

        return result

    def _get_yesterdays_consumption_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.yesterday_consumption}

        return result

    def _get_high_rate_consumption_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.high_rate_monthly_consumption}

        return result

    def _get_low_rate_consumption_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.low_rate_monthly_consumption}

        return result

    def _get_low_rate_cost_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {
            ATTR_STATE: data.low_rate_cost,
            ATTR_ACTIONS: {
                ACTION_ENTITY_SET_NATIVE_VALUE: self._set_low_rate_cost,
            },
        }

        return result

    def _get_low_rate_total_cost_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.low_rate_cost * data.low_rate_monthly_consumption}

        return result

    def _get_high_rate_cost_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {
            ATTR_STATE: data.high_rate_cost,
            ATTR_ACTIONS: {
                ACTION_ENTITY_SET_NATIVE_VALUE: self._set_high_rate_cost,
            },
        }

        return result

    def _get_high_rate_total_cost_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.high_rate_cost * data.high_rate_monthly_consumption}

        return result

    def _get_sewage_cost_data(self, _entity_description, meter_id: str) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {
            ATTR_STATE: data.sewage_cost,
            ATTR_ACTIONS: {
                ACTION_ENTITY_SET_NATIVE_VALUE: self._set_sewage_cost,
            },
        }

        return result

    def _get_sewage_total_cost_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {ATTR_STATE: data.sewage_cost * data.monthly_consumption}

        return result

    def _get_low_rate_consumption_threshold_data(
        self, _entity_description, meter_id: str
    ) -> dict | None:
        data = self._meter_processor.get_data(meter_id)

        result = {
            ATTR_STATE: data.low_rate_consumption_threshold,
            ATTR_ACTIONS: {
                ACTION_ENTITY_SET_NATIVE_VALUE: self._set_low_rate_consumption_threshold,
            },
        }

        return result

    def _get_alerts_data(self, _entity_description) -> dict | None:
        data = self._account_processor.get()

        result = {ATTR_STATE: data.alerts}

        return result

    def _get_use_unique_device_names_data(self, _entity_description) -> dict | None:
        is_on = self._config_manager.use_unique_device_names

        result = {
            ATTR_IS_ON: is_on,
            ATTR_ACTIONS: {
                ACTION_ENTITY_TURN_ON: self._set_use_unique_device_names_enabled,
                ACTION_ENTITY_TURN_OFF: self._set_use_unique_device_names_disabled,
            },
        }

        return result

    def _get_alert_setting_data(self, entity_description) -> dict | None:
        account = self._account_processor.get()
        is_on = account.alert_settings.get(entity_description.key, False)

        result = {
            ATTR_IS_ON: is_on,
            ATTR_ACTIONS: (
                {
                    ACTION_ENTITY_TURN_ON: self._set_alert_setting_enabled,
                    ACTION_ENTITY_TURN_OFF: self._set_alert_setting_disabled,
                }
                if entity_description.key != EntityKeys.ALERT_LEAK_EMAIL
                else None
            ),
        }

        return result

    async def _set_low_rate_consumption_threshold(
        self, _entity_description, meter_id: str, value: float
    ):
        _LOGGER.debug(
            f"Set low rate consumption threshold, Meter: {meter_id}, Value: {value}"
        )
        await self._config_manager.set_low_rate_consumption_threshold(meter_id, value)

        await self.async_request_refresh()

    async def _set_low_rate_cost(
        self, _entity_description, meter_id: str, value: float
    ):
        _LOGGER.debug(f"Set low rate cost, Meter: {meter_id}, Value: {value}")
        await self._config_manager.set_low_rate_cost(meter_id, value)

        await self.async_request_refresh()

    async def _set_high_rate_cost(
        self, _entity_description, meter_id: str, value: float
    ):
        _LOGGER.debug(f"Set high rate cost, Meter: {meter_id}, Value: {value}")
        await self._config_manager.set_high_rate_cost(meter_id, value)

        await self.async_request_refresh()

    async def _set_sewage_cost(self, _entity_description, meter_id: str, value: float):
        _LOGGER.debug(f"Set sewage cost, Meter: {meter_id}, Value: {value}")
        await self._config_manager.set_sewage_cost(meter_id, value)

        await self.async_request_refresh()

    async def _set_use_unique_device_names_enabled(self, _entity_description):
        await self._set_use_unique_device_names_state(True)

    async def _set_use_unique_device_names_disabled(self, _entity_description):
        await self._set_use_unique_device_names_state(False)

    async def _set_use_unique_device_names_state(self, enabled: bool):
        _LOGGER.debug(f"Set unique device name state, Value: {enabled}")

        await self._config_manager.set_use_unique_device_names(enabled)

        await self._remove_and_refresh()

    async def _set_alert_setting_enabled(self, entity_description):
        await self._set_alert_setting_state(entity_description, True)

    async def _set_alert_setting_disabled(self, entity_description):
        await self._set_alert_setting_state(entity_description, False)

    async def _set_alert_setting_state(self, entity_description, enabled: bool):
        _LOGGER.debug(
            f"Set setting state of {entity_description.key}, Value: {enabled}"
        )

        alert_mapping = ALERT_MAPPING.get(entity_description.key)
        alert_type = alert_mapping.get(ATTR_ALERT_TYPE)
        media_type = alert_mapping.get(ATTR_MEDIA_TYPE)

        await self._api.set_alert_settings(alert_type, media_type, enabled)

        await self.async_request_refresh()

    async def _reload_integration(self):
        data = {ENTITY_CONFIG_ENTRY_ID: self.config_manager.entry_id}

        await self.hass.services.async_call(HA_NAME, SERVICE_RELOAD_CONFIG_ENTRY, data)

    def _validate_weekday(self):
        today = datetime.now()
        today_day_name = calendar.day_name[today.weekday()]

        is_weekend = today_day_name in WEEKEND_DAYS

        was_changed = self._is_weekend != is_weekend

        if was_changed:
            self._is_weekend = is_weekend

            self.update_interval = self.current_update_interval

    async def _remove_and_refresh(self):
        entity_registry = async_get_entity_registry(self.hass)
        device_registry = async_get_device_registry(self.hass)

        entities = entities_by_config_entry(entity_registry, self.config_entry.entry_id)
        devices = devices_by_config_entry(device_registry, self.config_entry.entry_id)

        for entity_entry in entities:
            entity_registry.async_remove(entity_entry.entity_id)

        for device_entry in devices:
            device_registry.async_remove_device(device_entry.id)

        await self._reload_integration()
