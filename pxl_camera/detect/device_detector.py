"""
    Class for detecting
"""

import fcntl
import os
import stat
import sys
import time

import pyudev

from pxl_actor.actor import Actor


def _get_device_attribute(device: pyudev.Device, attribute: str):
    """
        Finds first available attribute by traversing the udev capture tree
    """

    if attribute in device.attributes.available_attributes:
        return device.attributes.asstring(attribute)

    for parent_device in device.ancestors:
        if attribute in parent_device.attributes.available_attributes:
            return parent_device.attributes.asstring(attribute)

    return None


def _is_capture_device(device):

    """OPEN DEVICE"""
    try:
        # Check if character special (video4linux device nodes are supposed to be)
        device_stat = os.stat(device)
        if not stat.S_ISCHR(device_stat.st_mode):
            DeviceDetector.logger.debug(f'[{device}] is not character special')
            return False

        # Open device and save file descriptor
        fd = os.open(device, os.O_RDONLY)

        if fd == -1:
            DeviceDetector.logger.debug(f'[{device}] open error')
            return False

    except OSError as exc:
        DeviceDetector.logger.debug(f'[{device}] exception: {exc}')
        return False

    """CHECK IF VIDEO CAPTURE DEVICE"""
    try:
        # Manually converted from C headers - find a smarter way?
        cap = bytearray(104)
        capture_offset = 84
        capture_length = 4

        VIDIOC_QUERYCAP = -2140645888
        VIDIOC_G_FMT = 3234878980
        V4L2_CAP_VIDEO_CAPTURE = 1

        ret = fcntl.ioctl(fd, VIDIOC_QUERYCAP, cap)

        if ret == -1:
            DeviceDetector.logger.debug(f'[{device}] VIDIOC_QUERYCAP error')
            return False

        capabilities = int.from_bytes(
            bytes=cap[capture_offset:capture_length+capture_offset],
            byteorder=sys.byteorder,
            signed=False)

        if not bool(capabilities & V4L2_CAP_VIDEO_CAPTURE):
            DeviceDetector.logger.debug(f'[{device}] - not video capture device')
            return False

        """GET CAPTURE FORMAT"""
        # This part distinguishes capture devices from metadata capture devices.
        fmt = bytearray(208)
        type_offset = 0
        type_length = 4

        fmt[type_offset:type_offset+type_length] = V4L2_CAP_VIDEO_CAPTURE.to_bytes(
            type_length,
            byteorder=sys.byteorder,
            signed=False)

        ret = fcntl.ioctl(fd, VIDIOC_G_FMT, fmt)

        if ret == -1:
            DeviceDetector.logger.debug(f'[{device}] - VIDIOC_G_FMT error')
            return False

    except OSError as exc:
        DeviceDetector.logger.debug(f'[{device}] exception: {exc}')
        return False

    finally:
        """CLOSE DEVICE"""
        os.close(fd)

    DeviceDetector.logger.debug(f'[{device}] - valid capture device')
    return True


class DeviceDetector(Actor):

    _udev_context = pyudev.Context()
    _supported_cameras = {
        'e-con systems See3CAM_130',
        'e-con systems See3CAM_CU135',
    }

    def __init__(self, actor=None, method=None):
        """
        :param actor: Actor that will receive non-blocking method call on capture event.
        :param method: Method that will receive the event call with args 'device', 'action'
                       See DeviceDetector.event_handler().
        """
        super(DeviceDetector, self).__init__()

        self.actor = None
        self.method = None

        self.devices = {}
        self._devices_by_dev_path = {}

        # We use {source='kernel'} for udev events here because for some
        # reason udev won't forward events inside docker containers.
        # TODO: Investigate this.
        self.monitor = pyudev.Monitor.from_netlink(self._udev_context, source='kernel')
        self.monitor.filter_by(subsystem="video4linux")

        self.observer = pyudev.MonitorObserver(
            monitor=self.monitor,
            callback=self.event_handler,
        )
        self.observer.start()

        self._update_mapping()
        self.logger.info(f'Detected devices: {self.devices}')

        if isinstance(actor, Actor) and isinstance(method, str):
            self.start(actor, method)

    def __call__(self, actor: Actor, method: str):
        if not isinstance(actor, Actor):
            raise TypeError(f'actor [{type(actor)}] not instance of Actor')
        elif not isinstance(method, str):
            raise TypeError(f'method [{type(method)}] not instance of str')
        else:
            self.start(actor, method)
            return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, actor: Actor, method: str):
        self.actor = actor
        self.method = method

    def stop(self):
        self.actor = None
        self.method = None

    def event_handler(self, device):
        """
            MonitorObserver callback for handling device events.

            Updates the device mapping list and calls the method of the actor (passed
            through the constructor) with two arguments:
              - device: '/dev/path' of the capture
              - action: 'add' and 'remove' are relevant ones. Others can be ignored.
        """

        if device.action == 'remove' and device.device_node not in self.devices.values():
            return

        if device.action == 'add':
            # Wait for udev to handle the device
            time.sleep(0.5)

            if not _is_capture_device(device.device_node):
                return

        DeviceDetector.logger.info(f'Device event: {device.device_node} {device.action}')

        self._update_mapping()

        if isinstance(self.actor, Actor) and isinstance(self.method, str):
            Actor.ProxyMethod(
                actor=self.actor,
                method=self.method,
            )(device=device.device_node, action=device.action, no_wait=True)

    def _update_mapping(self):
        self.devices.clear()
        self._devices_by_dev_path.clear()

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

                self.devices[serial] = dev_path
                self._devices_by_dev_path[dev_path] = serial

            except Exception:
                continue

    def get_devices(self):
        """
            Returns mapping serial-to-capture-node for supported devices.
        """

        return self.devices

    def get_dev_path(self, serial):
        return self.devices.get(serial, None)

    def get_serial(self, dev_path):
        return self._devices_by_dev_path.get(dev_path, None)

