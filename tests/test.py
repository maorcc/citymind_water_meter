"""Test."""
from __future__ import annotations

import asyncio
from datetime import datetime
import json
import logging
import os
import sys

from custom_components.citymind_water_meter.common.connectivity_status import (
    ConnectivityStatus,
)
from custom_components.citymind_water_meter.common.consts import (
    SIGNAL_API_STATUS,
    SIGNAL_DATA_CHANGED,
)
from custom_components.citymind_water_meter.common.enums import EntityType
from custom_components.citymind_water_meter.data_processors.account_processor import (
    AccountProcessor,
)
from custom_components.citymind_water_meter.data_processors.base_processor import (
    BaseProcessor,
)
from custom_components.citymind_water_meter.data_processors.meter_processor import (
    MeterProcessor,
)
from custom_components.citymind_water_meter.managers.config_manager import ConfigManager
from custom_components.citymind_water_meter.managers.rest_api import RestAPI
from custom_components.citymind_water_meter.models.config_data import ConfigData
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

DATA_KEYS = [CONF_EMAIL, CONF_PASSWORD]

DEBUG = str(os.environ.get("DEBUG", False)).lower() == str(True).lower()

log_level = logging.DEBUG if DEBUG else logging.INFO

root = logging.getLogger()
root.setLevel(log_level)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
stream_handler.setFormatter(formatter)
root.addHandler(stream_handler)

_LOGGER = logging.getLogger(__name__)


class Test:
    """Test Class."""

    def __init__(self, event_loop):
        """Do initialization of test class instance, Returns None."""

        self._config_data: ConfigData | None = None
        self._api: RestAPI | None = None
        self._loop = event_loop

        self._config_manager = ConfigManager(None, None)
        self._account_processor: AccountProcessor | None = None
        self._meter_processor: MeterProcessor | None = None
        self._processors: dict[EntityType, BaseProcessor] | None = None

    async def initialize(self):
        """Do initialization of test dependencies instances, Returns None."""

        data = {}

        for key in DATA_KEYS:
            value = os.environ.get(key)

            if value is None:
                raise KeyError(f"Key '{key}' was not set")

            data[key] = value

        await self._config_manager.initialize(data)

        self._account_processor = AccountProcessor(self._config_manager)
        self._meter_processor = MeterProcessor(self._config_manager)

        self._processors = {
            EntityType.ACCOUNT: self._account_processor,
            EntityType.METER: self._meter_processor,
        }

        self._config_data = self._config_manager.config_data

        self._api = RestAPI(
            None,
            self._config_data,
            self._config_manager.analytic_periods
        )

        self._api.set_local_async_dispatcher_send(self.local_async_dispatcher_send)

        await self._api.initialize()

    async def terminate(self):
        """Do termination of API, Returns None."""
        await self._api.terminate()

    def local_async_dispatcher_send(self, signal, entry_id, *args):
        _LOGGER.info(f"{signal} {entry_id} {args}")

        if signal == SIGNAL_API_STATUS:
            status = args[0]

            if status == ConnectivityStatus.Connected:
                _LOGGER.debug("connected")

        elif signal == SIGNAL_DATA_CHANGED:
            _LOGGER.debug("data changed")

    async def update(self):
        for i in range(1, 10):
            if self._api.status != ConnectivityStatus.Connected:
                await asyncio.sleep(1000)

        print("update")

        await self._api.update()

        for processor_type in self._processors:
            processor = self._processors[processor_type]
            processor.update(self._api.data)

        account = self._account_processor.get()
        meters = self._meter_processor.get_meters()

        _LOGGER.info(json.dumps(self._api.data, indent=4, default=str))
        _LOGGER.info(f"account: {account}")

        for meter_id in meters:
            meter = self._meter_processor.get_data(meter_id)
            _LOGGER.info(f"{meter}")

    def _get_api_data(self) -> str:
        data = self._api.data
        clean_data = {}

        try:
            for key in data:
                value = data.get(key)

                if isinstance(value, datetime):
                    value = str(value)

                clean_data[key] = value

        except Exception as ex:
            _LOGGER.error(f"Failed to get API data, Data: {data} Error: {ex}")

        result = json.dumps(clean_data, indent=4)

        return result


loop = asyncio.new_event_loop()
instance = Test(loop)

try:
    loop.run_until_complete(instance.initialize())
    loop.run_until_complete(instance.update())

except KeyboardInterrupt:
    _LOGGER.info("Aborted")

except Exception as rex:
    _LOGGER.error(f"Error: {rex}")

finally:
    loop.run_until_complete(instance.terminate())
