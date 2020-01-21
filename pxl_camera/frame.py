from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Frame:
    width: int = None
    height: int = None
    frame: Any = None
    timestamp: datetime = None

    fmt: str = '%F_%H-%M-%S-%f'

    def set_format(self, fmt: str):
        self.fmt = fmt

    def get_format(self):
        return self.fmt

    def get_timestamp(self) -> str:
        if self.timestamp is not None:
            return self.timestamp.strftime(self.fmt)

