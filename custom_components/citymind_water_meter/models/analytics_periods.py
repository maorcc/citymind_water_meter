import calendar
from datetime import datetime, timedelta
import json

from custom_components.citymind_water_meter.common.consts import (
    FORMAT_DATE_ISO,
    FORMAT_DATE_YEAR_MONTH,
)


class AnalyticPeriodsData:
    today: datetime | None
    yesterday: datetime | None
    first_date_of_month: datetime | None
    last_date_of_month: datetime | None

    def __init__(self):
        self.today = datetime.now()
        self.yesterday = None
        self.first_date_of_month = None
        self.last_date_of_month = None

        self.update()

    @property
    def today_iso(self) -> str | None:
        return None if self.today is None else self.today.strftime(FORMAT_DATE_ISO)

    @property
    def yesterday_iso(self) -> str | None:
        return (
            None if self.yesterday is None else self.yesterday.strftime(FORMAT_DATE_ISO)
        )

    @property
    def current_month_iso(self) -> str | None:
        return (
            None
            if self.first_date_of_month is None
            else self.first_date_of_month.strftime(FORMAT_DATE_YEAR_MONTH)
        )

    @property
    def first_date_of_month_iso(self) -> str | None:
        return (
            None
            if self.first_date_of_month is None
            else self.first_date_of_month.strftime(FORMAT_DATE_ISO)
        )

    @property
    def last_date_of_month_iso(self) -> str | None:
        return (
            None
            if self.last_date_of_month is None
            else self.last_date_of_month.strftime(FORMAT_DATE_ISO)
        )

    def update(self, current_date: datetime | None = None):
        now = datetime.now() if current_date is None else current_date
        last_day_of_month = calendar.monthrange(now.year, now.month)[1]

        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.yesterday = self.today - timedelta(days=1)
        self.first_date_of_month = self.today.replace(day=1)
        self.last_date_of_month = self.today.replace(day=last_day_of_month)

    def to_dict(self):
        obj = {
            "today": self.today,
            "today_iso": self.today_iso,
            "yesterday": self.yesterday,
            "yesterday_iso": self.yesterday_iso,
            "first_date_of_month": self.first_date_of_month,
            "first_date_of_month_iso": self.first_date_of_month_iso,
            "last_date_of_month": self.last_date_of_month,
            "last_date_of_month_iso": self.last_date_of_month_iso,
            "current_month_iso": self.current_month_iso,
        }

        return obj

    def __repr__(self):
        to_string = json.dumps(self.to_dict(), default=str)

        return to_string
