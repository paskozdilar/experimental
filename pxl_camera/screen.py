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
        return numpy.zeros((int(width), int(height), 3), numpy.uint8)

    def __init__(self, name=None):
        super(Screen, self).__init__()

        if name is None:
            name = Screen._generate_name()
        Screen._screen_names.add(name)

        self.open = False
        self.image = Screen.empty_image(640, 480)
        self.name = name

    def show(self, actor=None):
        if not self.open:
            cv2.namedWindow(self.name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_EXPANDED)
            cv2.resizeWindow(self.name, 640, 480)

            if actor is not None:
                cv2.createTrackbar('Focus', self.name, 0, 256, lambda value: actor.set_focus(focus=value))

            self.open = True

    def hide(self):
        if self.open:
            cv2.destroyWindow(self.name)
            self.open = False

    def update_image(self, frame: Frame):
        """
            Updates screen with RGB encoded frame.
            Assumes frame is copied and won't be modified concurrently by another actor.
        """
        cv2.imshow(self.name, frame.data)

    def wait(self, timeout=0):
        return cv2.waitKey(timeout)

    def on_exit(self):
        self.hide()
        Screen._screen_names.remove(self.name)
