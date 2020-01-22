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

    def __call__(self, config: Config):
        if not isinstance(config, RawCapture.Config):
            raise TypeError(f'config [{type(config)}] not instance of RawCapture.Config')
        else:
            self.set_config(config)
            return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.capture.release()
        self.config = RawCapture.Config()

    def _convert_to_rgb(self, raw_frame):
        return cv2.cvtColor(raw_frame, self._convert_code)

    def set_focus(self, focus):
        success = self.capture.set(cv2.CAP_PROP_FOCUS, focus)
        if success:
            self.config.focus = focus
        return success

    def get_focus(self):
        return self.config.focus

    def set_config(self, config: Config):
        """
            Opens device and sets config. Returns False on device open failure.

            Tries to avoid any unnecessary config changes.
        """
        print(__import__('threading').current_thread().name, 'set config - sanity check...', flush=True)
        if self.config.device is None and config.device is None:
            raise RuntimeError('Config device not set')

        print(__import__('threading').current_thread().name, 'set config - device...', flush=True)
        # Device
        if config.device != self.config.device or not self.open:
            success = self.capture.open(filename=config.device)  # , apiPreference=cv2.CAP_V4L2)  # This should be auto
            if success:
                self.config.device = config.device
                self.frame = cv2.UMat(self.get_frame())
                self.logger.info(f'Opening device {config.device} [{self.capture.getBackendName()}] success')
            else:
                self.config.device = None
                self.logger.error(f'Opening device {config.device} failure')
                return False

        print(__import__('threading').current_thread().name, 'set config - fourcc...', flush=True)
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

        print(__import__('threading').current_thread().name, 'set config - other...', flush=True)
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
                self.logger.debug(f'Loading value {key} from device: {value}')
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
            raise RuntimeError(f'Device {self.config.device} not opened')

        success, self.frame = self.capture.read(self.frame)

        if not success:
            self.capture.release()
            raise RuntimeError(f'Device {self.config.device} malfunctioned')

        return self.frame

    def on_exit(self):
        self.logger.info(f'Releasing device {self.config.device}...')
        self.capture.release()
