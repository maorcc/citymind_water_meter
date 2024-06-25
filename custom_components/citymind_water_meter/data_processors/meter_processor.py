import logging
import sys

from homeassistant.helpers.device_registry import DeviceInfo

from ..common.consts import (
    API_DATA_SECTION_CONSUMPTION_DAILY,
    API_DATA_SECTION_CONSUMPTION_FORECAST,
    API_DATA_SECTION_CONSUMPTION_MONTHLY,
    API_DATA_SECTION_LAST_READ,
    API_DATA_SECTION_METERS,
    CONSUMPTION_DATA,
    CONSUMPTION_DATE,
    CONSUMPTION_FORECAST_ESTIMATED_CONSUMPTION,
    CONSUMPTION_METER_COUNT,
    CONSUMPTION_VALUE,
    DEFAULT_NAME,
    LAST_READ_METER_COUNT,
    LAST_READ_VALUE,
    METER_COUNT,
    METER_FULL_ADDRESS,
    METER_SERIAL_NUMBER,
)
from ..common.enums import EntityType
from ..managers.config_manager import ConfigManager
from ..models.meter_data import MeterData
from .base_processor import BaseProcessor

_LOGGER = logging.getLogger(__name__)


class MeterProcessor(BaseProcessor):
    _meters: dict[str, MeterData]
    _account_number: str | None = None

    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)

        self._meters = {}
        self._account_number = None

    @property
    def processor_type(self) -> EntityType | None:
        return EntityType.METER

    def get_meters(self) -> list[str]:
        return list(self._meters.keys())

    def get_all(self) -> list[dict]:
        items = [self._meters[item_key].to_dict() for item_key in self._meters]

        return items

    def get_meter(self, identifiers: set[tuple[str, str]]) -> dict | None:
        device: dict | None = None
        device_identifier = list(identifiers)[0][1]

        for meter_id in self._meters:
            unique_id = self._get_device_info_unique_id(meter_id)

            if unique_id == device_identifier:
                device = self._meters[meter_id].to_dict()

        return device

    def get_data(self, meter_id: str) -> MeterData:
        meter = self._meters.get(meter_id)

        return meter

    def get_device_info(self, identifier: str | None = None) -> DeviceInfo:
        device = self.get_data(identifier)

        if self._config_manager.use_unique_device_names:
            device_name = device.unique_name

        else:
            device_name = self._get_default_device_info_name(device.meter_serial_number)

        parent_device_id = self._get_account_name()
        unique_id = self._get_device_info_unique_id(device.meter_id)

        device_info = DeviceInfo(
            identifiers={(DEFAULT_NAME, unique_id)},
            name=device_name,
            model=str(self.processor_type).capitalize(),
            manufacturer=device.address,
            via_device=(DEFAULT_NAME, parent_device_id),
        )

        return device_info

    def _process_api_data(self):
        super()._process_api_data()

        try:
            meters = self._api_data.get(API_DATA_SECTION_METERS, [])
            last_read_section = self._api_data.get(API_DATA_SECTION_LAST_READ)
            daily_consumption_section = self._api_data.get(
                API_DATA_SECTION_CONSUMPTION_DAILY
            )
            monthly_consumption_section = self._api_data.get(
                API_DATA_SECTION_CONSUMPTION_MONTHLY
            )
            consumption_forecast_section = self._api_data.get(
                API_DATA_SECTION_CONSUMPTION_FORECAST
            )

            last_read_details = {
                str(last_read_item.get(LAST_READ_METER_COUNT)): last_read_item.get(
                    LAST_READ_VALUE
                )
                for last_read_item in last_read_section
            }

            for meter in meters:
                self._load_meter(
                    meter,
                    last_read_details,
                    daily_consumption_section,
                    monthly_consumption_section,
                    consumption_forecast_section,
                )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to extract meter data, Error: {ex}, Line: {line_number}"
            )

    def _load_meter(
        self,
        meter_details: dict,
        last_read_details: dict,
        daily_consumption_section: dict,
        monthly_consumption_section: dict,
        consumption_forecast_section: dict,
    ):
        meter_serial_number = meter_details.get(METER_SERIAL_NUMBER)
        meter_address = meter_details.get(METER_FULL_ADDRESS)
        meter_id = str(meter_details.get(METER_COUNT))

        last_read_value = last_read_details.get(meter_id, 0)
        last_read = self._format_number(last_read_value, 3)

        yesterday_consumption = self._get_consumption(
            daily_consumption_section, meter_id, self._yesterday_iso
        )
        today_consumption = self._get_consumption(
            daily_consumption_section, meter_id, self._today_iso
        )
        monthly_consumption = self._get_consumption(
            monthly_consumption_section, meter_id, self._current_month_iso
        )

        consumption_forecast_data = consumption_forecast_section.get(str(meter_id))

        estimated_value = consumption_forecast_data.get(
            CONSUMPTION_FORECAST_ESTIMATED_CONSUMPTION, 0
        )
        consumption_forecast = self._format_number(estimated_value, 3)

        meter = MeterData(meter_id)

        meter.meter_serial_number = meter_serial_number
        meter.address = meter_address
        meter.last_read = last_read
        meter.today_consumption = today_consumption
        meter.yesterday_consumption = yesterday_consumption
        meter.monthly_consumption = monthly_consumption
        meter.consumption_forecast = consumption_forecast

        meter.low_rate_consumption_threshold = (
            self._config_manager.get_low_rate_consumption_threshold(meter_id)
        )
        meter.low_rate_cost = self._config_manager.get_low_rate_cost(meter_id)
        meter.high_rate_cost = self._config_manager.get_high_rate_cost(meter_id)
        meter.sewage_cost = self._config_manager.get_sewage_cost(meter_id)

        self._meters[meter_id] = meter

    def _set_meter(
        self,
        meter_id: str,
    ):
        existing_device_data = self._meters.get(meter_id)

        if existing_device_data is None:
            meter_data = MeterData(meter_id)

        else:
            meter_data = existing_device_data

        self._meters[meter_data.unique_id] = meter_data

    def _get_meter(self, unique_id: str) -> MeterData | None:
        device = self._meters.get(unique_id)

        return device

    @staticmethod
    def _format_number(value: int | float | None, digits: int = 0) -> int | float:
        if value is None:
            value = 0

        value_str = f"{value:.{digits}f}"
        result = int(value_str) if digits == 0 else float(value_str)

        return result

    def _get_consumption(
        self, data: dict, meter_id: str, date_iso: str
    ) -> int | float | None:
        state = None

        try:
            if data is not None:
                consumption_info = data.get(meter_id)
                if isinstance(consumption_info, dict) and consumption_info.get(
                    CONSUMPTION_DATA
                ):
                    consumption_info = consumption_info.get(CONSUMPTION_DATA)
                for consumption_item in consumption_info:
                    if consumption_item is not None:
                        consumption_meter_count = consumption_item.get(
                            CONSUMPTION_METER_COUNT
                        )
                        consumption_date = consumption_item.get(CONSUMPTION_DATE)
                        consumption_value = consumption_item.get(CONSUMPTION_VALUE, 0)

                        is_meter_relevant = str(consumption_meter_count) == meter_id
                        is_date_relevant = consumption_date.startswith(date_iso)

                        if is_meter_relevant and is_date_relevant:
                            if consumption_value is not None:
                                consumption = float(consumption_value)

                                state = self._format_number(consumption, 3)

                            break

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load extract consumption ({date_iso}) details, "
                f"Meter {meter_id}, Error: {ex}, Line: {line_number}"
            )

        return state
