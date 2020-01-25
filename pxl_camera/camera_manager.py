"""
    Class for high-level camera management of e-con systems See3CAM digital
    cameras.

    Manages multiple cameras by serial number.
"""

import enum
from typing import Dict

from pxl_actor.actor import Actor

from pxl_camera.camera import Camera
from pxl_camera.detect.device_detector import DeviceDetector


class CameraManager(Actor):

    def __init__(self):
        super(CameraManager, self).__init__()

        self.device_detector = DeviceDetector()
        self.device_detector.start(actor=self, method='handle_device_event')

        self.config = dict()
        self.camera = dict()

    def handle_device_event(self, device: str, serial: str, action: str):

        self.logger.info(f'Device event: {device} [{serial}] - {action}')

        # if action == 'remove':
        #     self.cameras[serial].stop()
        #     self.cameras[serial].kill()
        #     del self.cameras[serial]
        #
        # if action == 'add':
        #     self.cameras[serial] = Camera()

    #
    def get_config(self):
        return self.config

    def set_config(self, config: Dict[str, Camera.Config]):
        """
            Updates config with given values.

        config = {
            [serial_1]: Camera.Config(...),
            [serial_2]: Camera.Config(...),
            ...
        }
        """

        for serial, camera_config in config.items():

            # Stop already started Camera
            if serial in self.camera:
                self.camera[serial].stop()
            else:
                self.camera[serial] = Camera()

            # Start new one
            self.camera[serial].start(camera_config)

        # Save config
        self.config = config

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
