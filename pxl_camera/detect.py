import cv2
import pyudev

from pxl_actor.actor import Actor


def _get_device_attribute(device: pyudev.Device, attribute: str):
    """
        Finds first available attribute by traversing the udev device tree
    """

    if attribute in device.attributes.available_attributes:
        return device.attributes.asstring(attribute)

    for parent_device in device.ancestors:
        if attribute in parent_device.attributes.available_attributes:
            return parent_device.attributes.asstring(attribute)

    return None


def _is_capture_device(filename):

    capture = cv2.VideoCapture(filename)
    success = capture.isOpened()
    capture.release()

    return success


class Detect(Actor):

    _udev_context = pyudev.Context()
    _supported_cameras = {
        'e-con systems See3CAM_130',
        'e-con systems See3CAM_CU135',
    }

    def __init__(self, actor=None, method=None):
        """
        :param actor: Actor that will receive non-blocking method call on device event.
        :param method: Method that will receive the event call.
        """
        super(Detect, self).__init__()

        if actor is not None:
            self.actor = actor
            self.method = method

            self.monitor = pyudev.Monitor.from_netlink(self._udev_context, source='kernel')
            self.monitor.filter_by(subsystem="video4linux")

            self.observer = pyudev.MonitorObserver(
                monitor=self.monitor,
                callback=self.callback,
            )
            self.observer.start()

    def callback(self, device):
        """
            MonitorObserver callback for handling device events.

            Calls the method of the actor (passed through the constructor) with two arguments:
              - device: '/dev/path' of the device
              - action:
        """
        Actor.ProxyMethod(
            actor=self.actor,
            method=self.method,
        )(device=device.device_node, action=device.action, no_wait=True)

    def get_devices(self):
        """
            Returns mapping serial-to-device-node for supported devices.
        """

        devices = {}

        for device in self._udev_context.list_devices(subsystem='video4linux'):

            # noinspection PyBroadException
            try:
                name, manufacturer, product, serial = \
                    _get_device_attribute(device, 'name'), \
                    _get_device_attribute(device, 'manufacturer'), \
                    _get_device_attribute(device, 'product'), \
                    _get_device_attribute(device, 'serial')

                dev_path = device.device_node

                if f'{manufacturer} {product}' not in self._supported_cameras:
                    continue

                if not _is_capture_device(dev_path):
                    continue

                devices[serial] = dev_path

            except Exception:
                continue

        return devices

    def get_dev_path(self, serial):
        return self.get_devices().get(serial, None)

    def get_serial(self, dev_path):
        devices_by_path = {_dev_path: _serial for _serial, _dev_path in self.get_devices().items()}

        return devices_by_path.get(dev_path, None)

