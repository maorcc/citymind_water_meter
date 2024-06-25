from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.number import NumberEntityDescription, NumberMode
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import EntityCategory, Platform, UnitOfVolume
from homeassistant.helpers.entity import EntityDescription

from .consts import UNIT_COST
from .enums import EntityKeys, EntityType, ResetPolicy


@dataclass(frozen=True, kw_only=True)
class IntegrationEntityDescription(EntityDescription):
    platform: Platform | None = None
    entity_type: EntityType | None
    reset_policy: ResetPolicy = ResetPolicy.NONE


@dataclass(frozen=True, kw_only=True)
class IntegrationBinarySensorEntityDescription(
    BinarySensorEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.BINARY_SENSOR


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
class IntegrationSwitchEntityDescription(
    SwitchEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.SWITCH


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
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.LAST_READ,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.MONTHLY_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.TODAYS_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        reset_policy=ResetPolicy.DAILY,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.YESTERDAYS_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        reset_policy=ResetPolicy.DAILY,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.HIGH_RATE_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.LOW_RATE_CONSUMPTION,
        entity_type=EntityType.METER,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.LOW_RATE_TOTAL_COST,
        entity_type=EntityType.METER,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.LOW_RATE_COST,
        entity_type=EntityType.METER,
        mode=NumberMode.BOX,
        native_step=0.000001,
        native_min_value=0,
        native_max_value=30,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.HIGH_RATE_TOTAL_COST,
        entity_type=EntityType.METER,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.HIGH_RATE_COST,
        entity_type=EntityType.METER,
        mode=NumberMode.BOX,
        native_step=0.000001,
        native_min_value=0,
        native_max_value=30,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
    ),
    IntegrationSensorEntityDescription(
        key=EntityKeys.SEWAGE_TOTAL_COST,
        entity_type=EntityType.METER,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
        reset_policy=ResetPolicy.MONTHLY,
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.SEWAGE_COST,
        entity_type=EntityType.METER,
        mode=NumberMode.BOX,
        native_step=0.000001,
        native_min_value=0,
        native_max_value=30,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UNIT_COST,
        icon="mdi:currency-ils",
    ),
    IntegrationNumberEntityDescription(
        key=EntityKeys.LOW_RATE_CONSUMPTION_THRESHOLD,
        entity_type=EntityType.METER,
        mode=NumberMode.BOX,
        native_step=0.5,
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
    IntegrationSwitchEntityDescription(
        key=EntityKeys.ALERT_EXCEEDED_THRESHOLD_SMS,
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationSwitchEntityDescription(
        key=EntityKeys.ALERT_EXCEEDED_THRESHOLD_EMAIL,
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationSwitchEntityDescription(
        key=EntityKeys.ALERT_LEAK_SMS,
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationBinarySensorEntityDescription(
        key=EntityKeys.ALERT_LEAK_EMAIL,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationSwitchEntityDescription(
        key=EntityKeys.ALERT_LEAK_WHILE_AWAY_SMS,
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationSwitchEntityDescription(
        key=EntityKeys.ALERT_LEAK_WHILE_AWAY_EMAIL,
        entity_category=EntityCategory.CONFIG,
        entity_type=EntityType.ACCOUNT,
    ),
    IntegrationSwitchEntityDescription(
        key=EntityKeys.USE_UNIQUE_DEVICE_NAMES,
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
