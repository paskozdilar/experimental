import numpy


def empty_image(width, height):
    return numpy.zeros((int(width), int(height), 3), numpy.uint8)
