"""Platform for sensor integration."""
import json
import logging

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from bs4 import BeautifulSoup
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.const import VOLUME_CUBIC_METERS, VOLUME_LITERS
from homeassistant.helpers.entity import Entity

from custom_components.citymind_water_meter.const import get_headers, get_request_data

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_USERNAME): cv.string, vol.Required(CONF_PASSWORD): cv.string, }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities(
        [WaterMeterReadingSensor(config[CONF_USERNAME], config[CONF_PASSWORD]),
        WaterConsumptionSensor(config[CONF_USERNAME], config[CONF_PASSWORD])]
    )


class WaterMeterReadingSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, username, password):
        """Initialize the sensor."""
        self._state = None
        self._username = username
        self._password = password

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Water Meter Reading"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return VOLUME_CUBIC_METERS

    @property
    def icon(self):
        return 'mdi:counter'

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        data = get_request_data()
        data["txtEmail"] = self._username
        data["txtPassword"] = self._password

        response = requests.post(
            "https://cp.city-mind.com/", headers=get_headers(), data=data
        )
        soup = BeautifulSoup(response.text, "html.parser")
        json_str = soup.select_one("#cphMain_div_properties").text
        all_properties = json.loads(json_str)[0]
        meter = all_properties["LastRead"]
        _LOGGER.warning(meter)
        self._state = meter


class WaterConsumptionSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, username, password):
        """Initialize the sensor."""
        self._state = 0
        self._previous_reading = None
        self._username = username
        self._password = password

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Water Consumption"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return VOLUME_LITERS

    @property
    def icon(self):
        return 'mdi:speedometer'

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        data = get_request_data()
        data["txtEmail"] = self._username
        data["txtPassword"] = self._password

        response = requests.post(
            "https://cp.city-mind.com/", headers=get_headers(), data=data
        )
        soup = BeautifulSoup(response.text, "html.parser")
        json_str = soup.select_one("#cphMain_div_properties").text
        all_properties = json.loads(json_str)[0]
        new_reading = all_properties["LastRead"]
        _LOGGER.warning(new_reading)
        if self._previous_reading is not None:
            self._state = (new_reading - self._previous_reading) * 1000
        self._previous_reading = new_reading
