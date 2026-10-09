"""Atomic, image-coordinate resizing of axis-aligned rectangles (no Qt needed)."""

from collections import namedtuple
from math import isfinite


class ResizeResult(namedtuple('_ResizeResult', 'status points')):
    __slots__ = ()

    def __new__(cls, status, points=()):
        return super(ResizeResult, cls).__new__(cls, status, tuple(points))

    @property
    def changed(self):
        return self.status == 'ok'


def resize_rectangle(points, delta, bounds):
    """Move all four edges by delta, preserving point order and the center.

    points is a sequence of four (x, y) pairs in perimeter order; bounds is
    (minimum_x, minimum_y, maximum_x, maximum_y). Positive delta expands.
    Rejected operations return no replacement points and never mutate inputs.
    A candidate must fit entirely inside bounds and have width/height >= 1.
    """
    if isinstance(delta, bool) or not isinstance(delta, int) or delta == 0:
        return ResizeResult('invalid_delta')

    try:
        minimum_x, minimum_y, maximum_x, maximum_y = bounds
        if not all(isfinite(v) for v in bounds):
            return ResizeResult('invalid_bounds')
        if minimum_x >= maximum_x or minimum_y >= maximum_y:
            return ResizeResult('invalid_bounds')
    except (TypeError, ValueError, OverflowError):
        return ResizeResult('invalid_bounds')

    try:
        coordinates = tuple((float(x), float(y)) for x, y in points)
        if len(coordinates) != 4 or not all(
                isfinite(v) for point in coordinates for v in point):
            return ResizeResult('invalid_geometry')
        left = min(x for x, y in coordinates)
        top = min(y for x, y in coordinates)
        right = max(x for x, y in coordinates)
        bottom = max(y for x, y in coordinates)
        if left >= right or top >= bottom:
            return ResizeResult('invalid_geometry')
        corners = {(left, top), (right, top), (right, bottom), (left, bottom)}
        if set(coordinates) != corners:
            return ResizeResult('invalid_geometry')
        # Four corners alone also describe a bow-tie; require perimeter order.
        for (x, y), (next_x, next_y) in zip(
                coordinates, coordinates[1:] + coordinates[:1]):
            if (x == next_x) == (y == next_y):
                return ResizeResult('invalid_geometry')

        new_left, new_top = left - delta, top - delta
        new_right, new_bottom = right + delta, bottom + delta
    except (TypeError, ValueError, OverflowError):
        return ResizeResult('invalid_geometry')

    if new_right - new_left < 1 or new_bottom - new_top < 1:
        return ResizeResult('too_small')
    if (new_left < minimum_x or new_top < minimum_y or
            new_right > maximum_x or new_bottom > maximum_y):
        return ResizeResult('out_of_bounds')

    resized = tuple((new_left if x == left else new_right,
                     new_top if y == top else new_bottom)
                    for x, y in coordinates)
    if resized == coordinates:
        return ResizeResult('invalid_delta')
    return ResizeResult('ok', resized)
