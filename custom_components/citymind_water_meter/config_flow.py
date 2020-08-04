"""Config flow to configure CityMind Water Meter."""
import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from .helpers.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONFIG_FLOW_DATA,
    CONFIG_FLOW_OPTIONS,
    DEFAULT_NAME,
    DOMAIN,
    ENTRY_PRIMARY_KEY,
)
from .managers.config_flow_manager import ConfigFlowManager
from .models import AlreadyExistsError, LoginError

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class DomainFlowHandler(config_entries.ConfigFlow):
    """Handle a domain config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        super().__init__()

        self._config_flow = ConfigFlowManager()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return DomainOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        _LOGGER.debug(f"Starting async_step_user of {DEFAULT_NAME}")

        errors = None

        await self._config_flow.initialize(self.hass)

        new_user_input = self._config_flow.clone_items(user_input)

        if user_input is not None:
            try:
                flow = self._config_flow

                data = await flow.update_data(user_input, CONFIG_FLOW_DATA)

                return self.async_create_entry(title=flow.title, data=data)
            except LoginError as lex:
                _LOGGER.warning("Cannot complete login")

                del new_user_input[CONF_USERNAME]
                del new_user_input[CONF_PASSWORD]

                errors = lex.errors

            except AlreadyExistsError as aeex:
                _LOGGER.warning(
                    f"{DEFAULT_NAME} with {ENTRY_PRIMARY_KEY}: "
                    f"{aeex.title} already exists"
                )

                errors = {"base": "already_configured"}

        schema = await self._config_flow.get_default_data(new_user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=new_user_input,
        )

    async def async_step_import(self, info):
        """Import existing configuration."""
        _LOGGER.debug("Starting async_step_import " f"of {DEFAULT_NAME}")

        title = f"{DEFAULT_NAME} (import from configuration.yaml)"

        return self.async_create_entry(title=title, data=info)


class DomainOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle domain options."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize domain options flow."""
        super().__init__()

        self._config_entry = config_entry

        self._config_flow = ConfigFlowManager()

    async def async_step_init(self, user_input=None):
        """Manage the domain options."""
        return await self.async_step_city_mind_additional_settings(user_input)

    async def async_step_city_mind_additional_settings(self, user_input=None):
        _LOGGER.info(f"Starting additional settings step: {user_input}")
        errors = None

        await self._config_flow.initialize(self.hass, self._config_entry)

        if user_input is not None:
            if user_input is not None:
                try:
                    options = await self._config_flow.update_options(
                        user_input, CONFIG_FLOW_OPTIONS
                    )

                    return self.async_create_entry(
                        title=self._config_flow.title, data=options
                    )
                except LoginError as lex:
                    _LOGGER.warning("Cannot complete login")

                    errors = lex.errors

                except AlreadyExistsError as aeex:
                    _LOGGER.warning(
                        f"{DEFAULT_NAME} with {ENTRY_PRIMARY_KEY}: "
                        f"{aeex.title} already exists"
                    )

                    errors = {"base": "already_configured"}

        schema = self._config_flow.get_default_options()

        return self.async_show_form(
            step_id="city_mind_additional_settings",
            data_schema=schema,
            errors=errors,
            description_placeholders=user_input,
        )
