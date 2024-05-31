import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, Platform
from homeassistant.core import HomeAssistant

from .common.base_entity import IntegrationBaseEntity, async_setup_base_entry
from .common.consts import ATTR_IS_ON
from .common.entity_descriptions import IntegrationBinarySensorEntityDescription
from .common.enums import EntityType
from .managers.coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.BINARY_SENSOR,
        IntegrationBinarySensorEntity,
        async_add_entities,
    )


class IntegrationBinarySensorEntity(IntegrationBaseEntity, BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entity_description: IntegrationBinarySensorEntityDescription,
        coordinator: Coordinator,
        entity_type: EntityType,
        item_id: str | None,
    ):
        super().__init__(hass, entity_description, coordinator, entity_type, item_id)

        self._attr_device_class = entity_description.device_class

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            is_on = data.get(ATTR_IS_ON)
            icon = data.get(ATTR_ICON)

            self._attr_is_on = is_on

            if icon is not None:
                self._attr_icon = icon

        else:
            self._attr_is_on = None
