"""
Support for CityMind Water Meter.
"""
from datetime import timedelta

from homeassistant.components.sensor import DOMAIN as DOMAIN_SENSOR
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME

CONF_LOG_LEVEL = "log_level"

ENTRY_PRIMARY_KEY = CONF_NAME

CONFIG_FLOW_DATA = "config_flow_data"
CONFIG_FLOW_OPTIONS = "config_flow_options"
CONFIG_FLOW_INIT = "config_flow_init"

VERSION = "2.0.0"

DOMAIN = "citymind_water_meter"
PASSWORD_MANAGER = f"pm_{DOMAIN}"
DOMAIN_DATA = f"data_{DOMAIN}"
DOMAIN_API = f"{DOMAIN}_API"
DOMAIN_HA = f"{DOMAIN}_HA"
DOMAIN_HA_ENTITIES = f"{DOMAIN}_HA_Entities"
DEFAULT_NAME = "CityMind Water Meter"
DEFAULT_PORT = 80

DOMAIN_KEY_FILE = f"{DOMAIN}.key"
JSON_DATA_FILE = f"custom_components/{DOMAIN}/data/[NAME].json"

DOMAIN_LOGGER = "logger"
SERVICE_SET_LEVEL = "set_level"

AUTH_ERROR = "Authorization required"

NOTIFICATION_ID = f"{DOMAIN}_notification"
NOTIFICATION_TITLE = f"{DEFAULT_NAME} Setup"

DEFAULT_ICON = "mdi:alarm-light"

ATTR_FRIENDLY_NAME = "friendly_name"

SCAN_INTERVAL = timedelta(minutes=30)

DISCOVERY = f"{DOMAIN}_discovery"

UPDATE_SIGNAL = f"{DOMAIN}_UPDATE_SIGNAL"

SUPPORTED_DOMAINS = [DOMAIN_SENSOR]
SIGNALS = {DOMAIN_SENSOR: UPDATE_SIGNAL}

ENTITY_ID = "id"
ENTITY_NAME = "name"
ENTITY_STATE = "state"
ENTITY_ATTRIBUTES = "attributes"
ENTITY_ICON = "icon"
ENTITY_UNIQUE_ID = "unique-id"
ENTITY_DEVICE_CLASS = "device-class"
ENTITY_DEVICE_NAME = "device-name"
ENTITY_UNIT = "unit"
ENTITY_DISABLED = "disabled"


ENTITY_STATUS = "entity-status"
ENTITY_STATUS_EMPTY = None
ENTITY_STATUS_READY = f"{ENTITY_STATUS}-ready"
ENTITY_STATUS_CREATED = f"{ENTITY_STATUS}-created"
ENTITY_STATUS_MODIFIED = f"{ENTITY_STATUS}-modified"
ENTITY_STATUS_IGNORE = f"{ENTITY_STATUS}-ignore"
ENTITY_STATUS_CANCELLED = f"{ENTITY_STATUS}-cancelled"

DOMAIN_LOAD = "load"
DOMAIN_UNLOAD = "unload"

LOG_LEVEL_DEFAULT = "Default"
LOG_LEVEL_DEBUG = "Debug"
LOG_LEVEL_INFO = "Info"
LOG_LEVEL_WARNING = "Warning"
LOG_LEVEL_ERROR = "Error"

LOG_LEVELS = [
    LOG_LEVEL_DEFAULT,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
]

CONF_ARR = [CONF_USERNAME, CONF_PASSWORD]

BASE_URL = "https://cp.city-mind.com"
DATA_URL = "/Default.aspx"

VIEW_STATE = "__VIEWSTATE"
EVENT_ARGS = "__VIEWSTATEGENERATOR"
EVENT_VALID = "__EVENTVALIDATION"
BTN_LOGIN = "btnLogin"

INPUTS = [VIEW_STATE, EVENT_ARGS, EVENT_VALID, BTN_LOGIN]

HTML_DIV_PROPS = "#cphMain_div_properties"
HTML_DIV_FACTORY = "#lblFactoryName"
HTML_DIV_CONSUMER = "#lblConsumerName"
HTML_DIV_SN = "#cphMain_lblMeterSN"
