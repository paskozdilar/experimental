"""
    Capture/config setting actor for a single camera.

    Create a Capture object
"""

import dataclasses
import logging

import cv2

from pxl_actor.actor import Actor


class RawCapture(Actor):

    # CONFIG
    @dataclasses.dataclass
    class Config:
        device: str = None
        fourcc: str = None
        frame_width: int = None
        frame_height: int = None
        fps: int = None
        convert_rgb: bool = False
        autofocus: bool = None
        focus: int = None

        @staticmethod
        def decode_fourcc(fourcc):
            return "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)]) if fourcc is not None else None

    logger = logging.getLogger('camera')

    def __init__(self):
        super().__init__()

        self._convert_code = None

        self.open = False
        self.config = RawCapture.Config()
        self.capture = cv2.VideoCapture()
        self.frame = None

    def _convert_to_rgb(self, raw_frame):
        return cv2.cvtColor(raw_frame, self._convert_code)

    def set_focus(self, focus):
        return self.capture.set(cv2.CAP_PROP_FOCUS, focus)

    def set_config(self, config: Config):
        """
            Opens device and sets config.

            Tries to avoid any unnecessary config changes.
        """

        # Device
        if config.device != self.config.device or not self.open:
            success = self.capture.open(filename=config.device)  #, apiPreference=cv2.CAP_V4L2)  # This should be auto
            if success:
                self.open = True
                self.frame = self.get_frame()
                self.logger.debug(f'Opening camera {config.device} with backend {self.capture.getBackendName()}')
            else:
                self.open = False
                return False

        # Fourcc
        if config.fourcc is not None:
            success = self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*config.fourcc))
            self.logger.debug(f'Setting fourcc to {config.fourcc}: {"success" if success else "failure"}')

        # Other config
        for key, value in dataclasses.asdict(config).items():
            cv2_attribute = getattr(cv2, f'CAP_PROP_{key.upper()}', None)

            if value is None or cv2_attribute is None or key == 'fourcc':
                continue

            success = self.capture.set(cv2_attribute, value)

            self.logger.debug(f'Setting config {key} to {value}: {"success" if success else "failure"}')

    def get_frame(self):
        """
            Retrieves and returns the next frame from device, if available.
            Returns None on error.
        """
        if not self.open:
            return None

        success, self.frame = self.capture.read(self.frame)

        if not success:
            self.capture.release()
            return None

        return self.frame
