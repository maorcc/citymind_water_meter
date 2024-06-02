from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, ATTR_STATE, Platform
from homeassistant.core import HomeAssistant

from .common.base_entity import IntegrationBaseEntity, async_setup_base_entry
from .common.entity_descriptions import IntegrationSensorEntityDescription
from .common.enums import EntityType, ResetPolicy
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

        self._attr_state_class = entity_description.state_class
        self._attr_last_reset = self._get_last_reset()

    def _get_last_reset(self) -> datetime | None:
        last_reset: datetime | None = None
        reset_policy = self._entity_description.reset_policy

        if reset_policy != ResetPolicy.NONE:
            analytic_periods = self.coordinator.config_manager.analytic_periods

            if reset_policy == ResetPolicy.DAILY:
                last_reset = analytic_periods.today

            elif reset_policy == ResetPolicy.MONTHLY:
                last_reset = analytic_periods.first_date_of_month

        return last_reset

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
