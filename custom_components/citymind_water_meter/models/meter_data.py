from __future__ import annotations

import json


class MeterData:
    meter_id: str
    address: str | None = None
    meter_serial_number: str | None = None
    last_read: float | None = None
    today_consumption: float | None = None
    yesterday_consumption: float | None = None
    monthly_consumption: float | None = None
    consumption_forecast: float | None = None
    low_rate_consumption_threshold: float | None = None
    low_rate_cost: float | None = None
    high_rate_cost: float | None = None
    sewage_cost: float | None = None

    def __init__(self, meter_id: str):
        self.meter_id = meter_id
        self.meter_serial_number = None
        self.address = None
        self.last_read = None
        self.today_consumption = None
        self.yesterday_consumption = None
        self.monthly_consumption = None
        self.consumption_forecast = None
        self.low_rate_consumption_threshold = None
        self.low_rate_cost = None
        self.high_rate_cost = None
        self.sewage_cost = None

    @property
    def unique_id(self) -> str:
        return self.meter_id

    @property
    def unique_name(self) -> str | None:
        parts = [self.address, self.meter_serial_number]

        relevant_parts = [str(part) for part in parts if part is not None]

        name = " ".join(relevant_parts)

        return name

    @property
    def high_rate_monthly_consumption(self) -> float:
        value = 0

        if self.monthly_consumption > self.low_rate_consumption_threshold:
            value = self.monthly_consumption - self.low_rate_consumption_threshold

        return value

    @property
    def low_rate_monthly_consumption(self) -> float:
        value = self.monthly_consumption

        if self.monthly_consumption > self.low_rate_consumption_threshold:
            value = self.low_rate_consumption_threshold

        return value

    def to_dict(self):
        obj = {
            "meter_id": self.meter_id,
            "meter_serial_number": self.meter_serial_number,
            "address": self.address,
            "last_read": self.last_read,
            "today_consumption": self.today_consumption,
            "yesterday_consumption": self.yesterday_consumption,
            "monthly_consumption": self.monthly_consumption,
            "consumption_forecast": self.consumption_forecast,
            "low_rate_consumption_threshold": self.low_rate_consumption_threshold,
            "low_rate_cost": self.low_rate_cost,
            "high_rate_cost": self.high_rate_cost,
            "sewage_cost": self.sewage_cost,
        }

        return obj

    def __repr__(self):
        to_string = json.dumps(self.to_dict(), default=str)

        return to_string
