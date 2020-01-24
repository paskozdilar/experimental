"""
    Various image processing utilities used for image filtering.
"""
from functools import reduce, lru_cache

import cv2
import numpy


def image_size(image):
    if isinstance(image, cv2.UMat):
        height = len(image.get())
        width = len(image.get()[0])
        channels = len(image.get()[0][0])
    elif isinstance(image, numpy.ndarray):
        height = len(image)
        width = len(image[0])
        channels = len(image[0][0])
    else:
        raise TypeError(f'Unknown image type: {type(image)}')

    return width, height, channels


def crop(image: cv2.UMat, roi: tuple):
    """
        Returns given image cropped to the unit-based coordinates
        (x1, y1, x2, y2 are real numbers between 0 and 1).
    :param image: cv2.UMat object containing RGB frame.
    :param roi: tuple containing coordinates (x1, y1, x2, y2) where x1,y1 is
                the upper-left corner and x2,y2 is bottom-right corner (opt.)
    :return: cv.UMat object of the cropped image
    """
    width, height, _ = image_size(image)

    x1, y1, x2, y2 = roi
    x1, x2 = int(max(0, min(x1 * width, x2 * width))), int(min(width, max(x1 * width, x2 * width)))
    y1, y2 = int(max(0, min(y1 * height, y2 * height))), int(min(height, max(y1 * height, y2 * height)))

    return cv2.UMat(image, [y1, y2], [x1, x2])


def sharpness(image: cv2.UMat):
    """
        Calculates a sharpness factor from a given frame.

    :param image: cv2.UMat object containing RGB frame.
    :return: int denoting sharpness (larger value = sharper)
    """

    return cv2.Laplacian(image, cv2.CV_64FC3).get().var()


def make_smoother(image: cv2.UMat):
    return cv2.medianBlur(src=image, ksize=5, dst=image)


def abs_diff(image_a: cv2.UMat, image_b: cv2.UMat, roi: tuple = None):
    """
        Calculates absolute difference between two RGB frames.
    :param image_a: Image A.
    :param image_b: Image B.
    :param roi: tuple containing coordinates (x1, y1, x2, y2) where x1,y1 is
                the upper-left corner and x2,y2 is bottom-right corner (opt.)
    :return: Per-channel absolute difference between A and B.
    """

    if roi:
        image_a = crop(image_a, roi)
        image_b = crop(image_b, roi)

    return cv2.absdiff(image_a, image_b)


def abs_diff_factor(image_diff: cv2.UMat):
    """
        Takes input from abs_diff and returns a single integer denoting the "diff" factor.
    """
    width, height, channels = image_size(image_diff)

    return sum(cv2.sumElems(image_diff)) / (width * height * channels)


@lru_cache()
def _get_mask(_row, _col, _rows, _cols, _row_size, _col_size):
    block_shape = (_row_size, _col_size)
    grid_blocks = [
        [numpy.zeros(block_shape, numpy.uint8) for _ in range(_cols)]
        for __ in range(_rows)
    ]
    grid_blocks[_row][_col] = numpy.ones(block_shape, numpy.uint8)
    return numpy.block(grid_blocks)


# TODO: GET THIS BELOW 100ms
def grid_diff(image_a: cv2.UMat, image_b: cv2.UMat, rows: int, cols: int, roi: tuple = None):
    """
        Calculates a rows x cols matrix containing positive real values
        signifying absolute differences between grid cells when images are
        divided into rows x cols grid.
    """

    # TODO: avoid cropping
    if roi is not None:
        image_a = crop(image_a, roi)
        image_b = crop(image_b, roi)

    image_diff = abs_diff(image_a, image_b)

    width, height, channels = image_size(image_a)
    row_size = int(height / rows)
    col_size = int(width / cols)

    grid = [[0. for _ in range(cols)] for __ in range(rows)]

    for row in range(rows):
        for col in range(cols):
            mask = _get_mask(row, col, rows, cols, row_size, col_size)
            cell_diff = cv2.mean(image_diff, mask)

            grid[row][col] = cell_diff

    return grid


def grid_diff_factor(grid, threshold: float):
    """
        Takes input from grid_diff (integer matrix that contains cell_diffs)
        and returns the percentage of cells in diff grid that are higher than
        threshold.

        Return value is a real number between 0 and 1.
    """

    return sum(map(lambda s: 1 if s[0] > threshold else 0, reduce(lambda x, y: x + y, grid)))
