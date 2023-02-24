"""Storage handlers."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ...configuration.models.config_data import ConfigData
from ...core.api.base_api import BaseAPI
from ...core.helpers.const import DOMAIN, STORAGE_VERSION
from ...core.helpers.enums import ConnectivityStatus
from ..helpers.const import (
    STORAGE_DATA_FILE_CONFIG,
    STORAGE_DATA_FILES,
    STORAGE_DATA_METERS,
)

_LOGGER = logging.getLogger(__name__)


class StorageAPI(BaseAPI):
    _stores: dict[str, Store] | None
    _config_data: ConfigData | None
    _data: dict

    def __init__(
        self,
        hass: HomeAssistant,
        async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
        async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]]
        | None = None,
    ):
        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        self._config_data = None
        self._stores = None
        self._data = {}

    @property
    def _storage_config(self) -> Store:
        storage = self._stores.get(STORAGE_DATA_FILE_CONFIG)

        return storage

    def get_meter_config(self, meter_serial_number: str) -> dict | None:
        meters = self.data.get(STORAGE_DATA_METERS, {})
        meter = meters.get(meter_serial_number)

        return meter

    async def initialize(self, config_data: ConfigData):
        self._config_data = config_data

        self._initialize_storages()

        await self._async_load_configuration()

    def _initialize_storages(self):
        stores = {}

        entry_id = self._config_data.entry.entry_id

        for storage_data_file in STORAGE_DATA_FILES:
            file_name = f"{DOMAIN}.{entry_id}.{storage_data_file}.json"

            stores[storage_data_file] = Store(
                self.hass, STORAGE_VERSION, file_name, encoder=JSONEncoder
            )

        self._stores = stores

    async def _async_load_configuration(self):
        """Load the retained data from store and return de-serialized data."""
        self.data = await self._storage_config.async_load()

        if self.data is None:
            self.data = {}

            await self._async_save()

        _LOGGER.debug(f"Loaded configuration data: {self.data}")

        await self.set_status(ConnectivityStatus.Connected)
        await self.fire_data_changed_event()

    async def _async_save(self):
        """Generate dynamic data to store and save it to the filesystem."""
        _LOGGER.info(f"Save configuration, Data: {self.data}")

        await self._storage_config.async_save(self.data)

        await self.fire_data_changed_event()

    async def set_cost_parameters(self, meter_serial_number: str, data: dict):
        result = False
        meters = self.data.get(STORAGE_DATA_METERS, {})
        current_meter_data = meters.get(meter_serial_number, {})
        current_meter_data_hash = str(current_meter_data)

        meter_data = {}
        for data_key in data:
            if data_key != CONF_DEVICE_ID:
                meter_data[data_key] = data[data_key]

        latest_meter_data_hash = str(meter_data)

        if latest_meter_data_hash != current_meter_data_hash:
            meters[meter_serial_number] = meter_data

            self.data[STORAGE_DATA_METERS] = meters

            result = True

            await self._async_save()

        return result

    async def remove_cost_parameters(self, meter_serial_number: str, data: dict):
        result = False
        meters = self.data.get(STORAGE_DATA_METERS, {})

        if meter_serial_number in meters:
            del meters[meter_serial_number]

            self.data[STORAGE_DATA_METERS] = meters

            result = True

            await self._async_save()

        return result
