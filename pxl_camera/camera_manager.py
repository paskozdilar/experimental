"""
    Class for high-level camera management of e-con systems See3CAM digital
    cameras.

    Manages multiple cameras by serial number.
"""
import dataclasses
import enum
from typing import Dict, Tuple

from pxl_actor.actor import Actor

from pxl_camera.camera import Camera
from pxl_camera.detect.device_detector import DeviceDetector


class CameraManager(Actor):

    # Single camera status
    class Status(str, enum.Enum):
        IDLE = 'IDLE'
        ACTIVE = 'ACTIVE'
        UNPLUGGED = 'UNPLUGGED'
        MALFUNCTIONED = 'MALFUNCTIONED'

    # Pure camera config
    @dataclasses.dataclass
    class Config:
        width: int
        height: int
        autofocus: bool
        focus: int
        filter: bool
        roi: Tuple[int, int, int, int]

    def _to_camera_config(self, serial: str, config: Config, device: str = None):
        if device is None:
            device = self.device_detector.get_dev_path(serial)

        if config is None:
            return None

        return Camera.Config(
            device=device,
            width=config.width,
            height=config.height,
            autofocus=config.autofocus,
            focus=config.focus,
            filter=config.filter,
        )

    def __init__(self):
        super(CameraManager, self).__init__()

        self.config: Dict[str, CameraManager.Config] = dict()
        self.camera: Dict[str, Camera] = dict()

        self.device_detector = DeviceDetector()
        self.device_detector.start(actor=self, method='handle_device_event')

    def handle_device_event(self, device: str, serial: str, action: str):
        """
            A hardware camera is connected to the computer if, and only if,
            the hardware camera's serial number is in 'self.camera'.
        """

        self.logger.info(f'Device event: {device} [{serial}] - {action}')

        if action == 'add':
            manager_config = self.config.get(serial, None)
            camera_config = self._to_camera_config(serial, manager_config, device)

            self.camera[serial] = Camera(camera_config)

        if action == 'remove':
            self.camera[serial].stop()
            self.camera[serial].kill()
            del self.camera[serial]

    #
    def get_config(self):
        return self.config

    def set_config(self, config: Dict[str, Config]) -> object:
        """
            Sets manager config values for each camera serial number.

        config = {
            [serial_1]: Config(...),
            [serial_2]: Config(...),
            ...
        }
        """

        # Load all specified camera configs
        for serial, manager_config in config.items():
            old_config = self.config.get(serial, None)
            new_config = self._to_camera_config(serial, manager_config)

            self.config[serial] = self._updated_config(old_config, new_config)

            if old_config == new_config or serial not in self.camera:
                continue

            if self._needs_restart(old_config, new_config):
                self.camera[serial].stop()
                self.camera[serial].start(self.config[serial])
            else:
                for key, value in dataclasses.asdict(new_config).items():
                    if value is None:
                        continue

                    if key == 'autofocus':
                        self.camera[serial].set_autofocus(value)
                    elif key == 'focus':
                        self.camera[serial].set_focus(value)
                    elif key == 'filter':
                        old_filter = self.camera[serial].get_filter()
                        new_filter = value

                        # Turn the filter off then on to reset it
                        # ...or do we need a more sophisticated mechanism?
                        # Maybe filter frame in message?
                        if new_filter and not old_filter:
                            self.camera[serial].reset_filter()

                        self.camera[serial].set_filter(value)

                    elif key == 'roi':
                        if isinstance(value, tuple) and \
                                len(value) == 4 and \
                                all(0.0 <= coord <= 1.0 for coord in value):
                            self.camera[serial].set_roi(value)
                        else:
                            self.logger.warning(f'Invalid roi [{serial}]: {value}')

        # Stop all unspecified cameras and remove all unspecified config
        for serial in self.config.keys() - config.keys():
            self.config.pop(serial)

            if serial in self.camera:
                self.camera[serial].stop()

    @staticmethod
    def _updated_config(old_config: Camera.Config, new_config: Camera.Config):
        """
            Updates old config with specified values from the new config.
        """
        if old_config is None:
            return Camera.Config(**dataclasses.asdict(new_config))

        updated_config = Camera.Config(**dataclasses.asdict(old_config))

        for key, value in dataclasses.asdict(new_config):
            if value is not None and value != getattr(old_config, key):
                setattr(updated_config, key, value)

        return updated_config

    @staticmethod
    def _needs_restart(old_config: Camera.Config, new_config: Camera.Config):
        """
            Checks whether a change in config requires Camera restart.
        """

        if old_config is None:
            return True

        return any([
            old_config.device != new_config.device,
            old_config.width != new_config.width,
            old_config.height != new_config.height,
        ])

    #
    def get_devices(self):
        """
            Returns list of serial numbers of connected cameras.
        """

        return list(self.device_detector.get_devices().keys())

    def get_status(self):
        """
            Returns status of all connected cameras.

            Camera plugged in, no config:   IDLE
            Camera plugged in, config:      ACTIVE
            Camera unplugged, config:       UNPLUGGED
            Camera unplugged, no config:    [ won't show up in status ]
        """

        return {
            serial: self._get_status(serial)
            for serial in set().union(
                self.camera.keys(),
                self.config.keys()
            )
        }

    def _get_status(self, serial: str) -> Status:
        """
            Returns camera status for single serial number.
        """

        return CameraManager.Status.UNPLUGGED \
            if serial not in self.camera \
            else CameraManager.Status.IDLE \
            if serial not in self.config \
            else CameraManager.Status.ACTIVE
            # if [camera is working]
            # else CameraManager.Status.MALFUNCTIONED

    #
    def get_frames(self, *args):
        """
            - get_frames() gets frames from all configured cameras.

            - get_frames(serial_1, serial_2, ..., serial_n) gets frames
              from all specified serials.
        """
        if args:
            serials = args
        else:
            serials = self.config.keys()

        frames = {}

        for serial in serials:
            try:
                frames[serial] = self.camera[serial].get_frame()\
                    if serial in self.camera else None
            except (RuntimeError, KeyError) as exc:
                self.logger.error(f'get_frames error: {exc}')
                frames[serial] = None

        return frames
