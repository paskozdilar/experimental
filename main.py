# import logging
# import time
#
# from pxl_camera.camera import Camera
#
#
# logging.basicConfig(
#     level=logging.INFO,
#     format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
# )
#
#
# camera = Camera()
# config = Camera.Config(
#     device='/dev/video0',
#     width=1920,
#     height=1080,
# )
#
# with camera(config):
#     frame = camera.get_frame()
#     print(frame.state)
#     camera.set_base_frame(frame)
#     time.sleep(1)
#     frame = camera.get_frame()
#     print(frame.state)
#     camera.set_base_frame(None)
#     time.sleep(1)
#     frame = camera.get_frame()
#     print(frame.state)
#

import logging
import time

from pxl_actor.actor import Actor

from pxl_camera.detect.device_detector import DeviceDetector

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s",
)


class PrintActor(Actor):

    def print(self, device, action):
        print(f'Device: {device}, action: {action}')


if __name__ == "__main__":
    pa = PrintActor()
    dd = DeviceDetector(actor=pa, method='print')

    while True:
        logging.info(dd.get_devices())
        time.sleep(3)
