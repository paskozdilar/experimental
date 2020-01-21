"""
    Class for preprocessing frames and calculating whether or not the frames
    are good for further processing by models and stuff.
"""

from pxl_actor.actor import Actor

from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.util import image_processing


class Processor(Actor):

    def __init__(self):
        super(Processor, self).__init__()

        self.started = False

    def start(self, muxer_actor: FrameMuxer):
        self.started = True
        self.ping(muxer_actor)

    def stop(self):
        self.started = False

    def ping(self, muxer_actor: FrameMuxer):
        if not self.started:
            return

        frame = muxer_actor.get_frame()

        # PROCESS

        self.enqueue(method='ping', args=(muxer_actor,))

    def good(self):
        return True

