"""Real Qt shortcuts and serialization, with isolated application settings."""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'minimal')

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QImage, QKeyEvent, QPixmap
from PyQt5.QtTest import QTest, QSignalSpy
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit

from labelImg import MainWindow
from libs.constants import SETTING_BOX_RESIZE_STEP
from libs.create_ml_io import CreateMLReader
from libs.labelFile import LabelFileFormat
from libs.pascal_voc_io import PascalVocReader
from libs.settings import Settings
from libs.yolo_io import YoloReader


class TestBoxResizeWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='labelimg_resize_')
        self.addCleanup(self.directory.cleanup)
        self.settings = Settings()
        self.settings.path = os.path.join(self.directory.name, 'settings.pkl')
        self.settings.data = {}
        self.windows = []
        self.settings_patch = patch('labelImg.Settings', return_value=self.settings)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.trash_patch = patch.object(MainWindow, '_init_trash_directory',
                                       return_value=self.directory.name)
        self.trash_patch.start()
        self.addCleanup(self.trash_patch.stop)
        self.win = self.new_window()

    def tearDown(self):
        for window in self.windows:
            window.set_clean()
            window.close()
            window.deleteLater()
        self.app.processEvents()

    def new_window(self):
        window = MainWindow()
        self.windows.append(window)
        window.show()
        window.activateWindow()
        self.app.processEvents()
        return window

    def select_box(self, points=((20, 20), (40, 20), (40, 40), (20, 40))):
        image = QImage(100, 100, QImage.Format_RGB32)
        image.fill(Qt.white)
        self.win.image = self.win.image_data = image
        self.win.label_file = None
        self.win.file_path = os.path.join(self.directory.name, 'image.png')
        image.save(self.win.file_path)
        self.win.canvas.scale = 1  # Qt's existing QSize code expects integer scale.
        self.win.canvas.load_pixmap(QPixmap.fromImage(image))
        self.win.canvas.setEnabled(True)
        self.win.canvas.set_editing(True)
        self.win.load_labels([('object', points, None, None, False)])
        self.win.label_list.setCurrentRow(0)
        self.win.canvas.setFocus()
        self.app.processEvents()
        self.win.set_clean()
        return self.win.canvas.selected_shape

    def coordinates(self):
        return tuple((p.x(), p.y()) for p in self.win.canvas.selected_shape.points)

    def test_brackets_on_canvas_and_label_list_and_auto_repeat(self):
        self.select_box()
        spy = QSignalSpy(self.win.canvas.shapeMoved)
        # The old bare brackets no longer resize; F shrinks and H expands.
        QTest.keyClick(self.win.canvas, Qt.Key_BracketRight)
        QTest.keyClick(self.win.canvas, Qt.Key_BracketLeft)
        self.assertEqual(len(spy), 0)
        self.assertEqual(self.win.actions.expandBox.shortcut().toString(), 'H')
        self.assertEqual(self.win.actions.shrinkBox.shortcut().toString(), 'F')
        QTest.keyClick(self.win.canvas, Qt.Key_H)
        self.assertEqual(self.coordinates(), ((19, 19), (41, 19), (41, 41), (19, 41)))
        self.assertTrue(self.win.dirty)
        self.win.label_list.setFocus()
        self.app.processEvents()
        QTest.keyClick(self.win.label_list, Qt.Key_F)
        self.assertEqual(self.coordinates(), ((20, 20), (40, 20), (40, 40), (20, 40)))
        repeated = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_H,
                             Qt.NoModifier, 'h', True, 1)
        self.app.sendEvent(self.win.label_list, repeated)
        self.assertEqual(len(spy), 2)

    def test_shortcuts_do_not_edit_inputs_or_other_docks(self):
        self.select_box()
        before = self.coordinates()
        editor = QLineEdit(self.win)
        editor.show()
        editor.setFocus()
        self.app.processEvents()
        QTest.keyClick(editor, Qt.Key_H)
        QTest.keyClick(editor, Qt.Key_F)
        self.assertEqual(editor.text(), 'hf')
        self.assertEqual(self.coordinates(), before)
        for widget in (self.win.file_list_widget, self.win.box_resize_step):
            widget.setFocus()
            self.app.processEvents()
            QTest.keyClick(widget, Qt.Key_H)
            QTest.keyClick(widget, Qt.Key_F)
            self.assertEqual(self.coordinates(), before)
        self.assertFalse(self.win.dirty)

    def test_menu_action_and_format_boundary_do_not_mark_failed_change_dirty(self):
        self.select_box(((1, 20), (20, 20), (20, 40), (1, 40)))
        spy = QSignalSpy(self.win.canvas.shapeMoved)
        for label_format in (LabelFileFormat.PASCAL_VOC, LabelFileFormat.YOLO):
            self.win.label_file_format = label_format
            self.win.actions.expandBox.trigger()
            self.assertEqual(self.coordinates()[0], (1, 20))
            self.assertFalse(self.win.dirty)
            self.assertEqual(len(spy), 0)
        self.win.label_file_format = LabelFileFormat.CREATE_ML
        self.win.actions.expandBox.trigger()
        self.assertEqual(self.coordinates()[0], (0, 19))
        self.assertEqual(len(spy), 1)

    def test_step_persists_and_bad_config_falls_back(self):
        self.win.box_resize_step.setValue(5)
        self.assertEqual(self.settings.get(SETTING_BOX_RESIZE_STEP), 5)
        self.settings.save()
        reopened = self.new_window()
        self.assertEqual(reopened.box_resize_step.value(), 5)
        for value in (None, True, '5', 1.5, 0, 101):
            self.settings[SETTING_BOX_RESIZE_STEP] = value
            self.settings.save()
            with self.subTest(value=value):
                self.assertEqual(self.new_window().box_resize_step.value(), 1)

    def test_resize_save_reload_all_formats(self):
        for label_format in LabelFileFormat:
            with self.subTest(label_format=label_format):
                self.win.label_list.clear()
                self.win.items_to_shapes.clear()
                self.win.shapes_to_items.clear()
                self.win.canvas.reset_state()
                self.select_box(((2, 2), (99, 2), (99, 99), (2, 99)))
                self.win.label_file_format = label_format
                self.win.label_file = None
                self.win.label_hist = ['object']
                self.assertTrue(self.win.resize_selected_box(1))
                target = os.path.join(self.directory.name, label_format.name)
                self.assertTrue(self.win.save_labels(target))
                if label_format == LabelFileFormat.PASCAL_VOC:
                    shapes = PascalVocReader(target + '.xml').get_shapes()
                elif label_format == LabelFileFormat.YOLO:
                    shapes = YoloReader(target + '.txt', self.win.image).get_shapes()
                else:
                    shapes = CreateMLReader(target + '.json', self.win.file_path).get_shapes()
                self.assertEqual(shapes[0][0], 'object')
                self.assertEqual(tuple(shapes[0][1]), self.coordinates())

    def test_visibility_actions_recover_after_showing_box(self):
        shape = self.select_box()
        item = self.win.shapes_to_items[shape]
        item.setCheckState(Qt.Unchecked)
        self.assertFalse(self.win.actions.expandBox.isEnabled())
        before = self.coordinates()
        QTest.keyClick(self.win.canvas, Qt.Key_H)
        self.assertEqual(self.coordinates(), before)
        item.setCheckState(Qt.Checked)
        self.assertTrue(self.win.actions.expandBox.isEnabled())
        QTest.keyClick(self.win.canvas, Qt.Key_H)
        self.assertNotEqual(self.coordinates(), before)

    def test_modifiers_keep_zoom_and_brightness_shortcuts(self):
        self.select_box()
        self.win.zoom_widget.blockSignals(True)
        self.win.light_widget.blockSignals(True)
        self.win.actions.zoomOut.setEnabled(True)
        self.win.actions.lightDarken.setEnabled(True)
        before = self.coordinates()
        zoom = self.win.zoom_widget.value()
        brightness = self.win.light_widget.value()
        QTest.keyClick(self.win.canvas, Qt.Key_BracketLeft, Qt.ControlModifier)
        self.assertEqual(self.win.zoom_widget.value(), zoom - 10)
        QTest.keyClick(self.win.canvas, Qt.Key_BracketLeft,
                       Qt.ControlModifier | Qt.ShiftModifier)
        self.assertEqual(self.win.light_widget.value(), brightness - 10)
        self.assertEqual(self.coordinates(), before)
        self.assertFalse(self.win.dirty)

    def test_dialog_and_mouse_drag_do_not_resize(self):
        self.select_box()
        before = self.coordinates()
        dialog = QDialog(self.win)
        dialog.setModal(True)
        editor = QLineEdit(dialog)
        dialog.show()
        editor.setFocus()
        self.app.processEvents()
        QTest.keyClick(editor, Qt.Key_H)
        self.assertEqual(self.coordinates(), before)
        self.assertFalse(self.win.resize_selected_box(1))
        dialog.close()
        self.app.processEvents()
        self.win.canvas.setFocus()
        # Real button state prevents resizing even when the same widget has focus.
        with patch('libs.canvas.QApplication.mouseButtons', return_value=Qt.LeftButton):
            self.assertFalse(self.win.resize_selected_box(1))
        self.assertEqual(self.coordinates(), before)
        self.assertFalse(self.win.dirty)

    def test_image_navigation_auto_saves_resized_box(self):
        old_shape = self.select_box()
        self.win.box_resize_step.setValue(5)
        self.assertTrue(self.win.resize_selected_box(1))
        expected = self.coordinates()
        old_path = self.win.file_path
        next_path = os.path.join(self.directory.name, 'next.png')
        self.win.image.save(next_path)
        self.win.m_img_list = [old_path, next_path]
        self.win.img_count = 2
        self.win.cur_img_idx = 0
        self.win.default_save_dir = self.directory.name
        self.win.auto_saving.setChecked(True)
        self.win.zoom_widget.blockSignals(True)
        self.win.light_widget.blockSignals(True)
        with patch.object(self.win, 'paint_canvas'):
            self.win.open_next_image()
        shapes = PascalVocReader(os.path.splitext(old_path)[0] + '.xml').get_shapes()
        self.assertEqual(tuple(shapes[0][1]), expected)
        self.assertEqual(self.win.file_path, next_path)
        self.assertFalse(self.win.dirty)
        self.assertNotIn(old_shape, self.win.canvas.shapes)
        self.assertFalse(self.win.actions.expandBox.isEnabled())
        self.win.canvas.selected_shape = old_shape
        self.assertFalse(self.win.resize_selected_box(1))
        self.assertIsNone(self.win.canvas.selected_shape)
        self.assertEqual(tuple((p.x(), p.y()) for p in old_shape.points), expected)


if __name__ == '__main__':
    unittest.main()
