from copy import copy
import json
import logging
import sys
from typing import Any

from cryptography.fernet import InvalidToken

from homeassistant.config_entries import STORAGE_VERSION, ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ..common.consts import (
    CONFIGURATION_FILE,
    DEFAULT_METER_CONFIG,
    DEFAULT_NAME,
    DEFAULT_USE_UNIQUE_DEVICE_NAMES,
    DOMAIN,
    INVALID_TOKEN_SECTION,
    SIGNAL_DATA_CHANGED,
    STORAGE_DATA_METER_HIGH_RATE_COST,
    STORAGE_DATA_METER_LOW_RATE_CONSUMPTION_THRESHOLD,
    STORAGE_DATA_METER_LOW_RATE_COST,
    STORAGE_DATA_METER_SEWAGE_COST,
    STORAGE_DATA_METERS,
    STORAGE_DATA_USE_UNIQUE_DEVICE_NAMES,
)
from ..common.entity_descriptions import IntegrationEntityDescription
from ..models.analytics_periods import AnalyticPeriodsData
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class ConfigManager:
    _data: dict | None
    _config_data: ConfigData

    _store: Store | None
    _translations: dict | None
    _password: str | None
    _entry_title: str
    _entry_id: str

    _is_set_up_mode: bool
    _is_initialized: bool

    analytic_periods: AnalyticPeriodsData

    def __init__(self, hass: HomeAssistant | None, entry: ConfigEntry | None = None):
        self._hass = hass
        self._entry = entry
        self._entry_id = None if entry is None else entry.entry_id
        self._entry_title = DEFAULT_NAME if entry is None else entry.title

        self._local_async_dispatcher_send = None

        self._config_data = ConfigData()

        self._data = None

        self._store = None
        self._translations = None

        self._is_set_up_mode = entry is None
        self._is_initialized = False

        self.analytic_periods = AnalyticPeriodsData()

        if hass is not None:
            self._store = Store(
                hass, STORAGE_VERSION, CONFIGURATION_FILE, encoder=JSONEncoder
            )

    @property
    def is_initialized(self) -> bool:
        is_initialized = self._is_initialized

        return is_initialized

    @property
    def entry_id(self) -> str:
        entry_id = self._entry_id

        return entry_id

    @property
    def entry_title(self) -> str:
        entry_title = self._entry_title

        return entry_title

    @property
    def entry(self) -> ConfigEntry:
        entry = self._entry

        return entry

    @property
    def meters(self):
        result = self._data.get(STORAGE_DATA_METERS, {})

        return result

    @property
    def use_unique_device_names(self) -> bool:
        result = self._data.get(
            STORAGE_DATA_USE_UNIQUE_DEVICE_NAMES, DEFAULT_USE_UNIQUE_DEVICE_NAMES
        )

        return result

    @property
    def config_data(self) -> ConfigData:
        config_data = self._config_data

        return config_data

    async def initialize(self, entry_config: dict):
        try:
            await self._load()

            self._config_data.update(entry_config)

            if self._hass is None:
                self._translations = {}

            else:
                self._translations = await translation.async_get_translations(
                    self._hass, self._hass.config.language, "entity", {DOMAIN}
                )

            self._is_initialized = True

        except InvalidToken:
            self._is_initialized = False

            _LOGGER.error(
                f"Invalid encryption key, Please follow instructions in {INVALID_TOKEN_SECTION}"
            )

        except Exception as ex:
            self._is_initialized = False

            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize configuration manager, Error: {ex}, Line: {line_number}"
            )

    def get_translation(
        self,
        platform: Platform,
        entity_key: str,
        attribute: str,
        default_value: str | None = None,
    ) -> str | None:
        translation_key = (
            f"component.{DOMAIN}.entity.{platform}.{entity_key}.{attribute}"
        )

        translated_value = self._translations.get(translation_key, default_value)

        return translated_value

    def get_entity_name(
        self,
        entity_description: IntegrationEntityDescription,
        device_info: DeviceInfo,
    ) -> str:
        entity_key = entity_description.key

        device_name = device_info.get("name")
        platform = entity_description.platform

        translated_name = self.get_translation(
            platform, entity_key, CONF_NAME, entity_description.key
        )

        entity_name = (
            device_name
            if translated_name is None or translated_name == ""
            else f"{device_name} {translated_name}"
        )

        return entity_name

    def get_debug_data(self) -> dict:
        data = self._config_data.to_dict()

        for key in self._data:
            data[key] = self._data[key]

        return data

    def _get_meter_config(self, meter_id: str, key: str) -> int:
        meter_config = self.meters.get(meter_id, {})
        value = meter_config.get(key, 0)

        return value

    def get_low_rate_consumption_threshold(self, meter_id: str) -> int:
        result = self._get_meter_config(
            meter_id, STORAGE_DATA_METER_LOW_RATE_CONSUMPTION_THRESHOLD
        )

        return result

    def get_low_rate_cost(self, meter_id: str) -> int:
        result = self._get_meter_config(meter_id, STORAGE_DATA_METER_LOW_RATE_COST)

        return result

    def get_high_rate_cost(self, meter_id: str) -> int:
        result = self._get_meter_config(meter_id, STORAGE_DATA_METER_HIGH_RATE_COST)

        return result

    def get_sewage_cost(self, meter_id: str) -> int:
        result = self._get_meter_config(meter_id, STORAGE_DATA_METER_SEWAGE_COST)

        return result

    async def _load(self):
        self._data = None

        await self._load_config_from_file()

        _LOGGER.info(f"loaded: {self._data}")
        should_save = False

        if self._data is None:
            should_save = True
            self._data = {}

        default_configuration = self._get_defaults()
        _LOGGER.debug(f"Default configuration: {default_configuration}")

        for key in default_configuration:
            value = default_configuration[key]

            if key not in self._data:
                _LOGGER.debug(f"Adding {key}")
                should_save = True
                self._data[key] = value

        if should_save:
            _LOGGER.debug("Updating configuration")
            await self._save()

    @staticmethod
    def _get_defaults() -> dict:
        data = {
            STORAGE_DATA_USE_UNIQUE_DEVICE_NAMES: DEFAULT_USE_UNIQUE_DEVICE_NAMES,
            STORAGE_DATA_METERS: {},
        }

        return data

    async def _load_config_from_file(self):
        if self._store is not None:
            store_data = await self._store.async_load()

            if store_data is not None:
                self._data = store_data.get(self._entry_id)

    async def remove(self, entry_id: str):
        if self._store is None:
            return

        store_data = await self._store.async_load()

        if store_data is not None and entry_id in store_data:
            data = {key: store_data[key] for key in store_data}
            data.pop(entry_id)

            await self._store.async_save(data)

    async def _save(self):
        if self._store is None:
            return

        should_save = False
        store_data = await self._store.async_load()

        if store_data is None:
            store_data = {}

        entry_data = store_data.get(self._entry_id, {})

        _LOGGER.debug(
            f"Storing config data: {json.dumps(self._data)}, "
            f"Exiting: {json.dumps(entry_data)}"
        )

        for key in self._data:
            stored_value = entry_data.get(key)

            if key in [CONF_PASSWORD, CONF_USERNAME]:
                entry_data.pop(key)

                if stored_value is not None:
                    should_save = True

            else:
                current_value = self._data.get(key)

                if stored_value != current_value:
                    should_save = True

                    entry_data[key] = self._data[key]

        if should_save and self._entry_id is not None:
            store_data[self._entry_id] = entry_data

            await self._store.async_save(store_data)

    async def set_use_unique_device_names(self, value: bool) -> None:
        self._data[STORAGE_DATA_USE_UNIQUE_DEVICE_NAMES] = value

        await self._save()

        self._async_dispatcher_send(SIGNAL_DATA_CHANGED)

    async def _set_meter_config(self, meter_id: str, key: str, value: float) -> None:
        if meter_id not in self.meters:
            self._data[STORAGE_DATA_METERS][meter_id] = copy(DEFAULT_METER_CONFIG)

        self._data[STORAGE_DATA_METERS][meter_id][key] = value

        await self._save()

        self._async_dispatcher_send(SIGNAL_DATA_CHANGED)

    async def set_low_rate_consumption_threshold(
        self, meter_id: str, value: float
    ) -> None:
        await self._set_meter_config(
            meter_id, STORAGE_DATA_METER_LOW_RATE_CONSUMPTION_THRESHOLD, value
        )

    async def set_low_rate_cost(self, meter_id: str, value: float) -> None:
        await self._set_meter_config(meter_id, STORAGE_DATA_METER_LOW_RATE_COST, value)

    async def set_high_rate_cost(self, meter_id: str, value: float) -> None:
        await self._set_meter_config(meter_id, STORAGE_DATA_METER_HIGH_RATE_COST, value)

    async def set_sewage_cost(self, meter_id: str, value: float) -> None:
        await self._set_meter_config(meter_id, STORAGE_DATA_METER_SEWAGE_COST, value)

    def set_local_async_dispatcher_send(self, callback):
        self._local_async_dispatcher_send = callback

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        if self._hass is None:
            self._local_async_dispatcher_send(signal, None, *args)

        else:
            dispatcher_send(self._hass, signal, self._entry_id, *args)
