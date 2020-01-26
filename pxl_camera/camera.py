"""
    Generic class for single camera management.

    Manages a single camera through /dev/videoX node and allows control over
    resolution, focus and preprocessing.
"""

import dataclasses

from pxl_actor.actor import Actor

from pxl_camera.capture.frame_muxer import FrameMuxer
from pxl_camera.capture.raw_capture import RawCapture

from pxl_camera.filter.processor import Processor


class Camera(Actor):

    @dataclasses.dataclass
    class Config:
        device: str = None
        width: int = None
        height: int = None
        autofocus: bool = None
        focus: int = None
        filter: bool = None

    def __init__(self, config: Config = None):
        super(Camera, self).__init__()

        self.config = config

        self.capture = RawCapture()
        self.muxer = FrameMuxer()
        self.processor = Processor()

        if config is not None:
            self.start(config)

    def __call__(self, config: Config = None):
        if not isinstance(config, Camera.Config):
            raise TypeError(f'config [{type(config)}] not instance of Config.Config')
        else:
            self.start(config)
            return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, config: Config):
        self.logger.info(f'Starting Camera [{config}]')

        self.config = config

        capture_config = RawCapture.Config(
            device=config.device,
            frame_width=config.width,
            frame_height=config.height,
            focus=config.focus,
            autofocus=config.autofocus
        )

        self.capture.start(config=capture_config)
        self.muxer.start(capture_actor=self.capture)

        if config.filter:
            self.processor.start(muxer_actor=self.muxer)

    def stop(self):
        self.processor.stop()
        self.muxer.stop()
        self.capture.stop()

    #
    def get_filter(self):
        return self.config.filter

    def set_filter(self, filter: bool):
        old_filter = self.config.filter
        new_filter = filter

        if new_filter is True and old_filter is False:
            self.processor.start(self.muxer)
        if new_filter is False and old_filter is True:
            self.processor.stop()

        self.config.filter = filter

    def reset_filter(self):
        """
            Automatically loads last frame from frame muxer and sets it as the
            base frame of Processor.
        """
        self.set_base_frame(self.muxer.get_frame())

    #
    def get_autofocus(self):
        return self.config.autofocus

    def set_autofocus(self, autofocus: bool):
        success = self.capture.set_autofocus(autofocus)
        if success:
            self.config.autofocus = autofocus
        return success

    #
    def get_focus(self):
        return self.capture.get_focus()

    def set_focus(self, focus: int):
        success = self.capture.set_focus(focus)
        if success:
            self.config.focus = focus
        return success

    #
    def get_base_frame(self):
        return self.processor.get_base_frame()

    def set_base_frame(self, base_frame):  # Frame
        self.processor.set_base_frame(base_frame)

    #
    def get_diff_frame(self):
        return self.processor.get_diff_frame()

    def set_diff_frame(self, frame):
        self.processor.set_diff_frame(frame)

    # Note: 'roi' is a tuple of normalized coordinates (x1, y1, x2, y2)
    #       (i.e. x1, y1, x2, y2 are all real numbers between 0.0 and 1.0)
    def get_roi(self):
        return self.processor.get_roi()

    def set_roi(self, roi: tuple):
        self.processor.set_roi(roi)

    #
    def get_frame(self):
        frame = self.muxer.get_frame()
        if frame:
            frame.state = self.processor.get_state()

        return frame
