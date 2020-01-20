"""
    Frame muxer class for timestamping and multiplexing
    frames from a single camera.

    If no frames are available, returns None.

    Otherwise returns a Frame object containing the frame
    in RGB format and timestamp of the captured frame.

"""

import datetime
from typing import Union

import cv2

from pxl_actor.actor import Actor

from pxl_camera.frame import Frame
from pxl_camera.raw_capture import RawCapture


class FrameMuxer(Actor):

    def __init__(self):
        super(FrameMuxer, self).__init__()

        self.frame = None
        self.colorspace = None
        self.timestamp = None
        self.started = None

    def start(self, actor: RawCapture):
        self.started = True
        self.ping(actor)

    def stop(self):
        self.started = False

    def ping(self, actor: RawCapture):
        if not self.started:
            return

        frame = actor.get_frame()
        timestamp = datetime.datetime.now()

        if frame is None:
            self.stop()
            return

        # Frame is valid
        self.frame = frame
        self.timestamp = timestamp

        if self.colorspace is None:
            self.colorspace = getattr(cv2, f'COLOR_YUV2BGR_{actor.config.fourcc.upper()}')

        # noinspection PyCallByClass
        Actor.ProxyMethod(
            actor=self,
            method='ping',
        )(actor=actor, no_wait=True)

    def get_frame(self) -> Union[None, Frame]:
        """
            Returns None or a Frame object containing the last frame with timestamp.
        """
        if self.frame is None:
            return None

        rgb_frame = cv2.cvtColor(self.frame, self.colorspace)

        return Frame(data=rgb_frame, timestamp=self.timestamp)
