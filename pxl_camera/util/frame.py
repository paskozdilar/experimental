from dataclasses import dataclass
from datetime import datetime
from typing import Any

import cv2


@dataclass
class Frame:
    width: int = None
    height: int = None
    channels: int = None
    frame: Any = None
    timestamp: datetime = None
    state: Any = None

    fmt: str = '%F_%H-%M-%S-%f'

    def set_format(self, fmt: str):
        self.fmt = fmt

    def get_format(self):
        return self.fmt

    def get_timestamp(self) -> str:
        if self.timestamp is not None:
            return self.timestamp.strftime(self.fmt)

    def get_jpeg(self, quality=95):
        return cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, quality])[1].tostring()

    def get_state(self) -> str:
        return self.state.name

    def copy(self):
        return Frame(
            width=self.width,
            height=self.height,
            channels=self.channels,
            frame=cv2.UMat(self.frame.get().copy()),
            timestamp=self.timestamp,
        )
