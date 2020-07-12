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


# noinspection PyUnusedLocal
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    data_provider = DataProvider(config[CONF_USERNAME], config[CONF_PASSWORD])
    add_entities(
        [WaterMeterReadingSensor(data_provider),
         WaterConsumptionSensor(data_provider)]
    )


class DataProvider:
    """Get data from cp.city-mind.com"""

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._last_reading = None
        self._consumption = None

    def get_consumption(self):
        return self._consumption

    def get_reading(self):
        return self._last_reading

    def refresh_data(self):
        data = get_request_data()
        data["txtEmail"] = self._username
        data["txtPassword"] = self._password

        response = requests.post(
            "https://cp.city-mind.com/", headers=get_headers(), data=data
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            json_str = soup.select_one("#cphMain_div_properties").text
            all_properties = json.loads(json_str)[0]
            meter = all_properties["LastRead"]
            if self._last_reading is not None:
                self._consumption = int((meter - self._last_reading) * 1000)
            self._last_reading = meter
        else:
            _LOGGER.warning('response status code %s', response.status_code)


class WaterMeterReadingSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, data_provider):
        """Initialize the sensor."""
        self._data_provider = data_provider

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Water Meter Reading"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._data_provider.get_reading()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return VOLUME_CUBIC_METERS

    @property
    def icon(self):
        return 'mdi:counter'

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
        return self._data_provider.get_consumption()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return VOLUME_LITERS

    @property
    def icon(self):
        return 'mdi:speedometer'

    def update(self):
        """No need to do anything here because the data is always up-to-date"""
        pass
