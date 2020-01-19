from pxl_actor.actor import Actor

from pxl_camera.detect import Detect
from pxl_camera.raw_capture import RawCapture


class FrameMuxer(Actor):

    def __init__(self):
        super(FrameMuxer, self).__init__()

        self.detect = Detect()

    def start_muxer(self, actor: RawCapture):
        actor.get_frame()

