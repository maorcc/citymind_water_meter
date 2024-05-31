from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.number import NumberEntityDescription, NumberMode
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, Platform, UnitOfVolume
from homeassistant.helpers.entity import EntityDescription

from .consts import ALERT_OPTIONS, UNIT_COST
from .enums import EntityKeys, EntityType


@dataclass(frozen=True, kw_only=True)
class IntegrationEntityDescription(EntityDescription):
    platform: Platform | None = None
    entity_type: EntityType | None


@dataclass(frozen=True, kw_only=True)
class IntegrationBinarySensorEntityDescription(
    BinarySensorEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.BINARY_SENSOR
    on_value: str | bool | None = None
    attributes: list[str] | None = None


@dataclass(frozen=True, kw_only=True)
class IntegrationSensorEntityDescription(
    SensorEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.SENSOR


@dataclass(frozen=True, kw_only=True)
class IntegrationSelectEntityDescription(
    SelectEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.SELECT


@dataclass(frozen=True, kw_only=True)
class IntegrationNumberEntityDescription(
    NumberEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.NUMBER


ENTITY_DESCRIPTIONS: list[IntegrationEntityDescription] = [
    IntegrationSensorEntityDescription(
        key=EntityKeys.CONSUMPTION_FORECAST,
        entity_type=EntityType.METER,
        icon="mdi:meter-gas",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.LAST_READ,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.MONTHLY_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.TODAYS_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.YESTERDAYS_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.HIGH_RATE_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.LOW_RATE_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.LOW_RATE_COST,
        entity_type=EntityType.METER,
        native_min_value=0,
        native_max_value=50,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.HIGH_RATE_COST,
        entity_type=EntityType.METER,
        native_min_value=0,
        native_max_value=50,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.SEWAGE_COST,
        entity_type=EntityType.METER,
        native_min_value=0,
        native_max_value=50,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.LOW_RATE_CONSUMPTION_THRESHOLD,
        entity_type=EntityType.METER,
        native_min_value=0,
        native_max_value=100,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        icon="mdi:cup-water",
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.ALERTS,
        entity_type=EntityType.ACCOUNT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntegrationSelectEntityDescription(
        key=EntityKeys.ALERT_EXCEEDED_THRESHOLD,
        options=ALERT_OPTIONS.get(EntityKeys.ALERT_EXCEEDED_THRESHOLD),
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationSelectEntityDescription(
        key=EntityKeys.ALERT_LEAK,
        options=ALERT_OPTIONS.get(EntityKeys.ALERT_LEAK),
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationSelectEntityDescription(
        key=EntityKeys.ALERT_LEAK_WHILE_AWAY,
        options=ALERT_OPTIONS.get(EntityKeys.ALERT_LEAK_WHILE_AWAY),
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
]


def get_entity_descriptions(
    platform: Platform, entity_type: EntityType
) -> list[IntegrationEntityDescription]:
    result = [
        entity_description
        for entity_description in ENTITY_DESCRIPTIONS
        if entity_description.platform == platform
        and entity_description.entity_type == entity_type
    ]

    return result


def get_platforms() -> list[str]:
    platforms = {
        entity_description.platform: None for entity_description in ENTITY_DESCRIPTIONS
    }
    result = list(platforms.keys())

    return result


PLATFORMS = get_platforms()
