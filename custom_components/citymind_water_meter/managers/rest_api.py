from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from datetime import datetime, timedelta
import logging
import sys
from typing import Any, Callable

from aiohttp import ClientResponseError, ClientSession

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
    FORMAT_DATE_ISO,
    FORMAT_DATE_YEAR_MONTH,
    LOGIN_DEVICE_ID,
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    ME_MUNICIPAL_ID,
    METER_COUNT,
    SIGNAL_API_STATUS,
    SIGNAL_DATA_CHANGED,
)
from ..common.enums import AlertChannel, AlertType
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class RestAPI:
    _hass: HomeAssistant | None
    data: dict

    _status: ConnectivityStatus | None
    _session: ClientSession | None
    _entry_id: str | None
    _dispatched_meters: list
    _dispatched_account: bool

    _last_valid: datetime | None

    today: str | None
    yesterday: str | None
    first_day_of_month: str | None
    _last_day_of_current_month: str | None
    current_month: str | None

    _alert_settings_actions: dict[bool, Callable[[str, list[int]], Awaitable[dict]]]

    def __init__(
        self,
        hass: HomeAssistant | None,
        config_data: ConfigData,
        entry_id: str | None = None,
    ):
        try:
            self._hass = hass
            self._support_video_browser_api = False

            self.data = {}

            self._config_data = config_data

            self._local_async_dispatcher_send = None

            self._status = None

            self._session = None
            self._entry_id = entry_id
            self._dispatched_devices = []
            self._dispatched_server = False
            self._last_valid = None

            self.today = None
            self.yesterday = None
            self.first_day_of_month = None
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
        _LOGGER.info("Initializing EdgeOS API")

        self._set_status(ConnectivityStatus.Connecting)

        await self._initialize_session()

        await self.login()

    async def terminate(self):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def validate(self):
        await self.initialize()

        await self.login()

    async def update(self):
        _LOGGER.debug(f"Updating data for user {self._config_data.email}")

        if self.status == ConnectivityStatus.Failed:
            await self.initialize(self._config_data)

        if self.status == ConnectivityStatus.Connected:
            self._set_date()

            if self.municipal_id is None:
                await self._load_data(ENDPOINT_DATA_INITIALIZE)

            await self._load_data(ENDPOINT_DATA_UPDATE)

            meters = self.data.get(API_DATA_SECTION_METERS, [])

            for meter in meters:
                meter_id = str(meter.get(METER_COUNT))

                await self._load_data(ENDPOINT_DATA_UPDATE_PER_METER, meter_id)

            self._async_dispatcher_send(SIGNAL_DATA_CHANGED)

    async def login(self):
        exception_data = None

        status = ConnectivityStatus.Failed

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
                    status = ConnectivityStatus.InvalidCredentials

                    exception_data = f"Error #{error_code}: {error_reason}"

                if token is not None:
                    self.data[API_DATA_TOKEN] = token

                    status = ConnectivityStatus.Connected

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            exception_data = f"Error: {ex}, Line: {line_number}"

        self._set_status(status)

        log_level = ConnectivityStatus.get_log_level(status)

        message = status if exception_data is None else f"{status}, {exception_data}"

        _LOGGER.log(log_level, message)

    async def _initialize_session(self):
        try:
            if self._is_home_assistant:
                self._session = async_create_clientsession(hass=self._hass)

            else:
                self._session = ClientSession()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(
                f"Failed to initialize session, Error: {str(ex)}, Line: {line_number}"
            )

            self._set_status(ConnectivityStatus.Failed)

    def _set_status(self, status: ConnectivityStatus):
        if status != self._status:
            log_level = ConnectivityStatus.get_log_level(status)

            _LOGGER.log(
                log_level,
                f"Status changed from '{self._status}' to '{status}'",
            )

            self._status = status

            self._async_dispatcher_send(SIGNAL_API_STATUS, status)

    def set_local_async_dispatcher_send(self, callback):
        self._local_async_dispatcher_send = callback

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        if self._hass is None:
            self._local_async_dispatcher_send(signal, None, *args)

        else:
            dispatcher_send(self._hass, signal, self._entry_id, *args)

    def _set_date(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        year = today.year if today.month <= 11 else today.year + 1
        month = today.month + 1 if today.month <= 11 else 1

        next_month_date = datetime(year=year, month=month, day=1)
        last_day_of_current_month = next_month_date - timedelta(days=1)

        first_day_of_month = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        self.today = today.strftime(FORMAT_DATE_ISO)
        self.yesterday = yesterday.strftime(FORMAT_DATE_ISO)
        self.current_month = today.strftime(FORMAT_DATE_YEAR_MONTH)
        self.first_day_of_month = first_day_of_month.strftime(FORMAT_DATE_ISO)
        self._last_day_of_current_month = last_day_of_current_month.strftime(
            FORMAT_DATE_ISO
        )

    def _build_endpoint(
        self, endpoint, meter_count: str | None = None, alert_type: str | None = None
    ):
        data = {
            ENDPOINT_PARAMETER_METER_ID: meter_count,
            ENDPOINT_PARAMETER_YESTERDAY: self.yesterday,
            ENDPOINT_PARAMETER_TODAY: self.today,
            ENDPOINT_PARAMETER_LAST_DAY_MONTH: self._last_day_of_current_month,
            ENDPOINT_PARAMETER_MUNICIPALITY_ID: self.municipal_id,
            ENDPOINT_PARAMETER_CURRENT_MONTH: self.current_month,
            ENDPOINT_PARAMETER_ALERT_TYPE: alert_type,
        }

        url = endpoint.format(**data)

        return url

    async def _async_post(self, endpoint, request_data: dict):
        result = None

        try:
            url = self._build_endpoint(endpoint)

            _LOGGER.debug(f"POST {url}")

            async with self._session.post(
                url, json=request_data, ssl=False
            ) as response:
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

            headers = {API_HEADER_TOKEN: self.token}

            _LOGGER.debug(f"GET {url}")

            async with self._session.get(url, headers=headers, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self.data[API_DATA_LAST_UPDATE] = datetime.now()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {endpoint}, HTTP Status: {crex.message} ({crex.status})"
            )

            if response.status == 401:
                self._set_status(ConnectivityStatus.NotConnected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {endpoint}, Error: {ex}, Line: {line_number}"
            )

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
            _LOGGER.error(
                f"Failed to get data from {url}, Data: {data}, HTTP Status: {crex.message} ({crex.status})"
            )

            if response.status == 401:
                self._set_status(ConnectivityStatus.NotConnected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {url}, Data: {data}, Error: {ex}, Line: {line_number}"
            )

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
            _LOGGER.error(
                f"Failed to get data from {url}, Data: {data}, HTTP Status: {crex.message} ({crex.status})"
            )

            if response.status == 401:
                self._set_status(ConnectivityStatus.NotConnected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {url}, Data: {data}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def _load_data(self, endpoints: dict, meter_count: str | None = None):
        if self.status == ConnectivityStatus.Connected:
            for endpoint_key in endpoints:
                if self.status == ConnectivityStatus.Connected:
                    endpoint = endpoints.get(endpoint_key)

                    data = await self._async_get(endpoint, meter_count)

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
