import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, ATTR_STATE, Platform
from homeassistant.core import HomeAssistant

from .common.base_entity import IntegrationBaseEntity, async_setup_base_entry
from .common.entity_descriptions import IntegrationSensorEntityDescription
from .common.enums import EntityType
from .managers.coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.SENSOR,
        IntegrationSensorEntity,
        async_add_entities,
    )


class IntegrationSensorEntity(IntegrationBaseEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entity_description: IntegrationSensorEntityDescription,
        coordinator: Coordinator,
        entity_type: EntityType,
        item_id: str | None,
    ):
        super().__init__(hass, entity_description, coordinator, entity_type, item_id)

        self._attr_device_class = entity_description.device_class
        self._attr_native_unit_of_measurement = (
            entity_description.native_unit_of_measurement
        )

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            state = data.get(ATTR_STATE)
            icon = data.get(ATTR_ICON)

            self._attr_native_value = state

            if icon is not None:
                self._attr_icon = icon

        else:
            self._attr_native_value = None
