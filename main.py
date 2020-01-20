import logging
import time

from pxl_actor.actor import Actor

from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.raw_capture import RawCapture
from pxl_camera.util.ascii import Key

from pxl_camera.screen import Screen
from pxl_camera.detect import Detect


logging.basicConfig(level=logging.DEBUG)


conf = RawCapture.Config(
    device='/dev/video2',
    fourcc='UYVY',
    frame_width=3840,
    frame_height=2160,
    autofocus=False,
    focus=40
)

print('Starting RawCapture...')
rc = RawCapture()

print('Starting FrameMuxer...')
fm = FrameMuxer()

print('Starting Screen...')
s = Screen()

print(f'Config success: {rc.set_config(conf)}')
print('Sending ping message...')
fm.start(actor=rc)

while True:
    s.show()
    s.update_image(fm.get_frame())
    key = s.wait(1)

    if key in (Key.ENTER, Key.ESC):
        break

s.hide()


