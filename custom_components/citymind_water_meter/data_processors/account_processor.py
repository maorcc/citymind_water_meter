import logging
import sys

from homeassistant.helpers.device_registry import DeviceInfo

from ..common.consts import (
    API_DATA_SECTION_CUSTOMER_SERVICE,
    API_DATA_SECTION_MY_ALERTS,
    API_DATA_SECTION_MY_MESSAGES,
    API_DATA_SECTION_SETTINGS,
    CITY_MIND_WEBSITE,
    CUSTOMER_SERVICE_DESCRIPTION,
    CUSTOMER_SERVICE_EMAIL,
    CUSTOMER_SERVICE_PHONE_MUNICIPAL_ID,
    CUSTOMER_SERVICE_PHONE_NUMBER,
    DEFAULT_NAME,
    PROVIDER,
    SETTINGS_ALERT_TYPE_ID,
    SETTINGS_MEDIA_TYPE_ID,
)
from ..common.enums import AlertChannel, AlertType, EntityType
from ..managers.config_manager import ConfigManager
from ..models.account_data import AccountData
from .base_processor import BaseProcessor

_LOGGER = logging.getLogger(__name__)


class AccountProcessor(BaseProcessor):
    _account: AccountData | None = None

    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)

        self.processor_type = EntityType.ACCOUNT

        self._account = None

    def get(self) -> AccountData | None:
        return self._account

    def _get_device_info_name(self, meter_id: str | None = None):
        name = self._get_account_name()

        return name

    def get_device_info(self, meter_id: str | None = None) -> DeviceInfo:
        name = self._get_device_info_name()

        municipal_name = self._account.municipal_name
        if municipal_name is None:
            municipal_name = PROVIDER

        device_info = DeviceInfo(
            identifiers={(DEFAULT_NAME, name)},
            name=name,
            model=self.processor_type,
            manufacturer=municipal_name,
            configuration_url=CITY_MIND_WEBSITE,
        )

        return device_info

    def _process_api_data(self):
        super()._process_api_data()

        try:
            account = AccountData()

            customer_service_section = self._api_data.get(
                API_DATA_SECTION_CUSTOMER_SERVICE
            )
            vacations_data = self._api_data.get(API_DATA_SECTION_MY_MESSAGES)
            alerts_data = self._api_data.get(API_DATA_SECTION_MY_ALERTS)
            messages_data = self._api_data.get(API_DATA_SECTION_MY_MESSAGES)
            settings = self._api_data.get(API_DATA_SECTION_SETTINGS)

            account.account_number = self._account_number
            account.first_name = self._first_name
            account.last_name = self._last_name

            account.municipal_id = customer_service_section.get(
                CUSTOMER_SERVICE_PHONE_MUNICIPAL_ID
            )
            account.municipal_name = customer_service_section.get(
                CUSTOMER_SERVICE_DESCRIPTION
            )
            account.municipal_phone = customer_service_section.get(
                CUSTOMER_SERVICE_PHONE_NUMBER
            )
            account.municipal_email = customer_service_section.get(
                CUSTOMER_SERVICE_EMAIL
            )
            account.vacations = self._get_items_count(vacations_data)
            account.alerts = self._get_items_count(alerts_data)
            account.messages = self._get_items_count(messages_data)
            account.alert_leak = self._get_alert_state(settings, AlertType.LEAK)
            account.alert_exceeded_threshold = self._get_alert_state(
                settings, AlertType.DAILY_THRESHOLD
            )
            account.alert_leak_while_away = self._get_alert_state(
                settings, AlertType.CONSUMPTION_WHILE_AWAY
            )

            self._account = account

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to extract System data, Error: {ex}, Line: {line_number}"
            )

    @staticmethod
    def _get_items_count(data: list | dict | None) -> int:
        count = 0 if data is None else len(data)

        return count

    @staticmethod
    def _get_alert_state(settings: dict, alert_type: AlertType):
        is_leak_alert = alert_type == AlertType.LEAK

        value = int(AlertChannel.EMAIL) if is_leak_alert else 0

        for item in settings:
            alert_type_id = item.get(SETTINGS_ALERT_TYPE_ID)
            current_media_type_id = item.get(SETTINGS_MEDIA_TYPE_ID, 0)

            skip = is_leak_alert and current_media_type_id == int(AlertChannel.EMAIL)

            if alert_type_id == alert_type and not skip:
                value += current_media_type_id

        state = str(value)

        return state
