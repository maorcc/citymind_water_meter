from __future__ import annotations

import json

from custom_components.citymind_water_meter.common.enums import EntityKeys


class AccountData:
    account_number: int | None
    first_name: str | None
    last_name: str | None
    municipal_id: str | None
    municipal_name: str | None
    municipal_phone: str | None
    municipal_email: str | None
    vacations: int | None
    alerts: int | None
    messages: int | None
    alert_settings: dict[EntityKeys, bool] | None

    def __init__(self):
        self.account_number = None
        self.first_name = None
        self.last_name = None
        self.municipal_id = None
        self.municipal_name = None
        self.municipal_phone = None
        self.municipal_email = None
        self.vacations = None
        self.alerts = None
        self.messages = None
        self.alert_settings = None

    @property
    def unique_name(self) -> str | None:
        parts = [self.first_name, self.last_name, self.account_number]

        relevant_parts = [str(part) for part in parts if part is not None]

        name = " ".join(relevant_parts)

        return name

    def to_dict(self):
        obj = {
            "account_number": self.account_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "municipal_id": self.municipal_id,
            "municipal_name": self.municipal_name,
            "municipal_phone": self.municipal_phone,
            "municipal_email": self.municipal_email,
            "vacations": self.vacations,
            "alerts": self.alerts,
            "messages": self.messages,
            "alert_settings": self.alert_settings,
        }

        return obj

    def __repr__(self):
        to_string = json.dumps(self.to_dict(), default=str)

        return to_string
