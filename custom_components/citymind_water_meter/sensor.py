"""Platform for sensor integration."""
import logging

from .helpers.const import DOMAIN_SENSOR
from .models.base_entity import CityMindEntity, async_setup_base_entry
from .models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Binary Sensor."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, DOMAIN_SENSOR, CityMindSensor
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {DOMAIN_SENSOR}: {config_entry}")

    return True


class CityMindSensor(CityMindEntity):
    """Class for an BlueIris switch."""

    def __init__(self, hass, integration_name, entity: EntityData):
        super().__init__()

        super().initialize(hass, integration_name, entity, DOMAIN_SENSOR)
