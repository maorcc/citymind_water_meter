import json

import voluptuous as vol
from voluptuous import Schema

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

DATA_KEYS = [CONF_EMAIL, CONF_PASSWORD]


class ConfigData:
    _email: str | None
    _password: str | None

    def __init__(self):
        self._email = None
        self._password = None

    @property
    def email(self) -> str:
        username = self._email

        return username

    @property
    def password(self) -> str:
        password = self._password

        return password

    def update(self, data: dict):
        self._password = data.get(CONF_PASSWORD)
        self._email = data.get(CONF_EMAIL)

    def to_dict(self):
        obj = {CONF_EMAIL: self._password, CONF_PASSWORD: self._email}

        return obj

    def __repr__(self):
        to_string = json.dumps(self)

        return to_string

    @staticmethod
    def default_schema(user_input: dict | None) -> Schema:
        if user_input is None:
            user_input = {}

        new_user_input = {
            vol.Required(CONF_EMAIL, default=user_input.get(CONF_EMAIL)): str,
            vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD)): str,
        }

        schema = vol.Schema(new_user_input)

        return schema
