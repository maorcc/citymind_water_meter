"""Diagnostics support for Tuya."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .component.helpers.common import get_ha
from .component.helpers.const import (
    API_DATA_SECTION_METERS,
    API_DATA_SECTION_MY_ALERTS,
    API_DATA_SECTION_MY_MESSAGES,
    API_DATA_SECTION_SETTINGS,
    ENDPOINT_DATA_UPDATE_PER_METER,
    METER_COUNT,
    METER_SERIAL_NUMBER,
    STORAGE_DATA_METERS,
)
from .component.managers.home_assistant import CityMindHomeAssistantManager
from .configuration.helpers.const import DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Starting diagnostic tool")

    manager = get_ha(hass, entry.entry_id)

    return _async_get_diagnostics(hass, manager, entry)


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    manager = get_ha(hass, entry.entry_id)

    return _async_get_diagnostics(hass, manager, entry, device)


@callback
def _async_get_diagnostics(
    hass: HomeAssistant,
    manager: CityMindHomeAssistantManager,
    entry: ConfigEntry,
    device: DeviceEntry | None = None,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Getting diagnostic information")

    data = manager.config_data.to_dict()

    data[STORAGE_DATA_METERS] = manager.storage_api.data[STORAGE_DATA_METERS]

    if CONF_PASSWORD in data:
        data.pop(CONF_PASSWORD)

    data["disabled_by"] = entry.disabled_by
    data["disabled_polling"] = entry.pref_disable_polling

    meters = manager.api.data.get(API_DATA_SECTION_METERS, [])

    additional_details = [
        API_DATA_SECTION_MY_MESSAGES,
        API_DATA_SECTION_MY_ALERTS,
        API_DATA_SECTION_SETTINGS,
    ]

    consumptions = {}

    for consumption_key in ENDPOINT_DATA_UPDATE_PER_METER.keys():
        consumptions[consumption_key] = manager.api.data.get(consumption_key)

    for additional_details_key in additional_details:
        data[additional_details_key] = manager.api.data.get(additional_details_key)

    if CONF_PASSWORD in data:
        data.pop(CONF_PASSWORD)

    if device:
        device_name = next(iter(device.identifiers))[1]

        for meter in meters:
            meter_id = meter.get(METER_SERIAL_NUMBER)
            if manager.get_meter_name(meter_id) == device_name:
                _LOGGER.debug(f"Getting diagnostic information for meter #{meter_id}")

                data |= _async_device_as_dict(hass, meter, meter_id, consumptions)

                break
    else:
        _LOGGER.debug("Getting diagnostic information for all meters")

        data.update(
            meters=[
                _async_device_as_dict(
                    hass, meter, meter.get(METER_SERIAL_NUMBER), consumptions
                )
                for meter in meters
            ]
        )

    return data


@callback
def _async_device_as_dict(
    hass: HomeAssistant, data: dict, unique_id: str, consumptions: dict
) -> dict[str, Any]:
    """Represent a Shinobi monitor as a dictionary."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    ha_device = device_registry.async_get_device(
        identifiers={(DEFAULT_NAME, unique_id)}
    )

    meter_count = data.get(METER_COUNT)

    if meter_count is not None:
        meter_consumptions = {}

        for consumption_key in consumptions:
            consumption_data = consumptions[consumption_key]
            consumption_info = consumption_data.get(str(meter_count))

            meter_consumptions[
                consumption_key.replace("consumption-", "")
            ] = consumption_info

        data["consumptions"] = meter_consumptions

    if ha_device:
        data["home_assistant"] = {
            "name": ha_device.name,
            "name_by_user": ha_device.name_by_user,
            "disabled": ha_device.disabled,
            "disabled_by": ha_device.disabled_by,
            "entities": [],
        }

        ha_entities = er.async_entries_for_device(
            entity_registry,
            device_id=ha_device.id,
            include_disabled_entities=True,
        )

        for entity_entry in ha_entities:
            state = hass.states.get(entity_entry.entity_id)
            state_dict = None
            if state:
                state_dict = dict(state.as_dict())

                # The context doesn't provide useful information in this case.
                state_dict.pop("context", None)

            data["home_assistant"]["entities"].append(
                {
                    "disabled": entity_entry.disabled,
                    "disabled_by": entity_entry.disabled_by,
                    "entity_category": entity_entry.entity_category,
                    "device_class": entity_entry.device_class,
                    "original_device_class": entity_entry.original_device_class,
                    "icon": entity_entry.icon,
                    "original_icon": entity_entry.original_icon,
                    "unit_of_measurement": entity_entry.unit_of_measurement,
                    "state": state_dict,
                }
            )

    return data
