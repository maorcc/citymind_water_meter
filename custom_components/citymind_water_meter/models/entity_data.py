from ..helpers.const import (ENTITY_ATTRIBUTES, ENTITY_DEVICE_CLASS,
                             ENTITY_DEVICE_NAME, ENTITY_DISABLED, ENTITY_ICON,
                             ENTITY_ID, ENTITY_NAME, ENTITY_STATE,
                             ENTITY_STATUS, ENTITY_STATUS_CREATED,
                             ENTITY_UNIQUE_ID, ENTITY_UNIT)


class EntityData:
    id: str
    unique_id: str
    name: str
    state: bool
    attributes: dict
    icon: str
    device_name: str
    status: str
    device_class: str
    unit: str
    disabled: bool

    def __init__(self):
        self.id = ""
        self.unique_id = ""
        self.name = ""
        self.state = False
        self.attributes = {}
        self.icon = ""
        self.device_name = ""
        self.status = ENTITY_STATUS_CREATED
        self.device_class = ""
        self.unit = ""
        self.disabled = False

    def __repr__(self):
        obj = {
            ENTITY_ID: self.id,
            ENTITY_UNIQUE_ID: self.unique_id,
            ENTITY_NAME: self.name,
            ENTITY_STATE: self.state,
            ENTITY_ATTRIBUTES: self.attributes,
            ENTITY_ICON: self.icon,
            ENTITY_DEVICE_NAME: self.device_name,
            ENTITY_STATUS: self.status,
            ENTITY_DEVICE_CLASS: self.device_class,
            ENTITY_UNIT: self.unit,
            ENTITY_DISABLED: self.disabled,
        }

        to_string = f"{obj}"

        return to_string
