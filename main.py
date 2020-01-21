# import collections
# import logging
# import time
#
# import cv2
# import numpy
#
# from pxl_camera.frame_muxer import FrameMuxer
# from pxl_camera.util.image_processing import abs_diff, abs_diff_factor
# from pxl_camera.raw_capture import RawCapture
#
# from pxl_camera.screen import Screen
#
# logging.basicConfig(level=logging.DEBUG)
#
#
# conf = RawCapture.Config(
#     device='/dev/video2',
#     fourcc='UYVY',
#     frame_width=2840,
#     frame_height=2160,
#     autofocus=False
# )
#
# print('Starting RawCapture...')
# rc = RawCapture()
#
# print('Starting FrameMuxer...')
# fm = FrameMuxer()
#
# print('Starting Screen...')
# s = Screen()
#
# print(f'Config success: {rc.set_config(conf)}')
# print('Sending ping message...')
# fm.start(capture_actor=rc)
# s.show(control_actor=rc)
#
# print('Waiting for first frame...')
# frame = fm.get_frame()
# last_frame = frame
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
#         time_diff = frame.timestamp - last_frame.timestamp
#         frame_diff = abs_diff(frame.frame, last_frame.frame)
#
#         frame_diff = cv2.erode(frame_diff, kernel, frame_diff)
#         frame_diff = cv2.dilate(frame_diff, kernel, frame_diff)
#
#         start_time = time.time()
#         diff_factor = abs_diff_factor(frame.frame, last_frame.frame)
#         end_time = time.time()
#         print(end_time - start_time)
#
#         if diff_factor < DIFF_THRESHOLD:
#             frame_deque.append(frame)
#             s.set_text(f'Movement factor: {diff_factor}', color='blue')
#         else:
#             # What the fuck did I do here?
#             last_frame = frame_deque.popleft()
#             frame_deque.clear()
#             frame_deque.append(last_frame)
#             s.set_text(f'Movement factor: {diff_factor}', color='red')
#
#         # s.update_image(frame.frame)
#         s.update_image(frame_diff)
#         key = s.wait(10)
#
#         if key in (Screen.Key.ENTER, Screen.Key.ESC):
#             break
#
# s.hide()
# time.sleep(1)
#

from pxl_actor.actor import Actor
