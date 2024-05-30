from enum import Enum, StrEnum


class AlertChannel(StrEnum):
    NONE = "0"
    SMS = "1"
    EMAIL = "3"
    ALL = "4"


class AlertType(Enum):
    DAILY_THRESHOLD = 12
    LEAK = 23
    CONSUMPTION_WHILE_AWAY = 1001


class EntityType(StrEnum):
    METER = "meter"
    ACCOUNT = "account"

    @staticmethod
    def from_string(text: str | None):
        value = EntityType.ACCOUNT

        all_options: list[str] = list(EntityType)

        for option in all_options:
            item = EntityType(option)
            is_match = item.value == text

            if is_match:
                value = item
                break

        return value


class EntityKeys(StrEnum):
    CONSUMPTION_FORECAST = "consumption_forecast"
    LAST_READ = "last_read"
    MONTHLY_CONSUMPTION = "monthly_consumption"
    TODAYS_CONSUMPTION = "todays_consumption"
    YESTERDAYS_CONSUMPTION = "yesterdays_consumption"
    HIGH_RATE_CONSUMPTION = "high_rate_consumption"
    LOW_RATE_CONSUMPTION = "low_rate_consumption"
    LOW_RATE_COST = "low_rate_cost"
    HIGH_RATE_COST = "high_rate_cost"
    SEWAGE_COST = "sewage_cost"
    LOW_RATE_CONSUMPTION_THRESHOLD = "low_rate_consumption_threshold"
    ALERTS = "alerts"
    ALERT_EXCEEDED_THRESHOLD = "alert_exceeded_threshold"
    ALERT_LEAK = "alert_leak"
    ALERT_LEAK_WHILE_AWAY = "alert_leak_while_away"
