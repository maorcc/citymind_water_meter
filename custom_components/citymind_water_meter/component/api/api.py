from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
import logging
import sys

from aiohttp import ClientResponseError

from homeassistant.core import HomeAssistant

from ...configuration.models.config_data import ConfigData
from ...core.api.base_api import BaseAPI
from ...core.helpers.enums import ConnectivityStatus
from ..helpers.const import *

_LOGGER = logging.getLogger(__name__)


class IntegrationAPI(BaseAPI):
    """The Class for handling the data retrieval."""

    config_data: ConfigData | None

    today: str | None
    yesterday: str | None
    _last_day_of_current_month: str | None
    current_month: str | None

    _alert_settings_actions: dict[bool, Callable[[str, list[int]], Awaitable[dict]]]

    def __init__(self,
                 hass: HomeAssistant | None,
                 async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
                 async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]] | None = None
                 ):

        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        try:
            self.config_data = None

            self.data = {}

            self.today = None
            self.yesterday = None
            self._last_day_of_current_month = None
            self.current_month = None

            self._alert_settings_actions = {
                True: self._async_put,
                False: self._async_delete,
            }

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

    async def initialize(self, config_data: ConfigData):
        _LOGGER.info("Initializing CityMind API")

        try:
            await self.set_status(ConnectivityStatus.Connecting)

            self.config_data = config_data

            await self.initialize_session()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize City Mind API, error: {ex}, line: {line_number}"
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
        self.current_month = today.strftime(FORMAT_DATE_YEAR_MONTH)
        self._last_day_of_current_month = last_day_of_current_month.strftime(FORMAT_DATE_ISO)

    def _build_endpoint(self,
                        endpoint,
                        meter_count: str | None = None,
                        alert_type: int | None = None
                        ):

        data = {
            ENDPOINT_PARAMETER_METER_ID: meter_count,
            ENDPOINT_PARAMETER_YESTERDAY: self.yesterday,
            ENDPOINT_PARAMETER_TODAY: self.today,
            ENDPOINT_PARAMETER_LAST_DAY_MONTH: self._last_day_of_current_month,
            ENDPOINT_PARAMETER_MUNICIPALITY_ID: self.municipal_id,
            ENDPOINT_PARAMETER_CURRENT_MONTH: self.current_month,
            ENDPOINT_PARAMETER_ALERT_TYPE: alert_type
        }

        url = endpoint.format(**data)

        return url

    async def _async_post(self,
                          endpoint,
                          request_data: dict):
        result = None

        try:
            url = self._build_endpoint(endpoint)

            _LOGGER.debug(f"POST {url}")

            async with self.session.post(url, json=request_data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                result = await response.json()

                response.raise_for_status()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to post JSON to {endpoint}, HTTP Status: {crex.message} ({crex.status}), Data: {result}"
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to post JSON to {endpoint}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def _async_get(self, endpoint: str, meter_count: str | None = None):
        result = None

        try:
            url = self._build_endpoint(endpoint, meter_count=meter_count)

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

            if response.status == 401:
                await self.set_status(ConnectivityStatus.NotConnected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {endpoint}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def _async_put(self, endpoint: str, data: list[int]):
        result = None

        try:
            headers = {
                API_HEADER_TOKEN: self.token
            }

            url = self._build_endpoint(endpoint, alert_type=data[0])

            async with self.session.put(url, headers=headers, json=data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {endpoint}, Data: {data}, HTTP Status: {crex.message} ({crex.status})"
            )

            if response.status == 401:
                await self.set_status(ConnectivityStatus.NotConnected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {endpoint}, Data: {data}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def _async_delete(self, url: str, data: list[int]):
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

            if response.status == 401:
                await self.set_status(ConnectivityStatus.NotConnected)

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

            if self.municipal_id is None:
                await self._load_data(ENDPOINT_DATA_INITIALIZE)

            await self._load_data(ENDPOINT_DATA_UPDATE)

            meters = self.data.get(API_DATA_SECTION_METERS, [])

            for meter in meters:
                meter_count = str(meter.get(METER_COUNT))

                await self._load_data(ENDPOINT_DATA_UPDATE_PER_METER, meter_count)

            await self.fire_data_changed_event()

    async def login(self):
        await super().login()

        exception_data = None

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
                error_code = payload.get(API_DATA_ERROR_CODE)
                error_reason = payload.get(API_DATA_ERROR_REASON)

                if error_code == ERROR_REASON_INVALID_CREDENTIALS:
                    status = ConnectivityStatus.InvalidCredentials

                    exception_data = f"Error #{error_code}: {error_reason}"

                if token is not None:
                    self.data[API_DATA_TOKEN] = token

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
        if self.status == ConnectivityStatus.Connected:
            for endpoint_key in endpoints:
                if self.status == ConnectivityStatus.Connected:
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

        action = self._alert_settings_actions[enabled]
        data = [int(media_type_id)]

        await action(ENDPOINT_MY_ALERTS_SETTINGS_UPDATE, data)

        await self._load_data(ENDPOINT_DATA_RELOAD)
