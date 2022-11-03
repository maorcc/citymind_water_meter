"""
HA Manager.
"""
from __future__ import annotations

import calendar
from datetime import datetime
import logging
import sys

from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_CONFIGURATION_URL, VOLUME_CUBIC_METERS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from ...configuration.managers.configuration_manager import ConfigurationManager
from ...configuration.models.config_data import ConfigData
from ...core.helpers.enums import ConnectivityStatus
from ...core.managers.home_assistant import HomeAssistantManager
from ...core.models.entity_data import EntityData
from ...core.models.select_description import SelectDescription
from ..api.api import IntegrationAPI
from ..api.storage_api import StorageAPI
from ..helpers.const import *

_LOGGER = logging.getLogger(__name__)


class CityMindHomeAssistantManager(HomeAssistantManager):
    def __init__(self, hass: HomeAssistant):
        super().__init__(hass, WEEKDAY_UPDATE_DATA_INTERVAL)

        self._api: IntegrationAPI = IntegrationAPI(self._hass, self._api_data_changed, self._api_status_changed)
        self._storage_api = StorageAPI(self._hass)
        self._config_manager: ConfigurationManager | None = None
        self._is_weekend: bool = False

        self._today_date: datetime | None = None
        self._yesterday_date: datetime | None = None
        self._month_date: datetime | None = None
        self._account_number: str | None = None
        self._provider: str | None = None

    @property
    def api(self) -> IntegrationAPI:
        return self._api

    @property
    def storage_api(self) -> StorageAPI:
        return self._storage_api

    @property
    def config_data(self) -> ConfigData:
        return self._config_manager.get(self.entry_id)

    async def _api_data_changed(self):
        if self.api.status == ConnectivityStatus.Connected:
            await self.storage_api.debug_log_api(self.api.data)

            self._set_metadata()

    async def _api_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.Connected:
            await self.api.async_update()

            self._update_entities(None)

        if status == ConnectivityStatus.NotConnected:
            await self.api.initialize(self.config_data)

    async def async_component_initialize(self, entry: ConfigEntry):
        try:
            self._config_manager = ConfigurationManager(self._hass, self.api)
            await self._config_manager.load(entry)

            await self._validate_weekday(False)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_component_initialize, error: {ex}, line: {line_number}")

    async def async_initialize_data_providers(self):
        await self.storage_api.initialize(self.config_data)
        await self.api.initialize(self.config_data)

    async def async_stop_data_providers(self):
        await self.api.terminate()

    async def async_update_data_providers(self):
        try:
            await self._validate_weekday(True)

            await self.api.async_update()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_update_data_providers, Error: {ex}, Line: {line_number}")

    def _set_metadata(self):
        me_section = self.api.data.get(API_DATA_SECTION_ME)
        account_number_str = me_section.get(ME_ACCOUNT_NUMBER)

        customer_service_section = self.api.data.get(API_DATA_SECTION_CUSTOMER_SERVICE)
        provider = customer_service_section.get(CUSTOMER_SERVICE_DESCRIPTION)

        account_number = int(account_number_str)

        account_name = f"{self.entry_title} {account_number} Account"

        self._account_number = account_name
        self._provider = provider

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        first_day_of_month = today.replace(day=1)

        self._today_date = today
        self._yesterday_date = yesterday
        self._month_date = first_day_of_month

    def _get_meter_name(self, meter_id: str):
        meter_name = f"{self.entry_title} {meter_id} Meter"

        return meter_name

    def load_devices(self):
        data = self.api.data

        provider = self._provider
        meters = data.get(API_DATA_SECTION_METERS, [])

        account_name = self._account_number

        account_device = self.device_manager.get(account_name)

        account_device_info = {
            "identifiers": {(DEFAULT_NAME, account_name)},
            "name": account_name,
            "manufacturer": DEFAULT_NAME,
            "model": "Account",
            ATTR_CONFIGURATION_URL: CITY_MIND_WEBSITE
        }

        if account_device is None or account_device != account_device_info:
            self.device_manager.set(account_name, account_device_info)

            _LOGGER.info(f"Created device {account_device}, Data: {account_device_info}")

        for meter in meters:
            meter_serial_number = meter.get(METER_SERIAL_NUMBER)

            meter_name = self._get_meter_name(meter_serial_number)

            meter_device = self.device_manager.get(account_name)

            meter_device_info = {
                "identifiers": {(DEFAULT_NAME, meter_name)},
                "name": meter_name,
                "manufacturer": provider,
                "model": "Water Meter"
            }

            if meter_device is None or meter_device != meter_device_info:
                self.device_manager.set(meter_name, meter_device_info)

                _LOGGER.info(f"Created device {meter_name}, Data: {meter_device_info}")

    def load_entities(self):
        data = self.api.data
        meters = data.get(API_DATA_SECTION_METERS, [])

        account_name = self._account_number

        for alert_type in ALERT_TYPES:
            self._load_alert_settings_select(account_name, alert_type)

        self._load_messages_sensor(account_name)
        self._load_alerts_sensor(account_name)
        self._load_vacations_sensor(account_name)

        for meter in meters:
            meter_serial_number = meter.get(METER_SERIAL_NUMBER)

            meter_name = self._get_meter_name(meter_serial_number)

            self._load_last_read_sensor(meter_name, meter)
            self._load_daily_consumption_sensor(meter_name, meter, "Today", self.api.today)
            self._load_daily_consumption_sensor(meter_name, meter, "Yesterday", self.api.yesterday)
            self._load_monthly_consumption_sensor(meter_name, meter)
            self._load_consumption_forcast_sensor(meter_name, meter)

    def _load_alert_settings_select(self, account_name: str, alert_type: int):
        try:
            is_leak_alert = alert_type == ALERT_TYPE_LEAK

            settings = self.api.data.get(API_DATA_SECTION_SETTINGS)
            value = int(MEDIA_TYPE_EMAIL) if is_leak_alert else 0

            for item in settings:
                alert_type_id = item.get(SETTINGS_ALERT_TYPE_ID)
                current_media_type_id = item.get(SETTINGS_MEDIA_TYPE_ID, 0)

                skip = is_leak_alert and current_media_type_id == int(MEDIA_TYPE_EMAIL)

                if alert_type_id == alert_type and not skip:
                    value += current_media_type_id

            options = []
            for media_id in MEDIA_TYPES:
                if media_id not in [MEDIA_TYPE_NONE, MEDIA_TYPE_SMS] or not is_leak_alert:
                    options.append(media_id)

            state = str(value)
            alert_type_name = ALERT_TYPES.get(alert_type)
            entity_name = f"{account_name} Alert {alert_type_name}"

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SELECT, entity_name)

            icon = MEDIA_TYPE_ICONS.get(state)

            entity_description = SelectDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                device_class=f"{DOMAIN}__{ATTR_MEDIA_TYPES}",
                attr_options=tuple(options),
                entity_category=EntityCategory.CONFIG
            )

            details = {
                ATTR_ALERT_TYPES: alert_type
            }

            self.set_action(unique_id, ACTION_CORE_ENTITY_SELECT_OPTION, self._set_alert_settings)

            self.entity_manager.set_entity(DOMAIN_SELECT,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           account_name,
                                           entity_description,
                                           details=details)

        except Exception as ex:
            self.log_exception(ex, f"Failed to load select for {account_name} Alert #{alert_type}")

    def _load_messages_sensor(
            self,
            account_name: str
    ):
        entity_name = f"{account_name} Messages"

        try:
            messages = self.api.data.get(API_DATA_SECTION_MY_MESSAGES)

            state = len(messages)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                "Messages": messages
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)
            icon = "mdi:water-check" if state == 0 else "mdi:water-alert"

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                state_class=SensorStateClass.MEASUREMENT
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           account_name,
                                           entity_description)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load sensor for {entity_name}"
            )

    def _load_alerts_sensor(
            self,
            account_name: str
    ):
        entity_name = f"{account_name} Alerts"

        try:
            alerts = self.api.data.get(API_DATA_SECTION_MY_ALERTS)

            state = len(alerts)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                "Alerts": alerts
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)
            icon = "mdi:water-check" if state == 0 else "mdi:water-alert"

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                state_class=SensorStateClass.MEASUREMENT
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           account_name,
                                           entity_description)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load sensor for {entity_name}"
            )

    def _load_vacations_sensor(
            self,
            account_name: str
    ):
        entity_name = f"{account_name} Vacations"

        try:
            vacations = self.api.data.get(API_DATA_SECTION_MY_MESSAGES)

            state = len(vacations)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                "Vacations": vacations
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)
            icon = "mdi:home-remove"

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                state_class=SensorStateClass.MEASUREMENT
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           account_name,
                                           entity_description)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load sensor for {entity_name}"
            )

    def _load_last_read_sensor(
            self,
            meter_name: str,
            meter_details: dict
    ):
        entity_name = f"{meter_name} Last Read"

        try:
            meter_count = meter_details.get(METER_COUNT)
            last_read_section = self.api.data.get(API_DATA_SECTION_LAST_READ)

            last_read_value = 0

            for last_read_item in last_read_section:
                current_meter_count = last_read_item.get(LAST_READ_METER_COUNT)

                if current_meter_count == meter_count:
                    last_read_value = last_read_item.get(LAST_READ_VALUE)

                    break

            state = self._format_number(last_read_value, 3)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)
            icon = "mdi:meter-gas"

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=VOLUME_CUBIC_METERS
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           meter_name,
                                           entity_description)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load sensor for {entity_name}"
            )

    def _load_daily_consumption_sensor(
            self,
            meter_name: str,
            meter_details: dict,
            day_title: str,
            date_iso: str

    ):
        entity_name = f"{meter_name} {day_title}'s Consumption"

        try:
            state = self._get_consumption_state(meter_details,
                                                API_DATA_SECTION_CONSUMPTION_DAILY,
                                                date_iso)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)
            icon = "mdi:meter-gas"

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                state_class=SensorStateClass.TOTAL,
                last_reset=self._today_date,
                native_unit_of_measurement=VOLUME_CUBIC_METERS
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           meter_name,
                                           entity_description)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load sensor for {entity_name}"
            )

    def _load_monthly_consumption_sensor(
            self,
            meter_name: str,
            meter_details: dict
    ):
        entity_name = f"{meter_name} Monthly Consumption"

        try:
            state = self._get_consumption_state(meter_details,
                                                API_DATA_SECTION_CONSUMPTION_MONTHLY,
                                                self.api.current_month)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)
            icon = "mdi:meter-gas"

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                state_class=SensorStateClass.TOTAL,
                last_reset=self._month_date,
                native_unit_of_measurement=VOLUME_CUBIC_METERS
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           meter_name,
                                           entity_description)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load sensor for {entity_name}"
            )

    def _load_consumption_forcast_sensor(
            self,
            meter_name: str,
            meter_details: dict
    ):
        entity_name = f"{meter_name} Consumption Forcast"

        try:
            meter_count = meter_details.get(METER_COUNT)
            consumption_forcast_section = self.api.data.get(API_DATA_SECTION_CONSUMPTION_FORCAST)
            consumption_forcast = consumption_forcast_section.get(str(meter_count))

            estimated_value = consumption_forcast.get(CONSUMPTION_FORCAST_ESTIMATED_CONSUMPTION, 0)
            state = self._format_number(estimated_value, 3)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)
            icon = "mdi:meter-gas"

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=icon,
                state_class=SensorStateClass.TOTAL,
                last_reset=self._month_date,
                native_unit_of_measurement=VOLUME_CUBIC_METERS
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           meter_name,
                                           entity_description)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load sensor for {entity_name}"
            )

    async def _reload_integration(self):
        data = {
            ENTITY_CONFIG_ENTRY_ID: self.entry_id
        }

        await self._hass.services.async_call(HA_NAME, SERVICE_RELOAD, data)

    async def _validate_weekday(self, should_reload_integration: bool):
        today = datetime.now()
        today_day_name = calendar.day_name[today.weekday()]

        is_weekend = today_day_name in WEEKEND_DAYS

        if self._is_weekend != is_weekend:
            self._is_weekend = is_weekend

            if should_reload_integration:
                await self._reload_integration()

            else:
                update_data_interval = UPDATE_DATA_INTERVALS[self._is_weekend]

                self.update_intervals(UPDATE_ENTITIES_INTERVAL, update_data_interval)

    async def _set_alert_settings(self, entity: EntityData, option: str) -> None:
        """ Handles ACTION_CORE_ENTITY_SELECT_OPTION. """
        alert_type_id = entity.details.get(ATTR_ALERT_TYPES)

        if alert_type_id is not None:
            settings = self.api.data.get(API_DATA_SECTION_SETTINGS)

            current_sms_state = False
            current_email_state = False

            for item in settings:
                current_alert_type_id = item.get(SETTINGS_ALERT_TYPE_ID)
                current_media_type_id = item.get(SETTINGS_MEDIA_TYPE_ID)

                if current_alert_type_id == alert_type_id:
                    if str(current_media_type_id) == MEDIA_TYPE_SMS:
                        current_sms_state = True
                    elif str(current_media_type_id) == MEDIA_TYPE_EMAIL:
                        current_email_state = True

            expected_sms_state = option in [MEDIA_TYPE_SMS, MEDIA_TYPE_ALL]
            expected_email_state = option in [MEDIA_TYPE_EMAIL, MEDIA_TYPE_ALL]

            if current_sms_state != expected_sms_state:
                await self.api.async_set_alert_settings(alert_type_id, MEDIA_TYPE_SMS, expected_sms_state)

            if current_email_state != expected_email_state:
                await self.api.async_set_alert_settings(alert_type_id, MEDIA_TYPE_EMAIL, expected_email_state)

            await self.async_update_data_providers()

            self._update_entities(None)

    def _get_consumption_state(self, meter_details: dict, section_key: str, date_iso: str) -> int | float | None:
        meter_count = meter_details.get(METER_COUNT)
        data = self.api.data.get(section_key)

        consumption_info = data.get(str(meter_count))
        state = None

        for consumption_item in consumption_info:
            if consumption_item is not None:
                consumption_meter_count = consumption_item.get(CONSUMPTION_METER_COUNT)
                consumption_date = consumption_item.get(CONSUMPTION_DATE)
                consumption_value = consumption_item.get(CONSUMPTION_VALUE, 0)

                is_meter_relevant = consumption_meter_count == meter_count
                is_date_relevant = consumption_date.startswith(date_iso)

                if is_meter_relevant and is_date_relevant:
                    if consumption_value is not None:
                        consumption = float(consumption_value)

                        state = self._format_number(consumption, 3)

                    break

        return state

    @staticmethod
    def _format_number(value: int | float | None, digits: int = 0) -> int | float:
        if value is None:
            value = 0

        value_str = f"{value:.{digits}f}"
        result = int(value_str) if digits == 0 else float(value_str)

        return result
