import os
import sys
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from libs.box_geometry import resize_rectangle
from libs.canvas import Canvas
from libs.shape import Shape


class TestResizeRectangle(unittest.TestCase):
    def test_expands_and_preserves_point_order(self):
        points = ((10, 20), (30, 20), (30, 40), (10, 40))
        result = resize_rectangle(points, 1, (0, 0, 100, 100))
        self.assertEqual(result.status, 'ok')
        self.assertEqual(result.points, ((9.0, 19.0), (31.0, 19.0),
                                         (31.0, 41.0), (9.0, 41.0)))

    def test_shrink_rejects_small_box_without_mutating_input(self):
        points = ((10, 10), (11, 10), (11, 20), (10, 20))
        result = resize_rectangle(points, -1, (0, 0, 100, 100))
        self.assertEqual(result.status, 'too_small')
        self.assertEqual(points, ((10, 10), (11, 10), (11, 20), (10, 20)))

    def test_boundary_rejection_is_atomic(self):
        result = resize_rectangle(((0, 10), (20, 10), (20, 20), (0, 20)),
                                  1, (0, 0, 100, 100))
        self.assertEqual(result.status, 'out_of_bounds')
        self.assertFalse(result.points)

    def test_rejects_non_rectangle_and_bow_tie(self):
        self.assertEqual(
            resize_rectangle(((0, 0), (10, 1), (10, 10), (0, 10)),
                              1, (0, 0, 100, 100)).status,
            'invalid_geometry')
        self.assertEqual(
            resize_rectangle(((0, 0), (10, 10), (10, 0), (0, 10)),
                              1, (0, 0, 100, 100)).status,
            'invalid_geometry')

    def test_accepts_reverse_perimeter_order(self):
        result = resize_rectangle(((10, 40), (30, 40), (30, 20), (10, 20)),
                                  2, (0, 0, 100, 100))
        self.assertEqual(result.status, 'ok')
        self.assertEqual(result.points, ((8.0, 42.0), (32.0, 42.0),
                                         (32.0, 18.0), (8.0, 18.0)))

    def test_float_pixels_and_expand_shrink_round_trip(self):
        points = ((20.25, 30.5), (50.25, 30.5), (50.25, 60.5), (20.25, 60.5))
        for step in (1, 5, 100):
            with self.subTest(step=step):
                expanded = resize_rectangle(points, step, (-100, -100, 300, 300))
                self.assertEqual(expanded.status, 'ok')
                restored = resize_rectangle(expanded.points, -step, (-100, -100, 300, 300))
                self.assertEqual(restored.points, points)

    def test_all_borders_and_minimum_dimensions(self):
        for points in (((0, 10), (20, 10), (20, 20), (0, 20)),
                       ((10, 0), (20, 0), (20, 20), (10, 20)),
                       ((80, 10), (100, 10), (100, 20), (80, 20)),
                       ((10, 80), (20, 80), (20, 100), (10, 100)),
                       ((0, 0), (100, 0), (100, 100), (0, 100))):
            with self.subTest(points=points):
                self.assertEqual(resize_rectangle(points, 1, (0, 0, 100, 100)).status,
                                 'out_of_bounds')
        for size in (1, 2, 3):
            points = ((10, 10), (10 + size, 10), (10 + size, 20), (10, 20))
            self.assertEqual(resize_rectangle(points, -1, (0, 0, 100, 100)).status,
                             'ok' if size == 3 else 'too_small')

    def test_invalid_numbers_points_and_delta(self):
        for bad in (float('nan'), float('inf'), float('-inf')):
            self.assertEqual(resize_rectangle(((bad, 1), (4, 1), (4, 4), (1, 4)),
                                              1, (0, 0, 100, 100)).status,
                             'invalid_geometry')
        for points in ((), ((1, 1),), ((1, 1),) * 4):
            self.assertEqual(resize_rectangle(points, 1, (0, 0, 100, 100)).status,
                             'invalid_geometry')
        for delta in (0, True, 1.5, '1', None):
            self.assertEqual(resize_rectangle(((2, 2), (4, 2), (4, 4), (2, 4)),
                                              delta, (0, 0, 100, 100)).status,
                             'invalid_delta')

    def test_invalid_bounds(self):
        points = ((2, 2), (4, 2), (4, 4), (2, 4))
        for bounds in ((0, 0, 0, 100), (0, 0, 100, float('nan')), (0, 100), None):
            self.assertEqual(resize_rectangle(points, 1, bounds).status, 'invalid_bounds')


class TestCanvasResize(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.canvas = Canvas()
        self.canvas.load_pixmap(QPixmap(100, 100))
        shape = Shape(label='object')
        for point in ((20, 20), (40, 20), (40, 40), (20, 40)):
            shape.add_point(QPointF(*point))
        shape.close()
        shape.selected = True
        self.canvas.shapes = [shape]
        self.canvas.selected_shape = shape
        self.moved = 0
        self.canvas.shapeMoved.connect(self._count_move)

    def _count_move(self):
        self.moved += 1

    def test_success_emits_once_and_updates_shape(self):
        result = self.canvas.resize_selected_shape(1, (0, 0, 100, 100))
        self.assertTrue(result.changed)
        self.assertEqual(self.moved, 1)
        self.assertEqual([(p.x(), p.y()) for p in self.canvas.selected_shape.points],
                         [(19.0, 19.0), (41.0, 19.0), (41.0, 41.0), (19.0, 41.0)])

    def test_rejection_does_not_emit_or_change_shape(self):
        before = [(p.x(), p.y()) for p in self.canvas.selected_shape.points]
        result = self.canvas.resize_selected_shape(100, (0, 0, 100, 100))
        self.assertEqual(result.status, 'out_of_bounds')
        self.assertEqual(self.moved, 0)
        self.assertEqual(before, [(p.x(), p.y()) for p in self.canvas.selected_shape.points])

    def test_stale_selection_is_cleared(self):
        stale = self.canvas.selected_shape
        self.canvas.shapes = []
        result = self.canvas.resize_selected_shape(1, (0, 0, 100, 100))
        self.assertEqual(result.status, 'stale_selection')
        self.assertIsNone(self.canvas.selected_shape)
        self.assertFalse(stale.selected)

    def test_visibility_drawing_dragging_and_no_selection(self):
        shape = self.canvas.selected_shape
        self.canvas.set_shape_visible(shape, False)
        self.assertEqual(self.canvas.resize_selected_shape(1, (0, 0, 100, 100)).status,
                         'hidden')
        self.canvas.set_shape_visible(shape, True)
        self.canvas.mode = Canvas.CREATE
        self.assertEqual(self.canvas.resize_selected_shape(1, (0, 0, 100, 100)).status,
                         'invalid_state')
        self.canvas.mode = Canvas.EDIT
        self.canvas.selected_shape_copy = shape.copy()
        self.assertEqual(self.canvas.resize_selected_shape(1, (0, 0, 100, 100)).status,
                         'invalid_state')
        self.canvas.selected_shape_copy = None
        self.canvas.selected_shape = None
        self.assertEqual(self.canvas.resize_selected_shape(1, (0, 0, 100, 100)).status,
                         'no_selection')
        self.assertEqual(self.moved, 0)

    def test_zoom_and_metadata_are_preserved(self):
        shape = self.canvas.selected_shape
        shape.difficult = True
        for scale in (0.5, 1, 2):
            self.canvas.scale = scale
            self.assertTrue(self.canvas.resize_selected_shape(1, (0, 0, 100, 100)).changed)
            self.assertTrue(self.canvas.resize_selected_shape(-1, (0, 0, 100, 100)).changed)
            self.assertEqual([(p.x(), p.y()) for p in shape.points],
                             [(20, 20), (40, 20), (40, 40), (20, 40)])
            self.assertEqual(shape.label, 'object')
            self.assertTrue(shape.difficult)
            self.assertTrue(shape.selected)


if __name__ == '__main__':
    unittest.main()
