"""Test."""
from __future__ import annotations

import asyncio
from datetime import datetime
import json
import logging
import os
import sys

from custom_components.citymind_water_meter.component.api.api import IntegrationAPI
from custom_components.citymind_water_meter.configuration.models.config_data import (
    ConfigData,
)
from custom_components.citymind_water_meter.core.helpers.enums import ConnectivityStatus
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

    def __init__(self):
        """Do initialization of test class instance, Returns None."""

        self._api = IntegrationAPI(
            None, self._api_data_changed, self._api_status_changed
        )

        self._config_data: ConfigData | None = None

    async def initialize(self):
        """Do initialization of test dependencies instances, Returns None."""

        data = {}

        for key in DATA_KEYS:
            value = os.environ.get(key)

            if value is None:
                raise KeyError(f"Key '{key}' was not set")

            data[key] = value

        self._config_data = ConfigData.from_dict(data)

        await self._api.initialize(self._config_data)

    async def terminate(self):
        """Do termination of API, Returns None."""

        await self._api.terminate()

    async def _api_data_changed(self):
        data = self._get_api_data()

        _LOGGER.info(f"API Data: {data}")

    async def _api_status_changed(self, status: ConnectivityStatus):
        _LOGGER.info(f"API Status changed to {status.name}")

        if self._api.status == ConnectivityStatus.Connected:
            await self._api.async_update()
            await self._api.terminate()

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


instance = Test()
loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(instance.initialize())

except KeyboardInterrupt:
    _LOGGER.info("Aborted")

except Exception as rex:
    _LOGGER.error(f"Error: {rex}")

finally:
    loop.run_until_complete(instance.terminate())
