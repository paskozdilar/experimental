import dataclasses
import datetime

import cv2


@dataclasses.dataclass
class Frame:
    frame: cv2.UMat = None
    timestamp: datetime.datetime = None

    fmt: str = '%F_%H-%M-%S-%f'

    def set_format(self, fmt: str):
        self.fmt = fmt

    def get_format(self):
        return self.fmt

    def get_timestamp(self) -> str:
        if self.timestamp is not None:
            return self.timestamp.strftime(self.fmt)

