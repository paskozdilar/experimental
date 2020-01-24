"""
    Class for high-level camera management of e-con systems See3CAM digital
    cameras.

    Manages multiple cameras by serial number and provides methods for
    filtering frames.
"""

from pxl_actor.actor import Actor

from pxl_camera.detect.device_detector import DeviceDetector


class CameraManager(Actor):

    def __init__(self):
        super(CameraManager, self).__init__()

        self.device_detector = DeviceDetector()
        self.device_detector.start(actor=self, method='handle_device_event')

        self.available_devices = self.device_detector.get_devices()
        self.running_devices = set()

    def handle_device_event(self, device: str, action: str):
        self.logger.debug(f'Handle device event: {device} {action}')

        serial = self.device_detector.get_serial(device)
        if serial is None:
            return

        if action == 'remove':
            try:
                self.available_devices.pop(serial)
            except KeyError as exc:
                self.logger.error(f'DEVICE DETECTOR ERROR: {exc}')

        if action == 'add':
            self.available_devices[serial] = device

    def status(self):
        return self.available_devices
