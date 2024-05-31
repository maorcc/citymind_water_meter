from __future__ import annotations

import json


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
    alert_leak_data: str | None
    alert_exceeded_threshold: str | None
    alert_leak_while_away: str | None

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
        self.alert_leak = None
        self.alert_exceeded_threshold = None
        self.alert_leak_while_away = None

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
            "alert_leak": self.alert_leak,
            "alert_exceeded_threshold": self.alert_exceeded_threshold,
            "alert_leak_while_away": self.alert_leak_while_away,
        }

        return obj

    def __repr__(self):
        to_string = json.dumps(self, default=str)

        return to_string
