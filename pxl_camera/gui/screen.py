"""
    Reference UI implementation for live-streaming frames, setting focus
    and general camera debugging.

    MAYBE: Refactor - remove controlling logic from the UI and just use it as
           an interface to some internal mechanism?
"""

import enum
import time

import cv2
import numpy

from pxl_actor.actor import Actor

from pxl_camera.capture.raw_capture import RawCapture
from pxl_camera.util.frame import Frame
from pxl_camera.util.image_processing import image_size
from pxl_camera.util.key import Key
from pxl_camera.util.rectangle import Rectangle


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

        self.logger.debug(f'Initializing Screen: {name}')

        self.open = False
        self.image = Screen.empty_image(640, 480)
        self.name = name

        self.roi = Rectangle()
        self.new_roi = Rectangle()
        self.pressed_down = False
        self.running = False

        self.status = 'OK'
        self.status_color = (255, 0, 0)
        self.last_update = 0

        self.update_base = False
        self.index = 0

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
            self.logger.info(f'Set new ROI: {self.roi.get()}')
        elif event == cv2.EVENT_MOUSEMOVE and self.pressed_down:
            self.logger.debug(f'Mouse event: {event} [MOUSEMOVE]')
            self.new_roi.set_end(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.logger.debug(f'Mouse event: {event} [RBUTTONDOWN]')
            self.pressed_down = False
            self.update_base = True

    def set_roi(self, roi: tuple):
        self.roi.set_start(roi[0], roi[1])
        self.roi.set_end(roi[2], roi[3])

    def get_roi(self):
        """
            Returns tuple (x1, y1, x2, y2) of two opposite vertices of the
            rectangle.
        """
        return self.roi.get()

    def set_running(self, running):
        self.running = running

    def get_running(self):
        return self.running

    def get_update_base(self):
        update_base = self.update_base
        self.update_base = False
        return update_base

    def set_index(self, index):
        self.index = index

    def set_status(self, status, color=None):
        if self.status != status:
            self.logger.debug(f'Status update: {status}')

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

    @staticmethod
    def _put_text_outline(image, text, font_height, row, font_scale, color, thickness):
        cv2.putText(
            image,      # image
            text,       # text
            (10, int(1.5*row*font_height)),  # origin
            cv2.FONT_HERSHEY_DUPLEX,  # font face
            font_scale,  # font scale
            (0, 0, 0),  # color
            thickness + 5,  # thickness
            cv2.FILLED  # line type (opencv)
        )

        cv2.putText(
            image,  # image
            text,  # text
            (10, int(1.5*row*font_height)),  # origin
            cv2.FONT_HERSHEY_DUPLEX,  # font face
            font_scale,  # font scale
            color,  # color
            thickness,  # thickness
            cv2.FILLED  # line type (opencv)
        )

    def update_image(self, frame: Frame):
        """
            Updates screen with RGB encoded frame.
            Assumes frame has been copied and won't be modified concurrently
            by another actor.
        """
        x1, y1, x2, y2 = self.new_roi.get()
        width, height, channels = image_size(frame.frame)

        if channels == 1:
            frame.frame = cv2.cvtColor(frame.frame, cv2.COLOR_GRAY2RGB, frame.frame)

        font_height = height // 32
        thickness = height // 256
        font_scale = cv2.getFontScaleFromHeight(cv2.FONT_HERSHEY_DUPLEX, font_height, 2)

        def row():
            _row = 1
            while True:
                yield _row
                _row += 1

        row = row()

        current_time = time.time()
        last_time = self.last_update
        self.last_update = current_time

        #
        # Draw ROI
        pt1 = int(x1 * width), int(y1 * height)
        pt2 = int(x2 * width), int(y2 * height)

        self.image = cv2.rectangle(frame.frame, pt1, pt2, 255, thickness)

        # Draw font
        self._put_text_outline(
            image=self.image,
            text=f'STATUS: {self.status}',
            font_height=font_height,
            row=row.__next__(),
            font_scale=font_scale,
            color=self.status_color,
            thickness=thickness,
        )

        # FPS
        self._put_text_outline(
            image=self.image,
            text=f'FPS: {1 / (current_time - last_time):.1f}',
            font_height=font_height,
            row=row.__next__(),
            font_scale=font_scale,
            color=self.status_color,
            thickness=thickness,
        )

        # Image counter
        self._put_text_outline(
            image=self.image,
            text=f'IMAGES CAPTURED: {self.index}',
            font_height=font_height,
            row=row.__next__(),
            font_scale=font_scale,
            color=self.status_color,
            thickness=thickness,
        )

        # Instructions
        self._put_text_outline(
            image=self.image,
            text=f'[ENTER - {"stop" if self.running else "start"} capturing]',
            font_height=font_height,
            row=row.__next__(),
            font_scale=font_scale,
            color=self.status_color,
            thickness=thickness,
        )

        self._put_text_outline(
            image=self.image,
            text=f'[ESC - exit]',
            font_height=font_height,
            row=row.__next__(),
            font_scale=font_scale,
            color=self.status_color,
            thickness=thickness,
        )

        self._put_text_outline(
            image=self.image,
            text=f'[LEFT MOUSE - draw ROI]',
            font_height=font_height,
            row=row.__next__(),
            font_scale=font_scale,
            color=self.status_color,
            thickness=thickness,
        )

        self._put_text_outline(
            image=self.image,
            text=f'[RIGHT MOUSE - reset base image]',
            font_height=font_height,
            row=row.__next__(),
            font_scale=font_scale,
            color=self.status_color,
            thickness=thickness,
        )

        # Send to screen
        cv2.imshow(self.name, self.image)

    def wait(self, timeout=0):
        try:
            key_num = cv2.waitKey(timeout)
        except BaseException as bex:
            self.logger.critical(bex, exc_info=True)
            return

        if key_num not in set(map(int, Key)):
            return Key.UNKNOWN

        return Key(key_num)
