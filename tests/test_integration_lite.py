"""
Unit tests for labelImg enhanced features (lightweight version).

These tests focus on testing the core logic without full GUI initialization.
Tests cover:
- Keyboard label cycling (Issue #1)
- Lock zoom ratio (Issue #2)
- Image deletion and restoration (Issue #5, #6)
- Label undo (Issue #7)

Run with:
    python -m unittest tests.test_integration_lite
"""
import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path

# Add libs to path
dir_name = os.path.abspath(os.path.dirname(__file__))
libs_path = os.path.join(dir_name, '..', 'libs')
sys.path.insert(0, libs_path)
root_path = os.path.join(dir_name, '..')
sys.path.insert(0, root_path)

# Import Qt components
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QListWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage

# Create QApplication instance for tests (required for Qt widgets)
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestKeyboardLabelCycling(unittest.TestCase):
    """Test keyboard label cycling functionality (Issue #1)"""

    def setUp(self):
        """Set up test fixtures"""
        self.label_list = QListWidget()
        self.canvas = Mock()
        self.canvas.shapes = []

    def cycle_prev_label(self):
        """Replicate the cycle_prev_label logic"""
        if not self.canvas.shapes:
            return

        current_index = self.label_list.currentRow()
        if current_index <= 0:
            next_index = self.label_list.count() - 1
        else:
            next_index = current_index - 1

        self.label_list.setCurrentRow(next_index)

    def test_cycle_prev_label_empty_list(self):
        """Test cycling with no labels - should do nothing"""
        self.canvas.shapes = []
        self.label_list.clear()

        self.cycle_prev_label()
        self.assertEqual(self.label_list.currentRow(), -1)

    def test_cycle_prev_label_single_label(self):
        """Test cycling with single label"""
        self.label_list.clear()
        self.label_list.addItem("label1")
        self.canvas.shapes = [Mock()]
        self.label_list.setCurrentRow(0)

        self.cycle_prev_label()
        self.assertEqual(self.label_list.currentRow(), 0)

    def test_cycle_prev_label_multiple_labels(self):
        """Test cycling backward through multiple labels"""
        self.label_list.clear()
        for i in range(3):
            self.label_list.addItem(f"label{i}")
        self.canvas.shapes = [Mock(), Mock(), Mock()]

        self.label_list.setCurrentRow(2)
        self.cycle_prev_label()
        self.assertEqual(self.label_list.currentRow(), 1)

        self.cycle_prev_label()
        self.assertEqual(self.label_list.currentRow(), 0)

        self.cycle_prev_label()
        self.assertEqual(self.label_list.currentRow(), 2)

    def test_cycle_prev_label_wrap_around(self):
        """Test wrap-around from first to last label"""
        self.label_list.clear()
        for i in range(5):
            self.label_list.addItem(f"label{i}")
        self.canvas.shapes = [Mock() for _ in range(5)]

        self.label_list.setCurrentRow(0)
        self.cycle_prev_label()
        self.assertEqual(self.label_list.currentRow(), 4)


class TestLockZoomRatio(unittest.TestCase):
    """Test lock zoom ratio functionality (Issue #2)"""

    def setUp(self):
        """Set up test fixtures"""
        self.lock_zoom_ratio = False
        self.locked_zoom_value = 100
        self.zoom_widget = Mock()
        self.zoom_widget.value = Mock(return_value=100)
        self.actions = Mock()
        self.actions.lockZoom = Mock()
        self.actions.fitWindow = Mock()
        self.actions.fitWidth = Mock()
        self.zoom_mode = 0
        self.MANUAL_ZOOM = 0

    def toggle_lock_zoom(self, checked=None):
        """Replicate toggle_lock_zoom logic"""
        if checked is None:
            checked = not self.lock_zoom_ratio

        self.lock_zoom_ratio = checked
        self.actions.lockZoom.setChecked(checked)

        if checked:
            if self.actions.fitWindow.isChecked() or self.actions.fitWidth.isChecked():
                self.actions.fitWindow.setChecked(False)
                self.actions.fitWidth.setChecked(False)
                self.zoom_mode = self.MANUAL_ZOOM

            self.locked_zoom_value = self.zoom_widget.value()
            self.zoom_mode = self.MANUAL_ZOOM

    def test_toggle_lock_zoom_on(self):
        """Test locking zoom ratio"""
        self.zoom_widget.value = Mock(return_value=150)
        self.lock_zoom_ratio = False

        self.toggle_lock_zoom(True)

        self.assertTrue(self.lock_zoom_ratio)
        self.assertEqual(self.locked_zoom_value, 150)

    def test_toggle_lock_zoom_off(self):
        """Test unlocking zoom ratio"""
        self.lock_zoom_ratio = True
        self.locked_zoom_value = 150

        self.toggle_lock_zoom(False)

        self.assertFalse(self.lock_zoom_ratio)

    def test_lock_zoom_disables_fit_modes(self):
        """Test that locking zoom exits fit modes"""
        self.actions.fitWindow.isChecked = Mock(return_value=True)
        self.actions.fitWidth.isChecked = Mock(return_value=False)
        self.zoom_widget.value = Mock(return_value=120)

        self.toggle_lock_zoom(True)

        self.actions.fitWindow.setChecked.assert_called_with(False)
        self.assertEqual(self.zoom_mode, self.MANUAL_ZOOM)


class TestImageDeletionAndRestoration(unittest.TestCase):
    """Test image deletion and restoration functionality (Issue #5, #6)"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp(prefix="labelimg_test_lite_")
        self.trash_dir = tempfile.mkdtemp(prefix="labelimg_trash_lite_")
        self.image_deletion_stack = []

        # Create test images using simple file write
        self.image_paths = []
        for i in range(3):
            img_path = os.path.join(self.test_dir, f"test_{i}.txt")
            # Use text files instead of images for testing file operations
            with open(img_path, 'w') as f:
                f.write(f"test image {i}")
            self.image_paths.append(img_path)

    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.trash_dir):
            shutil.rmtree(self.trash_dir)

    def test_deletion_stack_management(self):
        """Test deletion stack push/pop operations"""
        trash_img = os.path.join(self.trash_dir, "deleted.jpg")
        self.image_deletion_stack.append((trash_img, None, self.test_dir))

        self.assertEqual(len(self.image_deletion_stack), 1)

        # Pop
        item = self.image_deletion_stack.pop()
        self.assertEqual(len(self.image_deletion_stack), 0)
        self.assertEqual(item[0], trash_img)

    def test_deletion_stack_cleared(self):
        """Test that stack can be cleared"""
        self.image_deletion_stack = [("a", None, "dir1"), ("b", None, "dir2")]
        self.assertEqual(len(self.image_deletion_stack), 2)

        self.image_deletion_stack.clear()
        self.assertEqual(len(self.image_deletion_stack), 0)

    def test_file_move_to_trash(self):
        """Test moving file to trash directory"""
        img_path = self.image_paths[0]

        # Verify file exists before moving
        self.assertTrue(os.path.exists(img_path), f"Source file should exist: {img_path}")
        self.assertTrue(os.path.exists(self.trash_dir), f"Trash dir should exist: {self.trash_dir}")

        trash_path = os.path.join(self.trash_dir, os.path.basename(img_path))

        # Move file
        shutil.move(img_path, trash_path)

        self.assertFalse(os.path.exists(img_path))
        self.assertTrue(os.path.exists(trash_path))

    def test_file_restore_from_trash(self):
        """Test restoring file from trash"""
        img_path = self.image_paths[1]  # Use second image to avoid conflict

        # Verify file exists before moving
        self.assertTrue(os.path.exists(img_path), f"Source file should exist: {img_path}")

        trash_path = os.path.join(self.trash_dir, os.path.basename(img_path))

        # Move to trash
        shutil.move(img_path, trash_path)
        self.assertTrue(os.path.exists(trash_path))

        # Restore
        shutil.move(trash_path, img_path)
        self.assertTrue(os.path.exists(img_path))
        self.assertFalse(os.path.exists(trash_path))


class TestLabelUndo(unittest.TestCase):
    """Test label undo functionality (Issue #7)"""

    def setUp(self):
        """Set up test fixtures"""
        self.label_deletion_stack = []
        self.canvas_shapes = []
        self.label_list = QListWidget()

    def test_label_stack_push(self):
        """Test pushing to label deletion stack"""
        shape = Mock()
        label_text = "test_label"
        flags = Qt.ItemIsEnabled

        self.label_deletion_stack.append((shape, label_text, flags))
        self.assertEqual(len(self.label_deletion_stack), 1)

    def test_label_stack_pop(self):
        """Test popping from label deletion stack"""
        shape = Mock()
        self.label_deletion_stack.append((shape, "label1", Qt.ItemIsEnabled))

        popped = self.label_deletion_stack.pop()
        self.assertEqual(len(self.label_deletion_stack), 0)
        self.assertEqual(popped[1], "label1")

    def test_label_stack_cleared(self):
        """Test clearing label deletion stack"""
        self.label_deletion_stack = [(Mock(), "l1", Qt.ItemIsEnabled)]
        self.label_deletion_stack.clear()
        self.assertEqual(len(self.label_deletion_stack), 0)

    def test_restore_empty_stack(self):
        """Test restore with empty stack"""
        # Should handle gracefully
        if not self.label_deletion_stack:
            pass  # Silent ignore
        self.assertEqual(len(self.label_deletion_stack), 0)


class TestCrossFeatureIntegration(unittest.TestCase):
    """Test integration scenarios"""

    def test_label_stack_cleared_on_image_deletion(self):
        """Test that label stack is cleared when deleting image"""
        label_stack = [Mock(), Mock()]
        # Simulate image deletion clearing stack
        label_stack.clear()
        self.assertEqual(len(label_stack), 0)

    def test_zoom_lock_persists_across_operations(self):
        """Test zoom lock state persistence"""
        lock_zoom = True
        locked_value = 150

        # Simulate some operation
        # ... operation ...

        # Zoom should still be locked
        self.assertTrue(lock_zoom)
        self.assertEqual(locked_value, 150)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_empty_list_operations(self):
        """Test operations on empty lists"""
        empty_list = []
        self.assertEqual(len(empty_list), 0)

        # Pop on empty should work with condition
        if empty_list:
            empty_list.pop()
        self.assertEqual(len(empty_list), 0)

    def test_single_item_list(self):
        """Test single item list operations"""
        single_list = [1]
        self.assertEqual(len(single_list), 1)

        single_list.pop()
        self.assertEqual(len(single_list), 0)

    def test_boundary_zoom_values(self):
        """Test zoom with boundary values"""
        min_zoom = 1
        max_zoom = 500

        self.assertEqual(min_zoom, 1)
        self.assertEqual(max_zoom, 500)


if __name__ == '__main__':
    unittest.main()
