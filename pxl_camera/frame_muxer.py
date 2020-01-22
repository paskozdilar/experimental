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
from pxl_camera.util import image_processing


class FrameMuxer(Actor):

    def __init__(self, capture_actor: RawCapture = None):
        super(FrameMuxer, self).__init__()

        self.frame = None
        self.colorspace = None
        self.timestamp = None
        self.started = None

        if capture_actor is not None:
            self.start(capture_actor, no_wait=True)

    def __call__(self, capture_actor: RawCapture):
        if not isinstance(capture_actor, RawCapture):
            raise TypeError(f'capture_actor [{type(capture_actor)}] not instance of RawCapture')
        else:
            self.start(capture_actor)
            return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, capture_actor: RawCapture):
        self.started = True
        self.ping(capture_actor)

    def stop(self):
        self.started = False

    def on_exit(self):
        self.stop()

    def ping(self, capture_actor: RawCapture):
        if not self.started:
            return

        frame = capture_actor.get_frame()
        timestamp = datetime.datetime.now()

        if frame is None:
            self.stop()
            return

        # Frame is valid
        self.frame = frame
        self.timestamp = timestamp

        if self.colorspace is None:
            self.colorspace = getattr(cv2, f'COLOR_YUV2BGR_{capture_actor.config.fourcc.upper()}')

        self.enqueue(method='ping', kwargs={'capture_actor': capture_actor})

    def get_frame(self) -> Union[None, Frame]:
        """
            Returns None or a Frame object containing the last frame with timestamp.
        """
        if self.frame is None:
            return None

        rgb_frame = cv2.cvtColor(self.frame, self.colorspace)
        width, height, channels = image_processing.image_size(rgb_frame)

        return Frame(width=width, height=height, channels=channels, frame=rgb_frame, timestamp=self.timestamp)
