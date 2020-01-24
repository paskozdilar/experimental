import logging
import time

from pxl_camera.camera_manager import CameraManager

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
)


cm = CameraManager()

while True:
    print(cm.status())
    time.sleep(1)
