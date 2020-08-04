import json
import logging
import sys
from datetime import datetime
from typing import Optional

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ..helpers.const import BASE_URL, DATA_URL, HTML_DIV_PROPS, INPUTS
from ..managers.configuration_manager import ConfigManager

REQUIREMENTS = ["aiohttp"]

_LOGGER = logging.getLogger(__name__)


class CityMindApi:
    """The Class for handling the data retrieval."""

    is_logged_in: bool
    request_data: Optional[dict]
    session: ClientSession
    data: Optional[dict]
    hass: HomeAssistant
    config_manager: ConfigManager
    last_reading: Optional[float]
    consumption: Optional[float]

    def __init__(self, hass: HomeAssistant, config_manager: ConfigManager):

        try:
            self._last_update = datetime.now()
            self.hass = hass
            self.config_manager = config_manager
            self.request_data = None
            self.last_reading = None
            self.consumption = None

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

    async def async_get(self, url: Optional[str] = None):
        result = None

        try:
            url = f"{BASE_URL}/{url}"

            async with self.session.get(url, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.text()

                _LOGGER.debug(f"Full result: {result}")

                self._last_update = datetime.now()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to connect {BASE_URL}/{url}, Error: {ex}, "
                f"Line: {line_number}"
            )

        return result

    async def async_post(self, url: Optional[str], data: dict):
        response = None

        try:
            url = f"{BASE_URL}/{url}"

            async with self.session.post(
                url, data=json.dumps(data), ssl=False
            ) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                self._last_update = datetime.now()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to connect {BASE_URL}/{url}, Error: {ex}, "
                f"Line: {line_number}"
            )

        return response

    async def initialize(self):
        _LOGGER.info("Initializing BlueIris")

        try:
            self.is_logged_in = False
            self.data = None

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

        self.last_reading = None

        if await self.login():
            latest_reading = self.data.get("LastRead")

            if latest_reading is None:
                _LOGGER.error(
                    "Last read is not available for the property, "
                    f" data: {self.data}"
                )
            else:
                if self.last_reading is not None:
                    consumption_m3 = latest_reading - self.last_reading

                    self.consumption = consumption_m3 * 1000

            self.last_reading = latest_reading

    async def load_request_data(self):
        _LOGGER.info("Retrieving session ID")

        self.request_data = None

        _LOGGER.debug("Getting session from Water Meter service.")

        initial_resp = await self.async_get()

        soup = BeautifulSoup(initial_resp.text, "html.parser")
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

        self.is_logged_in = False

    async def login(self):
        _LOGGER.info("Performing login")

        logged_in = False

        try:
            self.data = None

            await self.load_request_data()

            if self.request_data is not None:
                response = await self.async_post("", self.request_data)
                url = response.url

                message = None

                if DATA_URL in response.url:

                    body = await response.text()

                    soup = BeautifulSoup(body, "html.parser")

                    properties_tag = soup.select_one(HTML_DIV_PROPS)

                    if properties_tag is None:
                        message = f"Invalid response - no data: {body}"

                    else:
                        # The data is hidden as json text inside the html
                        props_list = json.loads(properties_tag.text)

                        if len(props_list) == 0:
                            message = f"No properties found, data: {body}"

                        else:
                            self.data = props_list[0]

                else:
                    message = f"Login request redirected to {url}"

                if message is not None:
                    logged_in = False

                    _LOGGER.error(message)

                else:
                    logged_in = True

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line = tb.tb_lineno

            _LOGGER.error(f"Failed to login, Error: {ex}, Line: {line}")

        self.is_logged_in = logged_in

        return self.is_logged_in
