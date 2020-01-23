"""
    Example of a simple frame capturing application with background detection and GUI.

    Outputs images into ./frames/ directory with timestamp format defined in Frame class.
"""

import logging
import os
import time

from pxl_camera.capture.frame_muxer import FrameMuxer
from pxl_camera.capture.raw_capture import RawCapture
from pxl_camera.filter.processor import Processor
from pxl_camera.gui.screen import Screen
from pxl_camera.util.key import Key

# Set logging level
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
)

conf = RawCapture.Config(
    device='/dev/video0',
    fourcc='UYVY',
    frame_width=2*1920,
    frame_height=2*1080,
    autofocus=False
)

capture = RawCapture()
muxer = FrameMuxer()
processor = Processor()
screen = Screen()

logging.info('Starting...')

try:
    with capture(config=conf), \
            muxer(capture_actor=capture), \
            processor(muxer_actor=muxer), \
            screen(control_actor=capture):

        time.sleep(1)

        base_frame = muxer.get_frame()
        roi = (0.0, 0.0, 1.0, 1.0)
        processor.set_roi(roi)

        processor.set_base_frame(base_frame)

        index = 1

        os.makedirs('frames', exist_ok=True)

        while True:
            frame = muxer.get_frame()
            state = processor.get_state()

            # Reload base from screen command
            if screen.get_update_base():
                processor.set_base_frame(frame)

            # Reload ROI from screen command
            new_roi = screen.get_roi()
            if new_roi != roi:
                roi = new_roi
                processor.set_roi(roi)

            if screen.get_running():
                if state == Processor.State.GOOD:
                    screen.set_status('GOOD', color='green')
                    with open(f'frames/{frame.get_timestamp()}.jpeg', 'wb') as image_file:
                        image_file.write(frame.get_jpeg().tostring())
                        screen.set_index(index)
                        index += 1
                elif state == Processor.State.BASE:
                    screen.set_status('BASE', color='blue')
                elif state == Processor.State.MOVE:
                    screen.set_status('MOVE', color='red')
                elif state == Processor.State.NONE:
                    screen.set_status('UNKNOWN', color='gray')
            else:
                screen.set_status('PAUSED', color='gray')

            screen.update_image(frame)

            key = screen.wait(10)
            logging.debug(f'state: {state}, key: {key}')

            if key == Key.ENTER:
                screen.set_running(not screen.get_running())
            if key == Key.ESC:
                break

except Exception as exc:
    logging.error('Exception:', exc)