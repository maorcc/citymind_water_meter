from copy import deepcopy
from datetime import datetime, timedelta
import json
import logging
import sys
from typing import Optional

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ..helpers.const import (
    BASE_URL,
    DATA_URL,
    DEFAULT_NAME,
    HTML_DIV_CONSUMER,
    HTML_DIV_FACTORY,
    HTML_DIV_PROPS,
    HTML_DIV_SN,
    INPUTS,
    STAT_FROM_QS,
    STAT_QS,
    STAT_TO_QS,
    STAT_URL,
)
from ..managers.configuration_manager import ConfigManager
from ..models.citymind_data import CityMindData
from ..models.response_data import ResponseData

REQUIREMENTS = ["aiohttp"]

_LOGGER = logging.getLogger(__name__)


class CityMindApi:
    """The Class for handling the data retrieval."""

    request_data: Optional[dict]
    session: ClientSession
    data: CityMindData
    previous_data: CityMindData

    hass: HomeAssistant
    config_manager: ConfigManager

    def __init__(self, hass: HomeAssistant, config_manager: ConfigManager):

        try:
            self._last_update = datetime.now()
            self.hass = hass
            self.config_manager = config_manager
            self.request_data = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno
            msg = f"Failed to load API, error: {ex}, line: {line_number}"

            _LOGGER.error(msg)

    @property
    def is_initialized(self):
        return self.session is not None and not self.session.closed

    @property
    def config_data(self):
        return self.config_manager.data

    async def async_get(self, url: str = "") -> ResponseData:
        result: ResponseData = ResponseData()
        result.status = 404

        try:
            url = f"{BASE_URL}/{url}"

            async with self.session.get(url, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                result.status = response.status
                result.reason = response.reason
                result.url = response.url.path

                response.raise_for_status()

                result.data = await response.text()

                self._last_update = datetime.now()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to connect {BASE_URL}/{url}, "
                f"Error: {ex}, "
                f"Line: {line_number}"
            )

        return result

    async def async_post(self, url: str, data: dict) -> ResponseData:
        result: ResponseData = ResponseData()
        result.status = 404

        try:
            url = f"{BASE_URL}/{url}"

            session = self.session

            async with session.post(url, data=data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                result.status = response.status
                result.reason = response.reason
                result.url = response.url.path

                response.raise_for_status()

                self._last_update = datetime.now()

                result.data = await response.text()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to connect {BASE_URL}/{url}, Error: {ex}, "
                f"Line: {line_number}"
            )

        return result

    async def initialize(self):
        _LOGGER.info(f"Initializing {DEFAULT_NAME}")

        try:
            self.data = CityMindData()
            self.previous_data = CityMindData()

            if self.hass is None:
                if self.session is not None:
                    await self.session.close()

                self.session = aiohttp.client.ClientSession()
            else:
                self.session = async_create_clientsession(hass=self.hass)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize CityMind API ({BASE_URL}), "
                f"error: {ex}, line: {line_number}"
            )

    async def async_update(self):
        _LOGGER.info(f"Updating data from CityMind {self.config_data.name})")

        if await self.login():
            previous_reading = self.previous_data.last_read
            current_reading = self.data.last_read

            if current_reading is not None and previous_reading is not None:
                consumption_m3 = current_reading - previous_reading

                self.data.consumption = consumption_m3 * 1000

            _LOGGER.info(f"CityMind data updated: {self.data}")

    async def load_request_data(self):
        _LOGGER.info("Retrieving session ID")

        self.request_data = None

        _LOGGER.debug("Getting session from Water Meter service.")

        response = await self.async_get()

        soup = BeautifulSoup(response.data, "html.parser")
        all_inputs = soup.find_all("input")

        # Initiate clean session payload
        session = {
            "txtEmail": self.config_data.username,
            "txtPassword": self.config_data.password_clear_text,
        }

        # Add to session data fields from ASP.NET WebForm
        # VIEW STATES and EVENT session
        for item in all_inputs:
            name = item.get("name")
            value = item.get("value", "")

            if name in INPUTS and value is not None:
                session[name] = value

        _LOGGER.info("Session data created successfully")

        self.request_data = session

    async def login(self):
        _LOGGER.info("Performing login")

        message = None

        logged_in = False

        data = CityMindData()

        try:
            await self.load_request_data()

            if self.request_data is not None:
                response = await self.async_post("", self.request_data)
                url = response.url

                if DATA_URL == url:
                    body = response.data

                    soup = BeautifulSoup(body, "html.parser")

                    properties = soup.select_one(HTML_DIV_PROPS)
                    factory = soup.select_one(HTML_DIV_FACTORY)
                    consumer = soup.select_one(HTML_DIV_CONSUMER)
                    serial_number = soup.select_one(HTML_DIV_SN)

                    data.provider = factory.text
                    data.consumer = consumer.text
                    data.serial_number = serial_number.text

                    if properties is None:
                        message = "Invalid response"

                    else:
                        # The data is hidden as json text inside the html
                        props_list = json.loads(properties.text)

                        if len(props_list) == 0:
                            message = "No properties found"

                        else:
                            data.property = props_list[0]

                            if "LastRead" in data.property:
                                self._update_metrics(data)

                                logged_in = True

                            else:
                                message = (
                                    "Last read is not available for "
                                    f"the property,  data: {data.property}"
                                )

                        await self._load_daily_consumptions(data)

                else:
                    message = f"Login request redirected to {url}"

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line = tb.tb_lineno

            message = f"Failed to login, Error: {ex}, Line: {line}"

        if message is not None:
            _LOGGER.error(message)

        previous_data = deepcopy(self.data)

        self.data = data
        self.previous_data = previous_data

        return logged_in

    async def _load_daily_consumptions(self, data: CityMindData):
        today = datetime.now()
        yesterday = datetime.now() - timedelta(1)
        yesterday_str = yesterday.strftime("%d%m%Y")
        today_str = today.strftime("%d%m%Y")

        get_daily_stat = self._get_daily_consumption

        data.yesterday_consumption = await get_daily_stat(yesterday_str)
        data.today_consumption = await get_daily_stat(today_str)

    async def _get_daily_consumption(self, date):
        qs = f"{STAT_QS}&{STAT_FROM_QS}={date}&{STAT_TO_QS}={date}"
        url = f"{STAT_URL}?{qs}"

        response = await self.async_get(url)

        daily_consumption: Optional[float] = None

        _LOGGER.info(f"{response}")

        if response.status == 200:
            try:
                json_data = json.loads(response.data)
                result = json_data.get("Response_Message", {})
                rows = result.get("Data_Rows", [])
                first_row = rows[0]
                row_data = first_row.get("Row", [])
                data_item = row_data[1]
                daily_consumption = float(data_item.get("Data", 0))
            except Exception as ex:
                exc_type, exc_obj, tb = sys.exc_info()
                line = tb.tb_lineno

                _LOGGER.error(f"Extract {date} failed, Error: {ex} [{line}]")

        return daily_consumption

    def _update_metrics(self, data):
        last_read = self._get_metrics(data, "LastRead")
        monthly = self._get_metrics(data, "Common_Consumption")
        predication = self._get_metrics(data, "Estemated_Consumption")

        data.last_read = last_read
        data.monthly_consumption = monthly
        data.consumption_predication = predication

    @staticmethod
    def _get_metrics(data, key) -> Optional[float]:
        metrics = data.property.get(key)

        if metrics is not None:
            metrics = float(metrics)

        return metrics
