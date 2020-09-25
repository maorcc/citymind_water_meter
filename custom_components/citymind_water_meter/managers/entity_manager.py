import logging
import sys
from typing import Dict, List, Optional

from homeassistant.const import VOLUME_CUBIC_METERS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from ..api.api import CityMindApi
from ..helpers.const import (
    ATTR_FRIENDLY_NAME,
    DEFAULT_ICON,
    DOMAIN,
    DOMAIN_SENSOR,
    ENTITY_STATUS_CREATED,
    ENTITY_STATUS_EMPTY,
    ENTITY_STATUS_READY,
    SIGNALS,
)
from ..models.config_data import ConfigData
from ..models.entity_data import EntityData
from .configuration_manager import ConfigManager
from .device_manager import DeviceManager

_LOGGER = logging.getLogger(__name__)


def _get_camera_binary_sensor_key(topic, event_type):
    key = f"{topic}_{event_type}".lower()

    return key


class EntityManager:
    hass: HomeAssistant
    ha = None
    entities: dict
    domain_component_manager: dict

    def __init__(self, hass, ha):
        self.hass = hass
        self.ha = ha
        self.domain_component_manager = {}
        self.entities = {}

    @property
    def entity_registry(self) -> EntityRegistry:
        return self.ha.entity_registry

    @property
    def config_data(self) -> ConfigData:
        return self.ha.config_data

    @property
    def config_manager(self) -> ConfigManager:
        return self.ha.config_manager

    @property
    def api(self) -> CityMindApi:
        return self.ha.api

    @property
    def device_manager(self) -> DeviceManager:
        return self.ha.device_manager

    @property
    def integration_title(self) -> str:
        return self.config_manager.config_entry.title

    def set_domain_component(self, domain, async_add_entities, component):
        self.domain_component_manager[domain] = {
            "async_add_entities": async_add_entities,
            "component": component,
        }

    def is_device_name_in_use(self, device_name):
        result = False

        for entity in self.get_all_entities():
            if entity.device_name == device_name:
                result = True
                break

        return result

    def get_all_entities(self) -> List[EntityData]:
        entities = []
        for domain in self.entities:
            for name in self.entities[domain]:
                entity = self.entities[domain][name]

                entities.append(entity)

        return entities

    def check_domain(self, domain):
        if domain not in self.entities:
            self.entities[domain] = {}

    def get_entities(self, domain) -> Dict[str, EntityData]:
        self.check_domain(domain)

        return self.entities[domain]

    def get_entity(self, domain, name) -> Optional[EntityData]:
        entities = self.get_entities(domain)
        entity = entities.get(name)

        return entity

    def get_entity_status(self, domain, name):
        entity = self.get_entity(domain, name)

        status = ENTITY_STATUS_EMPTY if entity is None else entity.status

        return status

    def set_entity_status(self, domain, name, status):
        if domain in self.entities and name in self.entities[domain]:
            self.entities[domain][name].status = status

    def delete_entity(self, domain, name):
        if domain in self.entities and name in self.entities[domain]:
            del self.entities[domain][name]

    def set_entity(self, domain, name, data: EntityData):
        try:
            self.check_domain(domain)

            self.entities[domain][name] = data
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to set_entity, domain: {domain}, name: {name}"
            )

    def create_components(self):
        self.generate_water_last_reading_sensor()
        self.generate_water_consumption_estimation_sensor()
        self.generate_water_monthly_consumption_sensor()

        data = self.api.data
        daily_consumption_sensor = self.generate_water_daily_consumption_sensor

        daily_consumption_sensor("Yesterday", data.yesterday_consumption)
        daily_consumption_sensor("Today", data.today_consumption)

    def update(self):
        self.hass.async_create_task(self._async_update())

    async def _async_update(self):
        step = "Mark as ignore"
        try:
            to_delete = []

            for entity in self.get_all_entities():
                to_delete.append(entity.unique_id)

            step = "Create components"

            self.create_components()

            step = "Start updating"

            for domain in SIGNALS:
                step = f"Start updating domain {domain}"

                entities_to_add = []
                domain_manager = self.domain_component_manager[domain]
                domain_component = domain_manager["component"]
                async_add_entities = domain_manager["async_add_entities"]

                entities = dict(self.get_entities(domain))

                for entity_key in entities:
                    step = f"Start updating {domain} -> {entity_key}"

                    entity = entities[entity_key]

                    entity_id = self.entity_registry.async_get_entity_id(
                        domain, DOMAIN, entity.unique_id
                    )

                    if entity.status == ENTITY_STATUS_CREATED:
                        entity_item = self.entity_registry.async_get(entity_id)

                        is_disabled = False
                        if entity_item is not None:
                            is_disabled = entity_item.disabled

                        if entity.unique_id in to_delete:
                            to_delete.remove(entity.unique_id)

                        step = f"Mark as created - {domain} -> {entity_key}"
                        config_entry = self.config_manager.config_entry

                        entity_component = domain_component(
                            self.hass, config_entry.entry_id, entity
                        )

                        if entity_id is not None:
                            entity_component.entity_id = entity_id

                            state = self.hass.states.get(entity_id)

                            if state is None:
                                restored = True
                            else:
                                attributes = state.attributes
                                restored = attributes.get("restored", False)

                                if restored:
                                    name = entity.name
                                    msg = f"Restore {name} [{entity_id}]"

                                    _LOGGER.info(msg)

                            if restored:
                                if entity_item is None or not is_disabled:
                                    entities_to_add.append(entity_component)
                        else:
                            entities_to_add.append(entity_component)

                        entity.status = ENTITY_STATUS_READY

                        if entity_item is not None:
                            entity.disabled = is_disabled

                step = f"Add entities to {domain}"

                if len(entities_to_add) > 0:
                    async_add_entities(entities_to_add, True)

            if len(to_delete) > 0:
                _LOGGER.info(f"Following items will be deleted: {to_delete}")

                for domain in SIGNALS:
                    entities = dict(self.get_entities(domain))

                    for entity_key in entities:
                        entity = entities[entity_key]
                        if entity.unique_id in to_delete:
                            await self.ha.delete_entity(domain, entity.name)

        except Exception as ex:
            self.log_exception(ex, f"Failed to update, step: {step}")

    def get_water_last_reading_entity(self) -> EntityData:
        entity = None

        try:
            device_name = self.device_manager.get_system_device_name()
            data = self.api.data

            identity = f"{data.serial_number} Last Reading"
            entity_name = f"Water Meter {identity}"
            unique_id = f"{DOMAIN}-{DOMAIN_SENSOR}-{entity_name}"

            state = data.last_read

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            entity = EntityData()

            entity.id = identity
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.unit = VOLUME_CUBIC_METERS
            # VOLUME_LITERS
        except Exception as ex:
            self.log_exception(ex, "Failed to get water consumption entity")

        return entity

    def generate_water_last_reading_sensor(self):
        try:
            entity = self.get_water_last_reading_entity()
            entity_name = entity.name

            self.set_entity(DOMAIN_SENSOR, entity_name, entity)
        except Exception as ex:
            msg = "Failed to generate water consumption sensor"
            self.log_exception(ex, msg)

    def get_water_monthly_consumption_entity(self) -> EntityData:
        entity = None

        try:
            device_name = self.device_manager.get_system_device_name()
            data = self.api.data

            identity = f"{data.serial_number} Monthly Consumption"
            entity_name = f"Water Meter {identity}"
            unique_id = f"{DOMAIN}-{DOMAIN_SENSOR}-{entity_name}"

            state = data.monthly_consumption

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            entity = EntityData()

            entity.id = identity
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.unit = VOLUME_CUBIC_METERS
        except Exception as ex:
            self.log_exception(ex, "Failed to get water consumption entity")

        return entity

    def generate_water_monthly_consumption_sensor(self):
        try:
            entity = self.get_water_monthly_consumption_entity()
            entity_name = entity.name

            self.set_entity(DOMAIN_SENSOR, entity_name, entity)
        except Exception as ex:
            msg = "Failed to generate water consumption sensor"
            self.log_exception(ex, msg)

    def get_water_consumption_estimation_entity(self) -> EntityData:
        entity = None

        try:
            device_name = self.device_manager.get_system_device_name()
            data = self.api.data

            identity = f"{data.serial_number} Consumption Predication"
            entity_name = f"Water Meter {identity}"
            unique_id = f"{DOMAIN}-{DOMAIN_SENSOR}-{entity_name}"

            predication = data.consumption_predication
            current_monthly = data.monthly_consumption

            percentage = (current_monthly / predication) * 100
            state = f"{percentage:.2f}"

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                "Predication": f"{predication} {VOLUME_CUBIC_METERS}",
            }

            entity = EntityData()

            entity.id = identity
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.unit = "%"

        except Exception as ex:
            self.log_exception(ex, "Failed to get water consumption entity")

        return entity

    def generate_water_consumption_estimation_sensor(self):
        try:
            entity = self.get_water_consumption_estimation_entity()
            entity_name = entity.name

            self.set_entity(DOMAIN_SENSOR, entity_name, entity)
        except Exception as ex:
            msg = "Failed to generate water consumption sensor"
            self.log_exception(ex, msg)

    def get_water_daily_consumption_entity(
        self, scope: str, value: Optional[float]
    ) -> EntityData:
        entity = None

        try:
            device_name = self.device_manager.get_system_device_name()
            data = self.api.data

            identity = f"{data.serial_number} {scope}'s Consumption"
            entity_name = f"Water Meter {identity}"
            unique_id = f"{DOMAIN}-{DOMAIN_SENSOR}-{entity_name}"

            state = value

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            entity = EntityData()

            entity.id = identity
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.unit = VOLUME_CUBIC_METERS

        except Exception as ex:
            self.log_exception(ex, "Failed to get water consumption entity")

        return entity

    def generate_water_daily_consumption_sensor(
        self, scope: str, value: Optional[float]
    ):
        try:
            entity = self.get_water_daily_consumption_entity(scope, value)
            entity_name = entity.name

            self.set_entity(DOMAIN_SENSOR, entity_name, entity)
        except Exception as ex:
            msg = "Failed to generate water consumption sensor"
            self.log_exception(ex, msg)

    @staticmethod
    def log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")
