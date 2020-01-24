"""
    Class for high-level camera management of e-con systems See3CAM digital
    cameras.

    Manages multiple cameras by serial number.
"""

from pxl_actor.actor import Actor

from pxl_camera.camera import Camera
from pxl_camera.detect.device_detector import DeviceDetector


class CameraManager(Actor):

    def __init__(self):
        super(CameraManager, self).__init__()

        self.device_detector = DeviceDetector()
        self.device_detector.start(actor=self, method='handle_device_event')

        self.configs = dict()
        self.cameras = dict()

    def handle_device_event(self, device: str, serial: str, action: str):

        self.logger.info(f'Device event: {device} [{serial}] - {action}')

        if action == 'remove':
            self.cameras[serial].stop()
            self.cameras[serial].kill()
            del self.cameras[serial]

        if action == 'add':
            self.cameras[serial] = Camera()

    #
    def get_config(self, serial: str):
        return self.configs.get(serial, None)

    def set_config(self, serial: str, config: dict):
        self.configs[serial] = config
        # TODO: Update state...

    #
    def get_devices(self):
        """
            Returns list of serial numbers of available cameras.
        """

        return list(self.cameras.keys())

    def get_status(self):
        """
            Returns status of all plugged in cameras
        """
        pass

    #
    def get_frames(self, serials):
        return {
            serial: self.cameras[serial].get_frame()
            for serial in serials
        }
