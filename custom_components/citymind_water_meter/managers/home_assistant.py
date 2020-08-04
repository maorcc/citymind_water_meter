"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import logging
import sys
from datetime import datetime
from typing import Optional

from cryptography.fernet import InvalidToken
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.entity_registry import \
    async_get_registry as er_async_get_registry
from homeassistant.helpers.event import async_track_time_interval

from ..api.api import CityMindApi
from ..helpers.const import (DEFAULT_NAME, DOMAIN, SCAN_INTERVAL, SIGNALS,
                             SUPPORTED_DOMAINS)
from ..models.config_data import ConfigData
from .configuration_manager import ConfigManager
from .device_manager import DeviceManager
from .entity_manager import EntityManager
from .password_manager import PasswordManager
from .storage_manager import StorageManager

_LOGGER = logging.getLogger(__name__)


class BlueIrisHomeAssistant:
    def __init__(self, hass: HomeAssistant, password_manager: PasswordManager):
        self._hass = hass

        self._remove_async_track_time = None

        self._is_initialized = False
        self._is_updating = False

        self._entity_registry = None

        self._api = None
        self._entity_manager = None
        self._device_manager = None
        self._storage_manager = None

        self._config_manager = ConfigManager(password_manager)

    @property
    def api(self) -> CityMindApi:
        return self._api

    @property
    def entity_manager(self) -> EntityManager:
        return self._entity_manager

    @property
    def device_manager(self) -> DeviceManager:
        return self._device_manager

    @property
    def entity_registry(self) -> EntityRegistry:
        return self._entity_registry

    @property
    def config_manager(self) -> ConfigManager:
        return self._config_manager

    @property
    def storage_manager(self) -> StorageManager:
        return self._storage_manager

    @property
    def config_data(self) -> Optional[ConfigData]:
        if self._config_manager is not None:
            return self._config_manager.data

        return None

    async def async_init(self, entry: ConfigEntry):
        try:
            self._storage_manager = StorageManager(self._hass)

            await self._config_manager.update(entry)

            self._api = CityMindApi(self._hass, self._config_manager)
            self._entity_manager = EntityManager(self._hass, self)
            self._device_manager = DeviceManager(self._hass, self)

            self._entity_registry = await er_async_get_registry(self._hass)

            self._hass.loop.create_task(self._async_init())
        except InvalidToken:
            error_message = (
                "Encryption key got corrupted, "
                "please remove the integration and re-add it"
            )

            _LOGGER.error(error_message)

            data = await self._storage_manager.async_load_from_store()
            data.key = None
            await self._storage_manager.async_save_to_store(data)

            await self._hass.services.async_call(
                "persistent_notification",
                "create",
                {"title": DEFAULT_NAME, "message": error_message},
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno
            msg = "Failed to async_init"

            _LOGGER.error(f"{msg}, error: {ex}, line: {line_number}")

    async def _async_init(self):
        load = self._hass.config_entries.async_forward_entry_setup

        for domain in SIGNALS:
            await load(self._config_manager.config_entry, domain)

        self._is_initialized = True

        await self.async_update_entry()

    def _update_entities(self, now):
        self._hass.async_create_task(self.async_update(now))

    async def async_update_entry(self, entry: ConfigEntry = None):
        update_config_manager = entry is not None

        if not update_config_manager:
            entry = self._config_manager.config_entry

            self._remove_async_track_time = async_track_time_interval(
                self._hass, self._update_entities, SCAN_INTERVAL
            )

        if not self._is_initialized:
            msg = "NOT INITIALIZED - Failed handling ConfigEntry change:"
            _LOGGER.info(f"{msg} {entry.as_dict()}")
            return

        _LOGGER.info(f"Handling ConfigEntry change: {entry.as_dict()}")

        if update_config_manager:
            await self._config_manager.update(entry)

        await self._api.initialize()

        await self.async_update(datetime.now())

    async def async_remove(self, entry: ConfigEntry):
        _LOGGER.info(f"Removing current integration - {entry.title}")

        if self._remove_async_track_time is not None:
            self._remove_async_track_time()
            self._remove_async_track_time = None

        unload = self._hass.config_entries.async_forward_entry_unload

        for domain in SUPPORTED_DOMAINS:
            await unload(entry, domain)

        await self._device_manager.async_remove()

        _LOGGER.info(f"Current integration ({entry.title}) removed")

    async def async_update(self, event_time):
        if not self._is_initialized:
            msg = "NOT INITIALIZED - "

            _LOGGER.info(f"{msg} Failed updating @{event_time}")
            return

        try:
            if self._is_updating:
                _LOGGER.debug(f"Skip updating @{event_time}")
                return

            _LOGGER.debug(f"Updating @{event_time}")

            self._is_updating = True

            await self._api.async_update()

            self.device_manager.update()
            self.entity_manager.update()

            await self.dispatch_all()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line = tb.tb_lineno

            _LOGGER.error(f"Failed to async_update, Error: {ex}, Line: {line}")

        self._is_updating = False

    async def delete_entity(self, domain, name):
        try:
            entity_manager = self.entity_manager

            entity = entity_manager.get_entity(domain, name)
            device_name = entity.device_name
            unique_id = entity.unique_id

            entity_manager.delete_entity(domain, name)

            device_in_use = entity_manager.is_device_name_in_use(device_name)

            entity_id = self.entity_registry.async_get_entity_id(
                domain, DOMAIN, unique_id
            )
            self.entity_registry.async_remove(entity_id)

            if not device_in_use:
                await self.device_manager.delete_device(device_name)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno
            msg = "Failed to delete_entity"

            _LOGGER.error(f"{msg}, Error: {ex}, Line: {line_number}")

    async def dispatch_all(self):
        if not self._is_initialized:
            _LOGGER.info("NOT INITIALIZED - Failed discovering components")
            return

        for domain in SUPPORTED_DOMAINS:
            signal = SIGNALS.get(domain)

            async_dispatcher_send(self._hass, signal)
