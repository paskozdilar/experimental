import cv2

from pxl_actor.actor import Actor

from pxl_camera.util import image
from pxl_camera.util.ascii import Key


class Screen(Actor):
    """
        Abstract class for showing view and selecting region-of-interest.
    """

    _screen_names = set()

    @classmethod
    def _generate_name(cls):
        i = 1
        name = lambda x: f'Screen_{x}'

        while name(i) in cls._screen_names:
            i += 1

        return name(i)

    def __init__(self, name=None):
        super(Screen, self).__init__()

        if name is None:
            name = Screen._generate_name()
        Screen._screen_names.add(name)

        self.open = False
        self.image = image.empty_image(1920, 1080)
        self.name = name
        self.key = None

    def __del__(self):
        self.hide()
        Screen._screen_names.remove(self.name)
        super(Screen, self).__del__()

    def show(self):
        if not self.open:
            cv2.namedWindow(self.name, cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO | cv2.WINDOW_GUI_NORMAL)

    def hide(self):
        if self.open:
            cv2.destroyWindow(self.name)

    def update_image(self, frame):
        """
            Updates screen with RGB encoded frame.
            Assumes frame is copied and won't be modified concurrently by another actor.
        """
        if frame is not None:
            cv2.imshow(self.name, frame)
            self.key = cv2.waitKey(1)

    def wait(self, timeout=None):
        key = cv2.waitKey(timeout)

        if key == Key.NONE:
            return None

        if key == Key.ENTER or key == Key.ESC:
            return True
