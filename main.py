import logging
import time

from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.processor import Processor
from pxl_camera.raw_capture import RawCapture

from pxl_camera.screen import Screen

# Fix KeyboardInterrupt handling on threading.Event.wait()
from pxl_camera.util.key import Key

# Set logging level
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(name)s:%(filename)s:%(lineno)d] - [%(funcName)s] - %(asctime)s - %(levelname)s - %(message)s"
)

conf = RawCapture.Config(
    device='/dev/video2',
    fourcc='UYVY',
    frame_width=3840,
    frame_height=2160,
    autofocus=False
)

print('Starting RawCapture...')
capture = RawCapture()

print('Starting FrameMuxer...')
muxer = FrameMuxer()

print('Starting Processor...')
processor = Processor()

print('Starting Screen...')
screen = Screen()


try:
    with capture(config=conf) as capture, \
            muxer(capture_actor=capture) as muxer, \
            processor(muxer_actor=muxer) as processor, \
            screen(control_actor=capture) as screen:

        while True:
            frame = muxer.get_frame()

            state = processor.get_state()

            if state == Processor.State.GOOD or state == Processor.State.NO_BASE:
                screen.set_status('GOOD', color='green')
            elif state == Processor.State.BASE:
                screen.set_status('BASE', color='blue')
            elif state == Processor.State.MOVE:
                screen.set_status('MOVE', color='red')
            elif state == Processor.State.NONE:
                screen.set_status('UNKNOWN', color='gray')

            screen.update_image(frame)

            key = screen.wait(10)
            print(state, key)

            if key == Key.ENTER or key == Key.ESC:
                break

except Exception as exc:
    print('Exception:', exc)

# fm.start(capture_actor=rc)
# s.start(control_actor=rc)
# p.start(muxer_actor=fm)
#
#
# print('Waiting for first frame...')
# frame = fm.get_frame()
# last_frame = frame
# print('Got first frame.')
#
# frame_deque = collections.deque(maxlen=10)
# frame_deque.append(last_frame)
#
# FPS = 15
# DIFF_THRESHOLD = 1
# GRID_ROWS = 5
# GRID_COLS = 5
#
# kernel = numpy.ones((10, 10), numpy.uint8)
#
# while True:
#     frame = fm.get_frame()
#     while frame.timestamp == last_frame.timestamp:
#         time.sleep(1/60)
#         frame = fm.get_frame()
#
#     if last_frame is not None and frame is not None:
#
#
#         s.update_image(frame_diff)
#         key = s.wait(10)
#
#         if key in (Screen.Key.ENTER, Screen.Key.ESC):
#             break
#
#         s.update_image(frame.frame)
#         key = s.wait(10)
#
#         if key in (Screen.Key.ENTER, Screen.Key.ESC):
#             break
#
# s.stop()
# time.sleep(1)
