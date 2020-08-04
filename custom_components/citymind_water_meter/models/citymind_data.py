from typing import Optional


class CityMindData:
    property: Optional[dict]
    consumer: Optional[str]
    provider: Optional[str]
    serial_number: Optional[str]
    last_read: Optional[float]
    consumption: Optional[float]
    monthly_consumption: Optional[float]
    consumption_estimation: Optional[float]

    def __init__(self):
        self.property = None
        self.consumer = None
        self.status = None
        self.serial_number = None
        self.last_read = None
        self.consumption = None
        self.monthly_consumption = None
        self.consumption_predication = None

    def to_dict(self):
        obj = {
            "property": self.property,
            "consumer": self.consumer,
            "provider": self.provider,
            "serial_number": self.serial_number,
            "last_read": self.last_read,
            "consumption": self.consumption,
            "monthly_consumption": self.monthly_consumption,
            "consumption_predication": self.consumption_predication,
        }

        return obj

    def __repr__(self):
        to_string = f"{self.to_dict()}"

        return to_string
