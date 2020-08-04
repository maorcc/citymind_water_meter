import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..managers.home_assistant import CityMindHomeAssistant
from ..managers.password_manager import PasswordManager
from .const import (CONF_LOG_LEVEL, DOMAIN, DOMAIN_DATA, DOMAIN_LOGGER,
                    LOG_LEVEL_DEFAULT, PASSWORD_MANAGER, SERVICE_SET_LEVEL)

_LOGGER = logging.getLogger(__name__)


def clear_ha(hass: HomeAssistant, entry_id):
    if DOMAIN_DATA not in hass.data:
        hass.data[DOMAIN_DATA] = dict()

    del hass.data[DOMAIN_DATA][entry_id]


def get_ha(hass: HomeAssistant, entry_id):
    ha_data = hass.data.get(DOMAIN_DATA, dict())
    ha = ha_data.get(entry_id)

    return ha


async def async_set_ha(hass: HomeAssistant, entry: ConfigEntry):
    try:
        if DOMAIN_DATA not in hass.data:
            hass.data[DOMAIN_DATA] = dict()

        if PASSWORD_MANAGER not in hass.data:
            hass.data[PASSWORD_MANAGER] = PasswordManager(hass)

        password_manager = hass.data[PASSWORD_MANAGER]

        instance = CityMindHomeAssistant(hass, password_manager)

        await instance.async_init(entry)

        hass.data[DOMAIN_DATA][entry.entry_id] = instance
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line = tb.tb_lineno

        _LOGGER.error(f"Failed to async_set_ha, error: {ex}, line: {line}")


async def handle_log_level(hass: HomeAssistant, entry: ConfigEntry):
    log_level = entry.options.get(CONF_LOG_LEVEL, LOG_LEVEL_DEFAULT)

    if log_level == LOG_LEVEL_DEFAULT:
        return

    log_level_data = {f"custom_components.{DOMAIN}": log_level.lower()}

    async_call = hass.services.async_call

    await async_call(DOMAIN_LOGGER, SERVICE_SET_LEVEL, log_level_data)
