import logging
import time

from pxl_actor.actor import Actor

from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.raw_capture import RawCapture

from pxl_camera.screen import Screen
from pxl_camera.detect import Detect


logging.basicConfig(level=logging.DEBUG)


conf = RawCapture.Config(
    device='/dev/video2',
    fourcc='UYVY',
    frame_width=640,
    frame_height=480,
    autofocus=False,
    focus=40
)

rc = RawCapture()
fm = FrameMuxer()
s = Screen()

print(f'Config success: {rc.set_config(conf)}')
input()
print('Sending ping message...')
fm.start(actor=rc)

input()

s.show()
s.update_image(fm.get_frame()[0])
s.wait()
