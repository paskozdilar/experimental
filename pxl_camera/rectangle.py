import cv2
from pxl_actor.actor import Actor


class Rectangle(Actor):

    def __init__(self):
        super(Rectangle, self).__init__()

        self.x1 = 0.
        self.y1 = 0.
        self.x2 = 1.
        self.y2 = 1.

    def set_end(self, x, y):
        """
            Sets x2, y2 coordinates of a rectangle while keeping x1, y1 constant.
        """
        self.x2 = x
        self.y2 = y

    def set_start(self, x, y):
        """
            Sets both coordinates of a rectangle to the same point
        """
        self.x1 = self.x2 = x
        self.y1 = self.y2 = y

    def get(self):
        """
            Returns rectangle coordinates as tuple (x1, y1, x2, y2), where
            (x1, y1) is the top left corner and (x2, y2) is the bottom right
            corner.
        """
        x_left = min(self.x1, self.x2)
        x_right = max(self.x1, self.x2)
        y_left = min(self.y1, self.y2)
        y_right = max(self.y1, self.y2)

        return x_left, y_left, x_right, y_right
