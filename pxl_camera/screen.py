"""
    Reference UI implementation for live-streaming frames, setting focus
    and general camera debugging.
"""

import enum

import cv2
import numpy

from pxl_actor.actor import Actor

from pxl_camera.frame import Frame


# TODO: Add concept + support for ROI mechanism
from pxl_camera.rectangle import Rectangle


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

    def __init__(self, name=None):
        super(Screen, self).__init__()

        if name is None:
            name = Screen._generate_name()
        Screen._screen_names.add(name)

        self.open = False
        self.image = Screen.empty_image(640, 480)
        self.name = name
        self.roi = Rectangle()
        self.pressed_down = False
        self.text = 'OK'
        self.text_color = (256, 0, 0)

    def show(self, control_actor=None):
        if not self.open:
            cv2.namedWindow(self.name, cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO | cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow(self.name, 640, 480)
            cv2.setMouseCallback(self.name, self.update_roi)

            if control_actor is not None:
                cv2.createTrackbar(
                    'Focus',    # Trackbar name
                    self.name,  # Window name
                    int(control_actor.get_focus()),     # Start value
                    256,        # Range
                    lambda value: control_actor.set_focus(focus=value, no_wait=True)    # On focus changed
                )

            self.open = True

    def hide(self):
        if self.open:
            cv2.destroyWindow(self.name)
            self.open = False

    def update_roi(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print('DOWN', event, x, y)
            self.pressed_down = True
            self.roi.set_start(x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            print('UP', event, x, y)
            self.pressed_down = False
            self.roi.set_end(x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.pressed_down:
            print('MOVE', event, x, y)
            self.roi.set_end(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            print('RIGHT', event, x, y)
            self.pressed_down = False
            self.roi = Rectangle()

    def get_roi(self):
        """
            Returns tuple (x1, y1, x2, y2) of two opposite vertices of the
            rectangle.
        """
        return self.roi.get()

    def set_text(self, text, color=None):
        self.text = text

        if color is None:
            return
        elif color == 'red':
            self.text_color = (0, 0, 255)
        elif color == 'green':
            self.text_color = (0, 255, 0)
        elif color == 'blue':
            self.text_color = (0, 255, 0)
        elif color == 'white':
            self.text_color = (255, 255, 255)

    def update_image(self, frame: cv2.UMat):
        """
            Updates screen with RGB encoded frame.
            Assumes frame has been copied and won't be modified concurrently
            by another actor.
        """
        x1, y1, x2, y2 = self.roi.get()

        # Draw ROI
        if (x1, y1, x2, y2) != (0., 0., 1., 1.):
            pt1 = int(x1), int(y1)
            pt2 = int(x2), int(y2)

            frame = cv2.rectangle(frame, pt1, pt2, 255, 5)

        # Draw font
        font_height = 40
        font_scale = cv2.getFontScaleFromHeight(cv2.FONT_HERSHEY_DUPLEX, font_height, 2)
        cv2.putText(
            frame,                      # image
            self.text,                  # text
            (10, 10 + font_height),     # text
            cv2.FONT_HERSHEY_DUPLEX,    # font face
            font_scale,                 # font scale
            self.text_color,            # color
            2,                          # thickness
            cv2.LINE_AA                 # line type (opencv)
        )

        cv2.imshow(self.name, frame)

    def wait(self, timeout=0):
        return cv2.waitKey(timeout)

    def on_exit(self):
        self.hide()
        Screen._screen_names.remove(self.name)
