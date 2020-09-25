from typing import Optional

from ..helpers.const import (CONF_LOG_LEVEL, CONF_NAME, CONF_PASSWORD,
                             CONF_USERNAME, DEFAULT_NAME, LOG_LEVEL_DEFAULT)


class ConfigData:
    name: str
    username: Optional[str]
    password: Optional[str]
    password_clear_text: Optional[str]
    log_level: str

    def __init__(self):
        self.name = DEFAULT_NAME
        self.username = None
        self.password = None
        self.password_clear_text = None
        self.log_level = LOG_LEVEL_DEFAULT

    @property
    def has_credentials(self):
        has_username = self.username and len(self.username) > 0

        has_password = False

        if self.password_clear_text is not None:
            has_password = len(self.password_clear_text) > 0

        has_credentials = has_username or has_password

        return has_credentials

    def __repr__(self):
        obj = {
            CONF_NAME: self.name,
            CONF_USERNAME: self.username,
            CONF_PASSWORD: self.password,
            CONF_LOG_LEVEL: self.log_level,
        }

        to_string = f"{obj}"

        return to_string
