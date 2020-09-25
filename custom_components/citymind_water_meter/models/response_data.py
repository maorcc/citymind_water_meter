from typing import Optional


class ResponseData:
    data: Optional[str]
    url: Optional[str]
    status: Optional[str]
    reason: Optional[str]

    def __init__(self):
        self.data = None
        self.url = None
        self.status = None
        self.reason = None

    def to_dict(self):
        obj = {
            "data": self.data,
            "url": self.url,
            "status": self.status,
            "reason": self.reason,
        }

        return obj

    def __repr__(self):
        to_string = f"{self.to_dict()}"

        return to_string
