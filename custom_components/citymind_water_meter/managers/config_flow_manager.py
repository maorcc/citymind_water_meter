import logging
from typing import Any, Dict, Optional

from cryptography.fernet import InvalidToken
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry

from .. import get_ha
from ..api.api import CityMindApi
from ..helpers.const import (
    CONF_ARR,
    CONF_LOG_LEVEL,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONFIG_FLOW_DATA,
    CONFIG_FLOW_INIT,
    CONFIG_FLOW_OPTIONS,
    DEFAULT_NAME,
    LOG_LEVELS,
)
from ..managers.configuration_manager import ConfigManager
from ..managers.password_manager import PasswordManager
from ..models import LoginError
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class ConfigFlowManager:
    _config_manager: ConfigManager
    _password_manager: PasswordManager
    _options: Optional[dict]
    _data: Optional[dict]
    _config_entry: Optional[ConfigEntry]
    api: Optional[CityMindApi]
    title: str

    def __init__(self):
        self._config_entry = None

        self._options = None
        self._data = None

        self._is_initialized = True
        self._hass = None
        self.api = None
        self.title = DEFAULT_NAME

    async def initialize(self, hass, config_entry: ConfigEntry = None):
        self._config_entry = config_entry
        self._hass = hass

        self._password_manager = PasswordManager(self._hass)
        self._config_manager = ConfigManager(self._password_manager)

        data = {}
        options = {}

        if self._config_entry is not None:
            data = self._config_entry.data
            options = self._config_entry.options

            self.title = self._config_entry.title

        await self.update_data(data, CONFIG_FLOW_INIT)
        await self.update_options(options, CONFIG_FLOW_INIT)

    @property
    def config_data(self) -> ConfigData:
        return self._config_manager.data

    async def update_options(self, options: dict, flow: str):
        _LOGGER.debug("Update options")
        validate_login = False

        new_options = await self._clone_items(options, flow)

        if flow == CONFIG_FLOW_OPTIONS:
            validate_login = self._should_validate_login(new_options)

            self._move_option_to_data(new_options)

        self._options = new_options

        await self._update_entry()

        if validate_login:
            await self._handle_data(flow)

        return new_options

    async def update_data(self, data: dict, flow: str):
        _LOGGER.debug("Update data")

        self._data = await self._clone_items(data, flow)

        await self._update_entry()

        await self._handle_data(flow)

        return self._data

    def _get_default_fields(
        self, flow, config_data: ConfigData = None
    ) -> Dict[vol.Marker, Any]:
        if config_data is None:
            config_data = self.config_data

        username = config_data.username
        password_clear_text = config_data.password_clear_text

        fields: Dict[vol.Marker, Any] = {
            vol.Optional(CONF_USERNAME, default=username): str,
            vol.Optional(CONF_PASSWORD, default=password_clear_text): str,
        }

        return fields

    async def get_default_data(self, user_input) -> vol.Schema:
        config_data = await self._config_manager.get_basic_data(user_input)

        fields = self._get_default_fields(CONFIG_FLOW_DATA, config_data)

        data_schema = vol.Schema(fields)

        return data_schema

    def get_default_options(self) -> vol.Schema:
        config_data = self.config_data

        fields = self._get_default_fields(CONFIG_FLOW_OPTIONS)

        log_level = config_data.log_level
        log_level_options = vol.In(LOG_LEVELS)
        log_level_field = vol.Optional(CONF_LOG_LEVEL, default=log_level)

        fields[log_level_field] = log_level_options

        data_schema = vol.Schema(fields)

        return data_schema

    async def _update_entry(self):
        try:
            entry = ConfigEntry(
                0, "", "", self._data, "", "", {}, options=self._options
            )

            await self._config_manager.update(entry)
        except InvalidToken:
            _LOGGER.info("Reset password")

            del self._data[CONF_PASSWORD]

            entry = ConfigEntry(
                0, "", "", self._data, "", "", {}, options=self._options
            )

            await self._config_manager.update(entry)

    async def _handle_password(self, user_input):
        if CONF_PASSWORD in user_input:
            password_clear_text = user_input[CONF_PASSWORD]
            password_manager = self._password_manager

            password = await password_manager.encrypt(password_clear_text)

            user_input[CONF_PASSWORD] = password

    async def _clone_items(self, user_input, flow: str):
        new_user_input = {}

        if user_input is not None:
            for key in user_input:
                user_input_data = user_input[key]

                new_user_input[key] = user_input_data

            if flow != CONFIG_FLOW_INIT:
                await self._handle_password(new_user_input)

        return new_user_input

    @staticmethod
    def clone_items(user_input):
        new_user_input = {}

        if user_input is not None:
            for key in user_input:
                user_input_data = user_input[key]

                new_user_input[key] = user_input_data

        return new_user_input

    def _should_validate_login(self, user_input: dict):
        validate_login = False
        data = self._data

        for conf in CONF_ARR:
            if data.get(conf) != user_input.get(conf):
                validate_login = True

                break

        return validate_login

    def _get_ha(self, key: str = None):
        if key is None:
            key = self.title

        ha = get_ha(self._hass, key)

        return ha

    def _move_option_to_data(self, options):
        for conf in CONF_ARR:
            if conf in options:
                self._data[conf] = options[conf]

                del options[conf]

    async def _handle_data(self, flow):
        if flow != CONFIG_FLOW_INIT:
            await self._valid_login()

        if flow == CONFIG_FLOW_OPTIONS:
            entries = self._hass.config_entries
            entries.async_update_entry(self._config_entry, data=self._data)

    async def _valid_login(self):
        errors = None

        api = CityMindApi(self._hass, self._config_manager)
        await api.initialize()

        if await api.login():
            data = api.data

            self.title = f"{data.consumer} [{data.serial_number}]"
        else:
            msg = "Failed to login CityMind due to invalid credentials"

            _LOGGER.warning(msg)

            errors = {"base": "invalid_credentials"}

        if errors is not None:
            raise LoginError(errors)
