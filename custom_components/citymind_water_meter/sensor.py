"""Platform for sensor integration."""
import json
import logging
from typing import Optional

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from bs4 import BeautifulSoup
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_PASSWORD, CONF_USERNAME,
                                 VOLUME_CUBIC_METERS, VOLUME_LITERS)
from homeassistant.helpers.entity import Entity
from pyexpat.errors import codes
from requests import RequestException

LOGIN_URL = "https://cp.city-mind.com/"
DATA_URL = f"{LOGIN_URL}Default.aspx"

INPUTS = [
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__EVENTVALIDATION",
    "btnLogin",
]

FIELDS = {
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(FIELDS)

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    data_provider = DataProvider(config[CONF_USERNAME], config[CONF_PASSWORD])
    data_provider.refresh_data()

    reading_sensor = WaterMeterReadingSensor(data_provider)
    consumption_sensor = WaterConsumptionSensor(data_provider)

    add_entities([reading_sensor, consumption_sensor], True)


class DataProvider:
    """Get data from cp.city-mind.com"""

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._session = None
        self._last_reading: Optional[float] = None
        self._consumption: Optional[float] = None
        self._data = None

    @property
    def consumption(self) -> Optional[float]:
        return self._consumption

    @property
    def reading(self) -> Optional[float]:
        return self._last_reading

    def _create_request_data(self):
        """
        Since ASP.NET session defined on the server side and we don't know
        When it will get expired, we need to perform login on every request
        """
        self._session = None

        _LOGGER.debug("Getting session from Water Meter service.")

        initial_resp = requests.get(LOGIN_URL, timeout=10)

        if initial_resp.status_code != codes.ok:
            # login failed, so leaving the self._session as None
            _LOGGER.error(
                "Failed to connect to Water Meter service, "
                f"error: {initial_resp.reason} [{initial_resp.status_code}]"
            )

            return

        soup = BeautifulSoup(initial_resp.text, "html.parser")
        all_inputs = soup.find_all("input")

        # Initiate clean session payload
        session = {"txtEmail": self._username, "txtPassword": self._password}

        # Add to session data fields from ASP.NET WebForm
        # VIEW STATES and EVENT session
        for item in all_inputs:
            name = item.get("name")
            value = item.get("value", "")

            if name in INPUTS and value is not None:
                session[name] = value

        _LOGGER.info("Session data created successfully")

        self._session = session

    def _update_data(self, retry: bool = True):
        if self._session is None:
            self._create_request_data()

        if self._session is not None:
            # all data is received in the html after login operation
            data = requests.post(LOGIN_URL, data=self._session, timeout=10)

            if data is None:
                self._session = None

                if retry:
                    # Retry to with new session one more time
                    self._update_data(False)

        else:
            # No data available
            self._data = None

    def _get_latest_reading(self) -> Optional[float]:
        latest_reading: Optional[float] = None

        status_code = self._data.status_code
        reason = self._data.reason
        url = self._data.url
        body = self._data.text

        message = None

        if status_code == codes.ok:

            if url == DATA_URL:
                soup = BeautifulSoup(body, "html.parser")
                properties_tag = soup.select_one("#cphMain_div_properties")

                if properties_tag is None:
                    message = f"Invalid response - no data: {body}"

                else:
                    # The data is hidden as json text inside the html
                    props_list = json.loads(properties_tag.text)

                    if len(props_list) == 0:
                        message = f"No properties found, data: {body}"

                    else:
                        all_properties = props_list[0]

                        latest_reading = all_properties.get("LastRead")

                        if latest_reading is None:
                            message = (
                                "Last read is not available for "
                                f"the property, data: {body}"
                            )

            else:
                message = f"Login request redirected to {url}"

        else:
            message = f"Request to {url} failed due {reason} [{status_code}]"

        if latest_reading is None:
            self._session = None

            if message is not None:
                _LOGGER.error(message)

        return latest_reading

    def refresh_data(self):
        try:
            self._update_data()

            latest_reading: Optional[float] = self._get_latest_reading()

            if self._last_reading is not None:
                # convert the increased amount to liters
                consumption_m3 = latest_reading - self._last_reading

                self._consumption = consumption_m3 * 1000

            self._last_reading = latest_reading

        except RequestException as e:
            _LOGGER.error(f"Request failed, error: {str(e)}")


class WaterMeterReadingSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, data_provider: DataProvider):
        """Initialize the sensor."""
        self._data_provider = data_provider

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Water Meter Reading"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._data_provider.reading

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return VOLUME_CUBIC_METERS

    @property
    def icon(self):
        return "mdi:counter"

    def update(self):
        self._data_provider.refresh_data()


class WaterConsumptionSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, data_provider):
        """Initialize the sensor."""
        self._data_provider = data_provider

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Water Consumption"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._data_provider.consumption

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return VOLUME_LITERS

    @property
    def icon(self):
        return "mdi:water-pump"

    def update(self):
        """No need to do anything here because the data is always up-to-date"""
        self._data_provider.refresh_data()
