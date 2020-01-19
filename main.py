import logging
import time

from pxl_actor.actor import Actor

from pxl_camera.raw_capture import RawCapture
from pxl_camera.screen import Screen
from pxl_camera.detect import Detect


class Manager(Actor):

    def handle_event(self):
        print('Event happened')


m = Manager()
d = Detect(actor=m, )

print(d.get_devices())
