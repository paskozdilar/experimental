"""
    Reference UI implementation for live-streaming frames, setting focus
    and general camera debugging.
"""

import enum
import time

import cv2
import numpy

from pxl_actor.actor import Actor

from pxl_camera.frame import Frame


# TODO: Add concept + support for ROI mechanism
from pxl_camera.raw_capture import RawCapture
from pxl_camera.rectangle import Rectangle
from pxl_camera.util.image_processing import image_size
from pxl_camera.util.key import Key


class Screen(Actor):

    class Key(enum.IntEnum):
        NONE = -1

        ENTER = 13
        ESC = 27

    _screen_names = set()

    @classmethod
    def _generate_name(cls):
        i = 1
        name = lambda x: f'Screen_{x}'

        while name(i) in cls._screen_names:
            i += 1

        return name(i)

    @staticmethod
    def empty_image(width, height):
        return numpy.zeros((int(height), int(width), 3), numpy.uint8)

    def __init__(self, name=None, control_actor: RawCapture = None):
        super(Screen, self).__init__()

        if name is None:
            name = Screen._generate_name()
        Screen._screen_names.add(name)

        self.open = False
        self.image = Screen.empty_image(640, 480)
        self.name = name
        self.roi = Rectangle()
        self.new_roi = Rectangle()
        self.pressed_down = False
        self.status = 'OK'
        self.status_color = (255, 0, 0)
        self.last_update = 0

        if control_actor is not None:
            self.start(control_actor, no_wait=True)

    def __call__(self, control_actor: RawCapture):
        if not isinstance(control_actor, RawCapture):
            raise TypeError(f'control_actor [{type(control_actor)}] not instance of RawCapture')
        else:
            self.start(control_actor)
            return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, control_actor: RawCapture):
        if not self.open:
            cv2.namedWindow(self.name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow(self.name, 640, 480)
            cv2.setMouseCallback(self.name, self.update_roi)

            cv2.createTrackbar(
                'Focus',                            # Trackbar name
                self.name,                          # Window name
                int(control_actor.get_focus()),     # Start value
                256,                                # Range
                lambda value: control_actor.set_focus(focus=value, no_wait=True)    # On focus changed
            )

            self.open = True

    def stop(self):
        if self.open:
            cv2.destroyWindow(self.name)
            self.open = False

    def on_exit(self):
        self.stop()
        Screen._screen_names.remove(self.name)

    def update_roi(self, event, x, y, flags, param):
        """
            Called by OpenCV mouse callback.
        """
        width, height, _ = image_size(self.image)
        print(f'x={x}, y={y}, width={width}, height={height}')

        x /= width
        y /= height

        if event == cv2.EVENT_LBUTTONDOWN:
            self.logger.debug(f'Mouse event: {event} [LBUTTONDOWN]')
            self.pressed_down = True
            self.new_roi.set_start(x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.logger.debug(f'Mouse event: {event} [LBUTTONUP]')
            self.pressed_down = False
            self.new_roi.set_end(x, y)
            self.roi = self.new_roi
        elif event == cv2.EVENT_MOUSEMOVE and self.pressed_down:
            self.logger.debug(f'Mouse event: {event} [MOUSEMOVE]')
            self.new_roi.set_end(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.logger.debug(f'Mouse event: {event} [RBUTTONDOWN]')
            self.pressed_down = False
            self.roi = Rectangle()

    def set_roi(self, roi: tuple):
        self.roi.set_start(roi[0], roi[1])
        self.roi.set_end(roi[2], roi[3])

    def get_roi(self):
        """
            Returns tuple (x1, y1, x2, y2) of two opposite vertices of the
            rectangle.
        """
        return self.roi.get()

    def set_status(self, status, color=None):
        self.status = status

        if color is None:
            return
        elif color == 'red':
            self.status_color = (0, 0, 255)
        elif color == 'green':
            self.status_color = (0, 255, 0)
        elif color == 'blue':
            self.status_color = (255, 0, 0)
        elif color == 'white':
            self.status_color = (255, 255, 255)
        elif color == 'black':
            self.status_color = (0, 0, 0)
        elif color == 'gray':
            self.status_color = (127, 127, 127)

    def update_image(self, frame: Frame):
        """
            Updates screen with RGB encoded frame.
            Assumes frame has been copied and won't be modified concurrently
            by another actor.
        """
        x1, y1, x2, y2 = self.new_roi.get()
        width, height, _ = image_size(frame.frame)

        # Draw ROI
        pt1 = int(x1 * width), int(y1 * height)
        pt2 = int(x2 * width), int(y2 * height)

        frame.frame = cv2.rectangle(frame.frame, pt1, pt2, 255, 5)

        # Draw font
        font_height = height // 16
        thickness = height // 256

        font_scale = cv2.getFontScaleFromHeight(cv2.FONT_HERSHEY_DUPLEX, font_height, 2)
        cv2.putText(
            frame.frame,                # image
            f'STATUS: {self.status}',   # text
            (10, 10 + font_height),     # origin
            cv2.FONT_HERSHEY_DUPLEX,    # font face
            font_scale,                 # font scale
            self.status_color,            # color
            thickness,                  # thickness
            cv2.FILLED                  # line type (opencv)
        )

        # FPS
        current_time = time.time()
        last_time = self.last_update
        self.last_update = current_time

        cv2.putText(
            frame.frame,  # image
            f'FPS: {1 / (current_time - last_time):.1f}',  # text
            (10, 10 + int(2.2*font_height)),  # origin
            cv2.FONT_HERSHEY_DUPLEX,  # font face
            font_scale,  # font scale
            self.status_color,  # color
            thickness,  # thickness
            cv2.FILLED  # line type (open cv)
        )

        # Send to screen
        cv2.imshow(self.name, frame.frame)

        # Save frame
        self.image = frame.frame

    def wait(self, timeout=0):
        key_num = cv2.waitKey(timeout)

        if key_num not in set(map(int, Key)):
            return Key.UNKNOWN

        return Key(key_num)
