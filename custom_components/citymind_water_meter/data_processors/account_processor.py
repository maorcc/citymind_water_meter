import logging
import sys

from homeassistant.helpers.device_registry import DeviceInfo

from ..common.consts import (
    ALERT_MAPPING,
    API_DATA_SECTION_CUSTOMER_SERVICE,
    API_DATA_SECTION_MY_ALERTS,
    API_DATA_SECTION_MY_MESSAGES,
    API_DATA_SECTION_SETTINGS,
    ATTR_ALERT_TYPE,
    ATTR_MEDIA_TYPE,
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
from ..common.enums import AlertChannel, AlertType, EntityKeys, EntityType
from ..managers.config_manager import ConfigManager
from ..models.account_data import AccountData
from .base_processor import BaseProcessor

_LOGGER = logging.getLogger(__name__)


class AccountProcessor(BaseProcessor):
    _account: AccountData | None = None

    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)

        self._account = None

    @property
    def processor_type(self) -> EntityType | None:
        return EntityType.ACCOUNT

    def get(self) -> AccountData | None:
        return self._account

    def get_device_info(self, identifier: str | None = None) -> DeviceInfo:
        if self._config_manager.use_unique_device_names:
            device_name = self._account.unique_name

        else:
            device_name = self._get_account_name()

        municipal_name = self._account.municipal_name
        if municipal_name is None:
            municipal_name = PROVIDER

        device_info = DeviceInfo(
            identifiers={(DEFAULT_NAME, device_name)},
            name=device_name,
            model=str(self.processor_type).capitalize(),
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
            settings_section = self._api_data.get(API_DATA_SECTION_SETTINGS)

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

            account.alert_settings = self._get_alert_settings(settings_section)

            self._account = account

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to extract System data, Error: {ex}, Line: {line_number}"
            )

    @staticmethod
    def _get_alert_settings(settings_section: dict) -> dict[EntityKeys, bool]:
        alert_settings: dict[EntityKeys, bool] = {}
        for entity_type in ALERT_MAPPING:
            alert_mapping = ALERT_MAPPING[entity_type]

            alert_type: AlertType = alert_mapping.get(ATTR_ALERT_TYPE)
            media_type: AlertChannel = alert_mapping.get(ATTR_MEDIA_TYPE)

            alert_type_id = alert_type.value
            media_type_id = media_type.value

            relevant_config = [
                item
                for item in settings_section
                if item.get(SETTINGS_ALERT_TYPE_ID) == alert_type_id
                and item.get(SETTINGS_MEDIA_TYPE_ID) == media_type_id
            ]

            enabled = len(relevant_config) > 0

            _LOGGER.debug(
                f"Checking Alert: {alert_type}, Channel: {media_type}, Status: {enabled}"
            )

            alert_settings[entity_type] = enabled

        return alert_settings

    @staticmethod
    def _get_items_count(data: list | dict | None) -> int:
        count = 0 if data is None else len(data)

        return count
