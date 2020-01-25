"""
    Class for high-level camera management of e-con systems See3CAM digital
    cameras.

    Manages multiple cameras by serial number.
"""
import dataclasses
import enum
from typing import Dict

from pxl_actor.actor import Actor

from pxl_camera.camera import Camera
from pxl_camera.detect.device_detector import DeviceDetector


class CameraManager(Actor):

    @dataclasses.dataclass
    class Config:
        width: int
        height: int
        autofocus: bool
        focus: int
        filter: bool

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

        self.device_detector = DeviceDetector()
        self.device_detector.start(actor=self, method='handle_device_event')

        self.config: Dict[str, CameraManager.Config] = dict()
        self.camera: Dict[str, Camera] = dict()

    def handle_device_event(self, device: str, serial: str, action: str):

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

    def set_config(self, config: Dict[str, Config]):
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

            if old_config == new_config:
                continue

            if serial in self.camera and self._needs_restart(old_config, new_config):
                self.camera[serial].stop()
                self.camera[serial].start(new_config)

        # Stop all unspecified cameras and remove all unspecified config
        for serial in self.config.keys() - config.keys():
            self.config.pop(serial)

            if serial in self.camera:
                self.camera[serial].stop()

        # Save config
        self.config = config

    @staticmethod
    def _needs_restart(old_config: Camera.Config, new_config: Camera.Config):
        """
            Checks whether a change in config requires Camera restart.
        """

        if old_config is None:
            return False

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
        """
        pass

    #
    def get_frames(self, serials):
        return {
            serial: self.cameras[serial].get_frame()
            for serial in serials
        }
