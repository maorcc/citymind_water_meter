from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from datetime import datetime
import logging
import sys
from typing import Any, Callable

from aiohttp import ClientResponseError, ClientSession
from aiohttp.hdrs import METH_DELETE, METH_GET, METH_POST, METH_PUT

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send

from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import (
    API_DATA_ERROR_CODE,
    API_DATA_ERROR_REASON,
    API_DATA_LAST_UPDATE,
    API_DATA_SECTION_ME,
    API_DATA_SECTION_METERS,
    API_DATA_TOKEN,
    API_HEADER_TOKEN,
    DEFAULT_NAME,
    DEVICE_ID,
    ENDPOINT_DATA_INITIALIZE,
    ENDPOINT_DATA_RELOAD,
    ENDPOINT_DATA_UPDATE,
    ENDPOINT_DATA_UPDATE_PER_METER,
    ENDPOINT_LOGIN,
    ENDPOINT_MY_ALERTS_SETTINGS_UPDATE,
    ENDPOINT_PARAMETER_ALERT_TYPE,
    ENDPOINT_PARAMETER_CURRENT_MONTH,
    ENDPOINT_PARAMETER_LAST_DAY_MONTH,
    ENDPOINT_PARAMETER_METER_ID,
    ENDPOINT_PARAMETER_MUNICIPALITY_ID,
    ENDPOINT_PARAMETER_TODAY,
    ENDPOINT_PARAMETER_YESTERDAY,
    ERROR_REASON_INVALID_CREDENTIALS,
    LOGIN_DEVICE_ID,
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    ME_MUNICIPAL_ID,
    METER_COUNT,
    SIGNAL_API_STATUS,
    SIGNAL_DATA_CHANGED,
)
from ..common.enums import AlertChannel, AlertType
from ..models.analytics_periods import AnalyticPeriodsData
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class RestAPI:
    _hass: HomeAssistant | None
    _config_data: ConfigData
    _analytic_periods: AnalyticPeriodsData

    data: dict

    _status: ConnectivityStatus | None
    _session: ClientSession | None
    _entry_id: str | None
    _dispatched_meters: list
    _dispatched_account: bool

    _last_valid: datetime | None

    _alert_settings_actions: dict[bool, Callable[[str, list[int]], Awaitable[dict]]]

    def __init__(
        self,
        hass: HomeAssistant | None,
        config_data: ConfigData,
        analytic_periods: AnalyticPeriodsData | None = None,
        entry_id: str | None = None,
    ):
        try:
            if analytic_periods is None:
                analytic_periods = AnalyticPeriodsData()

            self._hass = hass
            self._support_video_browser_api = False

            self.data = {}

            self._config_data = config_data
            self._analytic_periods = analytic_periods

            self._local_async_dispatcher_send = None

            self._status = None

            self._session = None
            self._entry_id = entry_id
            self._dispatched_devices = []
            self._dispatched_server = False
            self._last_valid = None

            self._alert_settings_actions = {
                True: self._async_put,
                False: self._async_delete,
            }

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load {DEFAULT_NAME} API, error: {ex}, line: {line_number}"
            )

    @property
    def is_connected(self):
        result = self._session is not None

        return result

    @property
    def status(self) -> str | None:
        status = self._status

        return status

    @property
    def _is_home_assistant(self):
        return self._hass is not None

    @property
    def token(self):
        return self.data.get(API_DATA_TOKEN)

    @property
    def municipal_id(self) -> str | None:
        customer_service = self.data.get(API_DATA_SECTION_ME, {})

        municipal_id = customer_service.get(ME_MUNICIPAL_ID)

        return municipal_id

    async def _do_nothing(self, _status: ConnectivityStatus):
        pass

    async def initialize(self):
        self._set_status(ConnectivityStatus.Connecting, "Initializing API")

        await self._initialize_session()

        await self.login()

    async def terminate(self):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def validate(self):
        await self.initialize()

    async def update(self):
        _LOGGER.debug(
            f"Updating data for user {self._config_data.email}, "
            f"Connection: {self.status}"
        )

        if self.status == ConnectivityStatus.Connected:
            if self.municipal_id is None:
                await self._load_data(ENDPOINT_DATA_INITIALIZE)

            await self._load_data(ENDPOINT_DATA_UPDATE)

            meters = self.data.get(API_DATA_SECTION_METERS, [])

            for meter in meters:
                meter_id = str(meter.get(METER_COUNT))

                await self._load_data(ENDPOINT_DATA_UPDATE_PER_METER, meter_id)

            self._async_dispatcher_send(SIGNAL_DATA_CHANGED)

    async def login(self):
        try:
            self.data[API_DATA_TOKEN] = None

            config_data = self._config_data

            data = {
                LOGIN_EMAIL: config_data.email,
                LOGIN_PASSWORD: config_data.password,
                LOGIN_DEVICE_ID: DEVICE_ID,
            }

            payload = await self._async_post(ENDPOINT_LOGIN, data)

            if payload is not None:
                token = payload.get(API_DATA_TOKEN)
                error_code = payload.get(API_DATA_ERROR_CODE)
                error_reason = payload.get(API_DATA_ERROR_REASON)

                if error_code == ERROR_REASON_INVALID_CREDENTIALS:
                    message = f"Failed to login, Error #{error_code}: {error_reason}"

                    self._set_status(ConnectivityStatus.InvalidCredentials, message)

                if token is not None:
                    self.data[API_DATA_TOKEN] = token

                    self._set_status(ConnectivityStatus.Connected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            message = f"Failed to login, Error: {ex}, Line: {line_number}"

            self._set_status(ConnectivityStatus.Failed, message)

    async def _initialize_session(self):
        try:
            if self._is_home_assistant:
                self._session = async_create_clientsession(hass=self._hass)

            else:
                self._session = ClientSession()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            message = (
                f"Failed to initialize session, Error: {str(ex)}, Line: {line_number}"
            )

            self._set_status(ConnectivityStatus.Failed, message)

    def _set_status(self, status: ConnectivityStatus, message: str | None = None):
        log_level = ConnectivityStatus.get_log_level(status)

        if status != self._status:
            log_message = f"Status update {self._status} --> {status}"

            if message is not None:
                log_message = f"{log_message}, {message}"

            _LOGGER.log(log_level, log_message)

            self._status = status

            self._async_dispatcher_send(SIGNAL_API_STATUS, status)

        else:
            log_message = f"Status is {status}"

            if message is None:
                log_message = f"{log_message}, {message}"

            _LOGGER.log(log_level, log_message)

    def set_local_async_dispatcher_send(self, callback):
        self._local_async_dispatcher_send = callback

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        if self._hass is None:
            self._local_async_dispatcher_send(signal, None, *args)

        else:
            dispatcher_send(self._hass, signal, self._entry_id, *args)

    def _build_endpoint(
        self, endpoint, meter_count: str | None = None, alert_type: str | None = None
    ):
        data = {
            ENDPOINT_PARAMETER_METER_ID: meter_count,
            ENDPOINT_PARAMETER_ALERT_TYPE: alert_type,
            ENDPOINT_PARAMETER_MUNICIPALITY_ID: self.municipal_id,
            ENDPOINT_PARAMETER_YESTERDAY: self._analytic_periods.yesterday_iso,
            ENDPOINT_PARAMETER_TODAY: self._analytic_periods.today_iso,
            ENDPOINT_PARAMETER_LAST_DAY_MONTH: self._analytic_periods.last_date_of_month_iso,
            ENDPOINT_PARAMETER_CURRENT_MONTH: self._analytic_periods.current_month_iso,
        }

        url = endpoint.format(**data)

        return url

    async def _async_post(self, endpoint, request_data: dict):
        result = None

        try:
            url = self._build_endpoint(endpoint)

            async with self._session.post(
                url, json=request_data, ssl=False
            ) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                result = await response.json()

                response.raise_for_status()

        except ClientResponseError as crex:
            self._handle_client_error(endpoint, METH_POST, crex)

        except TimeoutError:
            self._handle_server_timeout(endpoint, METH_POST)

        except Exception as ex:
            self._handle_general_request_failure(endpoint, METH_POST, ex)

        return result

    async def _async_get(self, endpoint: str, meter_count: str | None = None):
        result = None

        try:
            url = self._build_endpoint(endpoint, meter_count=meter_count)

            headers = {API_HEADER_TOKEN: self.token}

            async with self._session.get(url, headers=headers, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            self._handle_client_error(endpoint, METH_GET, crex)

        except TimeoutError:
            self._handle_server_timeout(endpoint, METH_GET)

        except Exception as ex:
            self._handle_general_request_failure(endpoint, METH_GET, ex)

        return result

    async def _async_put(self, url: str, data: list[int]):
        result = None

        try:
            headers = {API_HEADER_TOKEN: self.token}

            async with self._session.put(
                url, headers=headers, json=data, ssl=False
            ) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            self._handle_client_error(url, METH_PUT, crex)

        except TimeoutError:
            self._handle_server_timeout(url, METH_PUT)

        except Exception as ex:
            self._handle_general_request_failure(url, METH_PUT, ex)

        return result

    async def _async_delete(self, url: str, data: list[int]):
        result = None

        try:
            headers = {API_HEADER_TOKEN: self.token}

            async with self._session.delete(
                url, headers=headers, json=data, ssl=False
            ) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}, Data: {data}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            self._handle_client_error(url, METH_DELETE, crex)

        except TimeoutError:
            self._handle_server_timeout(url, METH_DELETE)

        except Exception as ex:
            self._handle_general_request_failure(url, METH_DELETE, ex)

        return result

    async def _load_data(self, endpoints: dict, meter_count: str | None = None):
        if self.status == ConnectivityStatus.Connected:
            for endpoint_key in endpoints:
                if self.status == ConnectivityStatus.Connected:
                    endpoint = endpoints.get(endpoint_key)

                    data = await self._async_get(endpoint, meter_count)

                    if data is None:
                        continue

                    if meter_count is None:
                        if data is None:
                            _LOGGER.debug(
                                f"Cannot update {endpoint_key} due to empty data"
                            )

                        else:
                            self.data[endpoint_key] = data

                    else:
                        metered_data = self.data.get(endpoint_key, {})
                        metered_data[meter_count] = data

                        if metered_data is None:
                            _LOGGER.debug(
                                f"Cannot update {endpoint_key} for meter '{meter_count}' due to empty data"
                            )

                        else:
                            self.data[endpoint_key] = metered_data

    def _handle_client_error(
        self, endpoint: str, method: str, crex: ClientResponseError
    ):
        message = (
            "Failed to send HTTP request, "
            f"Endpoint: {endpoint}, "
            f"Method: {method}, "
            f"HTTP Status: {crex.message} ({crex.status})"
        )

        if crex.status == 401:
            self._set_status(ConnectivityStatus.NotConnected)

        elif crex.status > 401:
            self._set_status(ConnectivityStatus.Failed, message)

    def _handle_server_timeout(self, endpoint: str, method: str):
        message = (
            "Failed to send HTTP request due to timeout, "
            f"Endpoint: {endpoint}, "
            f"Method: {method}"
        )

        self._set_status(ConnectivityStatus.Failed, message)

    def _handle_general_request_failure(
        self, endpoint: str, method: str, ex: Exception
    ):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        message = (
            "Failed to send HTTP request, "
            f"Endpoint: {endpoint}, "
            f"Method: {method}, "
            f"Error: {ex}, "
            f"Line: {line_number}"
        )

        self._set_status(ConnectivityStatus.Failed, message)

    async def set_alert_settings(
        self, alert_type: AlertType, media_type: AlertChannel, enabled: bool
    ) -> None:
        """Handles ACTION_CORE_ENTITY_SELECT_OPTION."""
        if media_type is not None:
            _LOGGER.info(
                f"Updating alert {alert_type} on media {media_type} to {enabled}"
            )

            action = self._alert_settings_actions[enabled]

            url = self._build_endpoint(
                ENDPOINT_MY_ALERTS_SETTINGS_UPDATE, alert_type=alert_type.value
            )
            data = [media_type.value]

            await action(url, data)

            await asyncio.sleep(1)

            await self._load_data(ENDPOINT_DATA_RELOAD)

            self._async_dispatcher_send(SIGNAL_DATA_CHANGED)
