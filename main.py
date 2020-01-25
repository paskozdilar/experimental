# import logging
# import time
#
# from pxl_camera.camera_manager import CameraManager
#
# logging.basicConfig(
#     level=logging.INFO,
#     format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
# )
#
#
# cm = CameraManager()
#
# while True:
#     print(cm.get_devices())
#     time.sleep(1)

import logging
import time

from pxl_camera.camera import Camera

# Set logging level
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
)


config = Camera.Config(
    device='/dev/video2',
    width=2*1920,
    height=2*1080,
)


while True:

    try:
        with Camera(config=config) as camera:
            while True:
                camera.get_frame()
    except RuntimeError as exc:
        logging.error(f'MAIN ERROR: {exc}')
        time.sleep(1)

