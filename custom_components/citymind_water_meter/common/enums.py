from enum import Enum, StrEnum


class AlertChannel(Enum):
    EMAIL = 1
    SMS = 3


class AlertType(Enum):
    DAILY_THRESHOLD = 12
    LEAK = 23
    CONSUMPTION_WHILE_AWAY = 1001


class EntityType(StrEnum):
    METER = "Water Meter"
    ACCOUNT = "Account"


class ResetPolicy(Enum):
    NONE = 0
    DAILY = 1
    MONTHLY = 2


class EntityKeys(StrEnum):
    CONSUMPTION_FORECAST = "consumption_forecast"
    LAST_READ = "last_read"
    MONTHLY_CONSUMPTION = "monthly_consumption"
    TODAYS_CONSUMPTION = "todays_consumption"
    YESTERDAYS_CONSUMPTION = "yesterdays_consumption"
    HIGH_RATE_CONSUMPTION = "high_rate_consumption"
    LOW_RATE_CONSUMPTION = "low_rate_consumption"
    LOW_RATE_TOTAL_COST = "low_rate_total_cost"
    LOW_RATE_COST = "low_rate_cost"
    HIGH_RATE_TOTAL_COST = "high_rate_total_cost"
    HIGH_RATE_COST = "high_rate_cost"
    SEWAGE_COST = "sewage_cost"
    SEWAGE_TOTAL_COST = "sewage_total_cost"
    LOW_RATE_CONSUMPTION_THRESHOLD = "low_rate_consumption_threshold"
    ALERTS = "alerts"
    ALERT_LEAK_WHILE_AWAY_SMS = "alert_leak_while_away_sms"
    ALERT_LEAK_WHILE_AWAY_EMAIL = "alert_leak_while_away_email"
    ALERT_LEAK_SMS = "alert_leak_sms"
    ALERT_LEAK_EMAIL = "alert_leak_email"
    ALERT_EXCEEDED_THRESHOLD_SMS = "alert_exceeded_threshold_sms"
    ALERT_EXCEEDED_THRESHOLD_EMAIL = "alert_exceeded_threshold_email"
    USE_UNIQUE_DEVICE_NAMES = "use_unique_device_name"
