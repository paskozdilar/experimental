"""
    Class for preprocessing frames and calculating whether or not the frames
    are good for further processing by models and stuff.
"""
import enum
import time

import cv2
from pxl_actor.actor import Actor

from pxl_camera.frame import Frame
from pxl_camera.frame_muxer import FrameMuxer
from pxl_camera.util import image_processing


class Processor(Actor):

    class State(enum.Enum):

        BASE = enum.auto()  # Frame is same as base image
        MOVE = enum.auto()  # Frame is moving
        GOOD = enum.auto()  # Frame is different from base image and static

        NO_BASE = enum.auto()   # Base frame not available; frame is not moving
        NO_MOVE = enum.auto()   # Move frame not available; frame is not base
        NONE = enum.auto()      # No information available

    class _Worker(Actor):
        """
            Worker for detecting movement and base image
        """

        # TODO: Take timestamps into account?

        def equal(self, frame_a: cv2.UMat, frame_b: cv2.UMat, roi: tuple = None):
            """
                Returns True if frame_a and frame_b are to be considered equal.
            """
            # TODO: Create two workers, one for absdiff and one for grid?

            GRID_ROWS = 10
            GRID_COLS = 5
            CELL_THRESHOLD = 10.

            ABS_THRESHOLD = 1
            GRID_THRESHOLD = 1

            # First round - fast processing
            abs_diff = image_processing.abs_diff(image_a=frame_a, image_b=frame_b, roi=roi)
            abs_diff = cv2.threshold(src=abs_diff, thresh=40, maxval=255, type=cv2.THRESH_BINARY)[1]

            abs_diff_factor = image_processing.abs_diff_factor(abs_diff)

            self.logger.debug(f'Absolute diff: {abs_diff_factor}, Threshold: {ABS_THRESHOLD}')

            return abs_diff_factor < ABS_THRESHOLD

            # if abs_diff > ABS_THRESHOLD:
            #     return False
            #
            # Second round - slow processing
            # grid_diff = image_processing.grid_diff_factor(
            #     image_a=frame_a, image_b=frame_b,
            #     rows=GRID_ROWS, cols=GRID_COLS,
            #     threshold=CELL_THRESHOLD,
            #     roi=roi,
            # )
            #
            # self.logger.debug(f'Grid diff: {grid_diff}, Threshold: {GRID_THRESHOLD}')
            #
            # return grid_diff < GRID_THRESHOLD

        def process_frame(self, frame: Frame, last_frame: Frame, base_frame: Frame, processor, roi: tuple):
            if frame is None:
                processor.set_state(Processor.State.NONE, _requeue_worker=True)
                return

            move = None
            base = None

            if last_frame is not None:
                self.logger.debug(f'Searching for movement')
                move = not self.equal(frame.frame, last_frame.frame, roi)
                self.logger.debug(f'Movement: {move}')

            if not move and base_frame is not None:
                self.logger.debug(f'Searching for base')
                base = self.equal(frame.frame, base_frame.frame, roi)
                self.logger.debug(f'Base: {base}')

            # Evaluation
            if move:
                state = Processor.State.MOVE
            elif base:
                state = Processor.State.BASE
            elif move is None and base is False:
                state = Processor.State.NO_MOVE
            elif move is False and base is None:
                state = Processor.State.NO_BASE
            elif move is False and base is False:
                state = Processor.State.GOOD
            else:
                state = Processor.State.NONE

            processor.set_state(state, _requeue_worker=True)

    def __init__(self, muxer_actor: FrameMuxer = None):
        super(Processor, self).__init__()

        self.frame = None
        self.base_frame = None
        self.last_frame = None
        self.roi = None
        self.started = True

        self.state = Processor.State.NONE

        self._muxer = None
        self._worker = Processor._Worker()

        if muxer_actor is not None:
            self.start(muxer_actor, no_wait=True)

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

        self._ping_worker()

    def stop(self):
        self.frame = None
        self.base_frame = None
        self.last_frame = None
        self.started = False
        self._muxer = None

    def _ping_worker(self):
        # Take new frame
        self.last_frame = self.frame
        self.frame = self._muxer.get_frame()

        self.logger.debug(f'Sending new frame to worker')

        # We ping the worker, then worker pings us through update_state, then we ping him again there, etc.
        self._worker.process_frame(
            frame=self.frame,
            last_frame=self.last_frame,
            base_frame=self.base_frame,
            processor=self,
            roi=self.roi,
            no_wait=True,
        )

    # Interface
    def get_roi(self):
        return self.roi

    def set_roi(self, roi: tuple):
        self.roi = roi

    def get_base_frame(self):
        return self.base_frame

    def set_base_frame(self, base_frame: Frame):
        self.base_frame = base_frame

    def get_state(self):
        return self.state

    def set_state(self, state: State, _requeue_worker=False):
        self.state = state

        if self.started and _requeue_worker:
            self._ping_worker()
