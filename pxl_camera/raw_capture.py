"""
    Capture/config setting actor for a single camera.

    Captures frame in raw format (usually UYVY or YUYV).
    Use frame muxer for decoding or roll your own.
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

    def get_focus(self):
        return self.capture.get(cv2.CAP_PROP_FOCUS)

    def set_config(self, config: Config):
        """
            Opens device and sets config. Returns False on device open failure.

            Tries to avoid any unnecessary config changes.
        """
        if self.config.device is None and config.device is None:
            raise RuntimeError('Config device not set')

        # Device
        if config.device != self.config.device or not self.open:
            success = self.capture.open(filename=config.device)  #, apiPreference=cv2.CAP_V4L2)  # This should be auto
            if success:
                self.config.device = config.device
                self.frame = cv2.UMat(self.get_frame())
                self.logger.debug(f'Opening camera {config.device} [{self.capture.getBackendName()}] success')
            else:
                self.config.device = None
                self.logger.debug(f'Opening camera {config.device} failure')
                return False

        # Fourcc
        if config.fourcc is None:
            self.config.fourcc = RawCapture.config.decode_fourcc(self.capture.get(cv2.CAP_PROP_FOURCC))
        else:
            success = self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*config.fourcc))
            if success:
                self.config.fourcc = config.fourcc
            else:
                self.config.fourcc = RawCapture.Config.decode_fourcc(self.capture.get(cv2.CAP_PROP_FOURCC))
            self.logger.debug(f'Setting fourcc to {config.fourcc}: {"success" if success else "failure"}')

        # Other config
        skip_keys = {'device', 'fourcc'}

        for key, value in dataclasses.asdict(config).items():
            if key in skip_keys:
                continue

            cv2_attribute = getattr(cv2, f'CAP_PROP_{key.upper()}', None)

            if cv2_attribute is None:
                self.logger.debug(f'Invalid attribute [{key}] for device [{self.config.device}]')
                continue

            if value is None:
                # If value is unset, read it from device
                value = self.capture.get(cv2_attribute)
                setattr(self.config, key, value)
                continue

            success = self.capture.set(cv2_attribute, value)
            if success:
                setattr(self.config, key, value)
            else:
                setattr(self.config, key, self.capture.get(cv2_attribute))

            self.logger.debug(f'Setting {key} to {value}: {"success" if success else "failure"}')

        return True

    def get_frame(self):
        """
            Retrieves and returns the next frame from device, if available.
            Returns None on error.
        """
        if not self.config.device:
            return None

        success, self.frame = self.capture.read(self.frame)

        if not success:
            self.capture.release()
            return None

        return self.frame
