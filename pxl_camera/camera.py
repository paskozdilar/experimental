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
        device: str
        width: int
        height: int

    def __init__(self, config: Config = None, _filter: bool = True):
        super(Camera, self).__init__()

        self.capture = RawCapture()
        self.muxer = FrameMuxer()
        self.processor = Processor()
        self._filter = False

        if config is not None:
            self.start(config)

    def __call__(self, config: Config = None, _filter: bool = True):
        if not isinstance(config, Camera.Config):
            raise TypeError(f'config [{type(config)}] not instance of Config.Config')
        else:
            self.start(config)
            return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, config: Config, _filter=True):
        self.logger.info(f'Starting Camera [{config}]')

        capture_config = RawCapture.Config(
            device=config.device,
            frame_width=config.width,
            frame_height=config.height,
        )

        self.capture.start(config=capture_config)
        self.muxer.start(capture_actor=self.capture)

        if _filter:
            self.processor.start(muxer_actor=self.muxer)

        self._filter = _filter

    def stop(self):
        self.processor.stop()
        self.muxer.stop()
        self.capture.stop()

        self._filter = False

    #
    def get_focus(self):
        return self.capture.get_focus()

    def set_focus(self, focus: int):
        return self.capture.set_focus(focus)

    #
    def get_base_frame(self):
        return self.processor.get_base_frame()

    def set_base_frame(self, base_frame):
        self.processor.set_base_frame(base_frame)

    #
    def get_diff_frame(self):
        return self.processor.get_diff_frame() if self._filter else None

    def set_diff_frame(self, frame):
        self.processor.set_diff_frame(frame)

    #
    def get_frame(self):
        frame = self.muxer.get_frame()
        frame.state = self.processor.get_state()

        return frame
