import logging
import time

from pxl_camera.camera import Camera


logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
)


camera = Camera()
config = Camera.Config(
    device='/dev/video0',
    width=1920,
    height=1080,
)

with camera(config):
    frame = camera.get_frame()
    print(frame.state)
    camera.set_base_frame(frame)
    time.sleep(1)
    frame = camera.get_frame()
    print(frame.state)
    camera.set_base_frame(None)
    time.sleep(1)
    frame = camera.get_frame()
    print(frame.state)

