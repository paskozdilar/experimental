import logging
import threading
import time

import cv2
import numpy
from pxl_actor.actor import Actor

from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.image_processor import crop, abs_diff, sharpness
from pxl_camera.raw_capture import RawCapture

from pxl_camera.screen import Screen
from pxl_camera.detect import Detect


logging.basicConfig(level=logging.DEBUG)


conf = RawCapture.Config(
    device='/dev/video2',
    fourcc='UYVY',
    frame_width=1920,
    frame_height=1080,
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
fm.start(capture_actor=rc)
s.show(control_actor=rc)

print('Waiting for first frame...')
frame = fm.get_frame()
last_frame = frame

DIFF_THRESHOLD = 40

while True:
    #last_frame = frame
    frame = fm.get_frame()

    if last_frame is not None and frame is not None:
        time_diff = frame.timestamp - last_frame.timestamp
        frame_diff = abs_diff(frame.frame, last_frame.frame)

        # diff_factor = sum(cv2.sumElems(abs_diff))
        diff_factor = sum(cv2.mean(frame_diff)) / (time_diff.microseconds / 1000)

        if diff_factor < DIFF_THRESHOLD:
            last_frame = frame
            s.set_text(f'Movement factor: {diff_factor}', color='blue')
        else:
            s.set_text(f'Movement factor: {diff_factor}', color='red')

        s.update_image(frame_diff)
        key = s.wait(1)

        if key in (Screen.Key.ENTER, Screen.Key.ESC):
            break


s.hide()


