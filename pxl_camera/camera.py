"""
    Class for single camera management.

    Manages a single camera through /dev/videoX node.
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
        fps: int

    def __init__(self, config: Config = None):
        super(Camera, self).__init__()

        self.capture = RawCapture()
        self.muxer = FrameMuxer()
        self.processor = Processor()

        if config is not None:
            self.start(config)

    def __call__(self, config: Config = None):
        if isinstance(config, Camera.Config):
            self.start(config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, config: Config):
        capture_config = RawCapture.Config(
            device=config.device,
            frame_width=config.width,
            frame_height=config.height,
            fps=config.fps,
        )

        self.capture.start(config=capture_config)
        self.muxer.start(capture_actor=self.capture)
        self.processor.start(muxer_actor=self.muxer)

    def stop(self):
        self.processor.stop()
        self.muxer.stop()
        self.capture.stop()
