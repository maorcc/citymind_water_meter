"""Platform for sensor integration."""
import json
import logging

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from bs4 import BeautifulSoup as bs
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.const import VOLUME_CUBIC_METERS, VOLUME_LITERS
from homeassistant.helpers.entity import Entity

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
        self._session = None
        self._last_reading = None
        self._consumption = None

    def get_consumption(self):
        return self._consumption

    def get_reading(self):
        return self._last_reading

    def login(self):
        _LOGGER.info("Logging in to Water Meter service.")
        self._session = requests.session()  # Discard any old session if existed
        initial_resp = self._session.get('https://cp.city-mind.com/')
        if initial_resp.status_code != requests.codes.ok:
            _LOGGER.error(f'Error connecting to Water Meter service - %s - %s',
                          initial_resp.status_code, initial_resp.reason)
            self._session = None
            return None  # login failed
        soup = bs(initial_resp.text, "html.parser")
        # We mimic ASP frontend behavior, sending back most hidden HTML input fields.
        all_inputs = soup.find_all('input')
        payload = {v['name']: (v.get('value')) or '' for v in all_inputs}
        payload["txtEmail"] = self._username
        payload["txtPassword"] = self._password
        payload["cbRememberMe"] = 'on'
        # need to send some other fields
        payload["txtConsumerNumber"] = ''
        payload["__EVENTARGUMENT"] = ''
        payload["__LASTFOCUS"] = ''
        payload["ddlWaterAuthority"] = ''
        payload["ddlWaterAuthority"] = ''
        del payload['btnRegister']  # not needed
        del payload['cbAgree']  # not needed
        resp = self._session.post('https://cp.city-mind.com/', data=payload)
        if resp.status_code == requests.codes.ok and resp.url == 'https://cp.city-mind.com/Default.aspx':
            _LOGGER.info("login success to Water Meter service")
            return resp
        else:
            _LOGGER.error('Login to Water Meter failed. Username: %s . Check username and password', self._username)
            self._session = None
            return None  # login failed

    def refresh_data(self):
        if self._session is None:
            response = self.login()
        else:
            _LOGGER.debug("Fetching data from Water Meter service")
            response = self._session.get('https://cp.city-mind.com/Default.aspx')
            if response.status_code != requests.codes.ok:
                _LOGGER.error('Error response status %s - %s', response.status_code, response.reason)
                _LOGGER.info('Trying to login again')
                response = self.login()  # try a second time, before giving up for now
        if response is None:  # if Login failed
            return
        soup = bs(response.text, "html.parser")
        json_str = soup.select_one("#cphMain_div_properties").text  # The data is hidden as json text inside the html
        all_properties = json.loads(json_str)[0]  # For consumers is always only one entry in this array.
        meter = all_properties["LastRead"]  # the field in the json is called "LastRead"
        if self._last_reading is not None:
            self._consumption = int((meter - self._last_reading) * 1000)  # convert the increased amount to liters
        self._last_reading = meter


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
