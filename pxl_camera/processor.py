"""
    Class for preprocessing frames and calculating whether or not the frames
    are good for further processing by models and stuff.
"""
import enum
import time

from pxl_actor.actor import Actor

from pxl_camera.frame import Frame
from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.util import image_processing


class Processor(Actor):

    class State(enum.Enum):

        BASE = enum.auto()  # Frame is same as base image
        MOVE = enum.auto()  # Frame is under movement
        GOOD = enum.auto()  # Frame is different from base image and static
        NONE = enum.auto()  # Frame not available (?)

    class _Worker(Actor):

        def process_frame(self, frame: Frame, last_frame: Frame, base_frame: Frame, processor):
            # TODO: Implement frame_processing

            processor.set_state(Processor.State.NONE, _requeue_worker=True)

    def __init__(self):
        super(Processor, self).__init__()

        self.base_frame = None
        self.last_frame = None
        self.started = True

        self._muxer = None
        self._worker = Processor._Worker()

    def __call__(self, muxer_actor: FrameMuxer):
        if not isinstance(muxer_actor, FrameMuxer):
            raise TypeError(f'muxer_actor [{type(muxer_actor)}] not instance of FrameMuxer')
        else:
            self.start(muxer_actor)
            return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, muxer_actor: FrameMuxer):
        self._muxer = muxer_actor
        self.started = True

        # We ping the worker, then worker pings us through update_state, then we ping him again there, etc.
        self._worker.process_frame(
            frame=self._muxer.get_frame(),
            last_frame=self.last_frame,
            base_frame=self.base_frame,
            processor=self,
            no_wait=True,
        )

    def stop(self):
        self.base_frame = None
        self.last_frame = None
        self.started = False
        self._muxer = None

    # Interface
    def get_base_frame(self):
        return self.base_frame

    def set_base_frame(self, base_frame: Frame):
        self.base_frame = base_frame

    def get_state(self):
        return self.state

    def set_state(self, state: State, _requeue_worker=False):
        self.state = state

        if self.started and _requeue_worker:
            self._worker.process_frame(
                frame=self._muxer.get_frame(),
                last_frame=self.last_frame,
                base_frame=self.base_frame,
                processor=self,
                no_wait=True,
            )
