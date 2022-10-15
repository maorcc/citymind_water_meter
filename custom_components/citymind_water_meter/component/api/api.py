from __future__ import annotations

from datetime import datetime
import logging
import sys
from typing import Awaitable, Callable

import aiohttp
from aiohttp import ClientResponseError, ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ...configuration.models.config_data import ConfigData
from ...core.api.base_api import BaseAPI
from ...core.helpers.enums import ConnectivityStatus
from ..helpers.const import *

_LOGGER = logging.getLogger(__name__)


class IntegrationAPI(BaseAPI):
    """The Class for handling the data retrieval."""

    session: ClientSession | None
    hass: HomeAssistant
    config_data: ConfigData | None
    base_url: str | None

    today: str | None
    yesterday: str | None
    _last_day_of_current_month: str | None
    _current_month: str | None

    def __init__(self,
                 hass: HomeAssistant,
                 async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
                 async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]] | None = None
                 ):

        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        try:
            self.config_data = None
            self.session = None
            self.base_url = None

            self.data = {}

            self.today = None
            self.yesterday = None
            self._last_day_of_current_month = None
            self._current_month = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize CityMind API, error: {ex}, line: {line_number}"
            )

    @property
    def token(self):
        return self.data.get(API_DATA_TOKEN)

    @property
    def municipal_id(self) -> str | None:
        customer_service = self.data.get(API_DATA_SECTION_ME, {})
        municipal_id = customer_service.get(ME_MUNICIPAL_ID)

        return municipal_id

    async def terminate(self):
        await self.set_status(ConnectivityStatus.Disconnected)

    async def initialize(self, config_data: ConfigData):
        _LOGGER.info("Initializing CityMind API")

        try:
            await self.set_status(ConnectivityStatus.Connecting)

            self.config_data = config_data

            if self.hass is None:
                if self.session is not None:
                    await self.session.close()

                self.session = aiohttp.client.ClientSession()
            else:
                self.session = async_create_clientsession(hass=self.hass)

            await self._login()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize City Mind API ({self.base_url}), error: {ex}, line: {line_number}"
            )

            await self.set_status(ConnectivityStatus.Failed)

    async def validate(self, data: dict | None = None):
        config_data = ConfigData.from_dict(data)

        await self.initialize(config_data)

    def _set_date(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        year = today.year if today.month <= 11 else today.year + 1
        month = today.month + 1 if today.month <= 11 else 1

        next_month_date = datetime(year=year, month=month, day=1)
        last_day_of_current_month = next_month_date - timedelta(days=1)

        self.today = today.strftime(FORMAT_DATE_ISO)
        self.yesterday = yesterday.strftime(FORMAT_DATE_ISO)
        self._current_month = today.strftime(FORMAT_DATE_YEAR_MONTH)
        self._last_day_of_current_month = last_day_of_current_month.strftime(FORMAT_DATE_ISO)

    def _build_endpoint(self, endpoint, meter_count: str = None):
        if PH_MUNICIPALITY in endpoint and self.municipal_id is not None:
            endpoint = endpoint.replace(PH_MUNICIPALITY, str(self.municipal_id))

        if PH_TODAY in endpoint:
            endpoint = endpoint.replace(PH_TODAY, self.today)

        if PH_YESTERDAY in endpoint:
            endpoint = endpoint.replace(PH_YESTERDAY, self.yesterday)

        if PH_CURRENT_MONTH in endpoint:
            endpoint = endpoint.replace(PH_CURRENT_MONTH, self._current_month)

        if PH_LAST_DAY_MONTH in endpoint:
            endpoint = endpoint.replace(PH_LAST_DAY_MONTH, self._last_day_of_current_month)

        if PH_METER in endpoint and meter_count is not None:
            endpoint = endpoint.replace(PH_METER, meter_count)

        return endpoint

    async def _async_post(self,
                          endpoint,
                          request_data: dict):
        result = None

        try:
            url = self._build_endpoint(endpoint)

            _LOGGER.debug(f"POST {url}")

            async with self.session.post(url, json=request_data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to post JSON to {endpoint}, HTTP Status: {crex.message} ({crex.status})"
            )

            if crex.status in [404, 405]:
                self.status = ConnectivityStatus.NotFound

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to post JSON to {endpoint}, Error: {ex}, Line: {line_number}"
            )

            self.status = ConnectivityStatus.Failed

        return result

    async def _async_get(self, endpoint: str, meter_count: str | None = None):
        result = None

        try:
            url = self._build_endpoint(endpoint, meter_count)

            headers = {
                API_HEADER_TOKEN: self.token
            }

            _LOGGER.debug(f"GET {url}")

            async with self.session.get(url, headers=headers, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {endpoint}, HTTP Status: {crex.message} ({crex.status})"
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {endpoint}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def _async_put(self, url: str, data: dict | list):
        result = None

        try:
            headers = {
                API_HEADER_TOKEN: self.token
            }

            async with self.session.put(url, headers=headers, json=data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {url}, HTTP Status: {crex.message} ({crex.status})"
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {url}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def _async_delete(self, url: str, data: dict | list):
        result = None

        try:
            headers = {
                API_HEADER_TOKEN: self.token
            }

            async with self.session.delete(url, headers=headers, json=data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {url}, HTTP Status: {crex.message} ({crex.status})"
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {url}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def async_update(self):
        _LOGGER.debug(f"Updating data for user {self.config_data.email}")

        if self.status == ConnectivityStatus.Failed:
            await self.initialize(self.config_data)

        if self.status == ConnectivityStatus.Connected:
            self._set_date()

            if API_DATA_SECTION_ME not in self.data:
                await self._load_data(ENDPOINT_DATA_INITIALIZE)

            await self._load_data(ENDPOINT_DATA_UPDATE)

            meters = self.data.get(API_DATA_SECTION_METERS, [])

            for meter in meters:
                meter_count = str(meter.get(METER_COUNT))

                await self._load_data(ENDPOINT_DATA_UPDATE_PER_METER, meter_count)

            await self.fire_data_changed_event()

    async def _login(self):
        _LOGGER.info("Performing login")
        exception_data = None

        await self.set_status(ConnectivityStatus.Connecting)

        status = ConnectivityStatus.Failed

        try:
            self.data[API_DATA_TOKEN] = None

            config_data = self.config_data

            data = {
                LOGIN_EMAIL: config_data.email,
                LOGIN_PASSWORD: config_data.password,
                LOGIN_DEVICE_ID: DEVICE_ID
            }

            payload = await self._async_post(ENDPOINT_LOGIN, data)

            if payload is not None:
                token = payload.get(API_DATA_TOKEN)
                self.data[API_DATA_TOKEN] = token

                if token is None:
                    status = ConnectivityStatus.MissingAPIKey

                else:
                    status = ConnectivityStatus.Connected

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            exception_data = f"Error: {ex}, Line: {line_number}"

        await self.set_status(status)

        log_level = ConnectivityStatus.get_log_level(status)

        message = status if exception_data is None else f"{status}, {exception_data}"

        _LOGGER.log(log_level, message)

    async def _load_data(self, endpoints: dict, meter_count: str | None = None):
        for endpoint_key in endpoints:
            endpoint = endpoints.get(endpoint_key)

            data = await self._async_get(endpoint, meter_count)

            if meter_count is None:
                self.data[endpoint_key] = data

            else:
                metered_data = self.data.get(endpoint_key, {})
                metered_data[meter_count] = data

                self.data[endpoint_key] = metered_data

    async def async_set_alert_settings(self, alert_type_id: int, media_type_id: str, enabled: bool):
        _LOGGER.info(f"Updating alert {alert_type_id} on media {media_type_id} to {enabled}")

        action: Callable[[str, dict | list], Awaitable[dict]] = self._async_put if enabled else self._async_delete
        endpoint = self._build_endpoint(ENDPOINT_MY_ALERTS_SETTINGS_UPDATE)
        url = f"{endpoint}/{alert_type_id}"

        data = [int(media_type_id)]

        await action(url, data)

        await self._load_data(ENDPOINT_DATA_RELOAD)
