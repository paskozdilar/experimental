"""
    Class for high-level camera management.

    Manages multiple cameras by serial number and provides methods for
    filtering frames.
"""

from pxl_actor.actor import Actor

from pxl_camera.detect.device_detector import DeviceDetector


class CameraManager(Actor):

    def __init__(self):
        super(CameraManager, self).__init__()

        self.device_detector = DeviceDetector(actor=self, method='device_event')
        self.device_mapping = self.device_detector.get_devices()

    def handle_device_event(self, device: str, action: str):
        ...
        # self.device_mapping
