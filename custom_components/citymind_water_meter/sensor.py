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
        self._payload = None
        self._last_reading = None
        self._consumption = None

    def get_consumption(self):
        return self._consumption

    def get_reading(self):
        return self._last_reading

    def create_session(self):
        """
        Sessions in cp.city-mind.com are strange.  Here are few observations:
        1. Sessions seem to exist for unlimited time.
        2. A session needs to be retrieved from server before a login operation can be done.
        3. On most computers, even in Incognito mode, whenever we ask for a session, we always get the same session data.
           It is not clear how the server uniquely identifies that it is the same client, even if it did not connect
           for a very long time.
        4. Login operation authenticate the session for only few minutes. After that a new login operation (with the
           same session data needs to be done.
        So here we create a session only once. If there later we see errors, we will try to recreate a session, but
        but so far such case have not been observed.
        """
        self._session = None
        self._payload = None
        _LOGGER.debug("Getting session from Water Meter service.")
        session = requests.session()
        initial_resp = session.get(LOGIN_URL, timeout=10)
        if initial_resp.status_code != requests.codes.ok:
            _LOGGER.error('Error connecting to Water Meter service - %s - %s',
                          initial_resp.status_code, initial_resp.reason)
            return  # login failed, so leaving the self._session as None
        soup = bs(initial_resp.text, "html.parser")
        # We mimic ASP frontend behavior, sending back most hidden HTML input fields.
        all_inputs = soup.find_all('input')
        # transform from structure from list like [{'name': myName, 'value': myVal}] to dictionary
        payload = {v['name']: (v.get('value')) or '' for v in all_inputs}
        # add some params
        payload.update({
            "txtEmail": self._username,
            "txtPassword": self._password,
            "cbRememberMe": 'on',
            "txtConsumerNumber": '',
            "__EVENTARGUMENT": '',
            "__LASTFOCUS": '',
            "ddlWaterAuthority": ''
        })
        del payload['btnRegister']  # not needed
        del payload['cbAgree']  # not needed
        _LOGGER.info("Reusable session data from the Water Meter service retrieved successfully.")
        self._session = session
        self._payload = payload

    def fetch_data(self):
        # all data is received in the html after login operation
        resp = self._session.post(LOGIN_URL, data=self._payload, timeout=10)
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
        try:
            if self._session is None:
                self.create_session()
                meter = self.fetch_data()
            else:
                meter = self.fetch_data()
                if meter is None:
                    _LOGGER.warning('Existing session failed fetching data.  Trying to create a new session.')
                    self.create_session()  # if session doesn't work, try creating a new session
                    meter = self.fetch_data()
            if meter is None:
                return
            _LOGGER.debug("Fetched last read from Water Meter service: %s", meter)
            if self._last_reading is not None:
                self._consumption = int((meter - self._last_reading) * 1000)  # convert the increased amount to liters
            self._last_reading = meter
        except requests.exceptions.RequestException as e:
            _LOGGER.error('RequestException from Water Meter service: %s', e)


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
        return 'mdi:water-pump'

    def update(self):
        """No need to do anything here because the data is always up-to-date"""
        pass
