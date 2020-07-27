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

LOGIN_URL = 'https://cp.city-mind.com/'
DATA_URL = 'https://cp.city-mind.com/Default.aspx'

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
        _LOGGER.debug("Logging in to Water Meter service.")
        self._session = requests.session()  # Discard any old session if existed
        initial_resp = self._session.get(LOGIN_URL)
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
        resp = self._session.post(LOGIN_URL, data=payload)
        meter = self.extract_meter_value(resp)  # return None if response is no good
        if meter is not None:
            _LOGGER.info("Login successful to the Water Meter service.")
        return meter

    def fetch_data(self):
        resp = self._session.get(DATA_URL)
        return self.extract_meter_value(resp)

    def extract_meter_value(self, data_response):
        if data_response.status_code != requests.codes.ok:
            _LOGGER.error('Error response status %s - %s: %s', data_response.status_code, data_response.reason,
                          data_response.url)
            self._session = None  # Session is no good.  Need to login again.
            return None
        elif data_response.url != DATA_URL:
            _LOGGER.error('Redirected to %s , probably because session expired.', data_response.url)
            self._session = None
            return None
        soup = bs(data_response.text, "html.parser")
        properties_tag = soup.select_one("#cphMain_div_properties")
        if properties_tag is None:
            _LOGGER.error('Data not found in response from server:\n%s', data_response.text)
            self._session = None
            return None
        json_str = properties_tag.text  # The data is hidden as json text inside the html
        props_list = json.loads(json_str)
        if len(props_list) != 1:  # For consumers always one entry in this array.
            _LOGGER.error('Data from server contains an empty #cphMain_div_properties tag:\n%s', data_response.text)
            self._session = None
            return None
        all_properties = props_list[0]  # For consumers is always only one entry in this array.
        if 'LastRead' not in all_properties:
            _LOGGER.error('Data from server contains #cphMain_div_properties tag with no LastRead:\n%s',
                          data_response.text)
            self._session = None
            return None
        meter = all_properties["LastRead"]  # the field in the json is called "LastRead"
        return meter

    def refresh_data(self):
        _LOGGER.debug("Fetching data from Water Meter service")
        if self._session is None:
            meter = self.login()
        else:
            meter = self.fetch_data()
            if meter is None:
                meter = self.login()  # if session expired, try login again
        if meter is None:
            return
        _LOGGER.debug("Fetched last read from Water Meter service: %s", meter)
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
