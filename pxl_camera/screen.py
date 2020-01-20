import cv2

from pxl_actor.actor import Actor

from pxl_camera.util import image


# TODO: Add concept + support for ROI mechanism
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

    def show(self):
        if not self.open:
            cv2.namedWindow(self.name, cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO | cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow(self.name, 640, 480)
            cv2.startWindowThread()

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

    def wait(self, timeout=0):
        return cv2.waitKey(timeout)

    def on_exit(self):
        self.hide()
        Screen._screen_names.remove(self.name)
