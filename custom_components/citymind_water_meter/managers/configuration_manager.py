import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry

from ..helpers.const import (
    CONF_LOG_LEVEL,
    CONF_PASSWORD,
    CONF_USERNAME,
    LOG_LEVEL_DEFAULT,
)
from ..models.config_data import ConfigData
from .password_manager import PasswordManager

_LOGGER = logging.getLogger(__name__)


class ConfigManager:
    data: ConfigData
    config_entry: ConfigEntry
    password_manager: PasswordManager

    def __init__(self, password_manager: Optional[PasswordManager]):
        self.password_manager = password_manager

    async def update(self, config_entry: ConfigEntry):
        data = config_entry.data
        options = config_entry.options

        result: ConfigData = await self.get_basic_data(data)

        result.log_level = options.get(CONF_LOG_LEVEL, LOG_LEVEL_DEFAULT)

        self.config_entry = config_entry
        self.data = result

    async def get_basic_data(self, data):
        result = ConfigData()

        if data is not None:
            result.username = data.get(CONF_USERNAME)
            result.password = data.get(CONF_PASSWORD)

            if (
                result.password is not None
                and len(result.password) > 0
                and self.password_manager is not None
            ):
                decrypt = self.password_manager.decrypt

                result.password_clear_text = await decrypt(result.password)
            else:
                result.password_clear_text = result.password

        return result

    @staticmethod
    def _get_allowed_option(key, options):
        allowed_audio_sensor = None
        if key in options:
            allowed_audio_sensor = options.get(key, [])

        return allowed_audio_sensor

    @staticmethod
    def _get_config_data_item(key, options, data):
        data_result = data.get(key, "")

        result = options.get(key, data_result)

        return result
