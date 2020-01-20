import logging
import threading
import time

import cv2
from pxl_actor.actor import Actor

from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.raw_capture import RawCapture

from pxl_camera.screen import Screen
from pxl_camera.detect import Detect


logging.basicConfig(level=logging.DEBUG)


conf = RawCapture.Config(
    device='/dev/video0',
    fourcc='YUYV',
    frame_width=3840,
    frame_height=2160,
    autofocus=False
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

s.show(rc)

while True:
    frame = fm.get_frame()
    if frame is not None:
        s.update_image(frame)
        key = s.wait(1)

        if key in (Screen.Key.ENTER, Screen.Key.ESC):
            break

s.hide()


