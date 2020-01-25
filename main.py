import logging
import time

from pxl_camera.camera_manager import CameraManager

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
)


cm = CameraManager()
cm.set_config({
    '38185000': CameraManager.Config(
        width=1920,
        height=1080,
        autofocus=False,
        focus=90,
        filter=True,
    ),
    'ASDFQWER': CameraManager.Config(
        width=1920,
        height=1080,
        autofocus=False,
        focus=90,
        filter=True,
    )
})

while True:
    print(cm.get_devices())
    print(cm.get_status())
    print(cm.get_config())
    print(cm.get_frames())
    time.sleep(1)


