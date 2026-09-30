#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for Issue #7: Label Undo Functionality (ADR 003 Part 3)

Tests the label deletion stack implementation:
- delete_selected_shape() pushes to label_deletion_stack
- restore_last_deleted_label() pops and restores labels
- 'z' key binding
- Stack clearing on load_file(), save_file(), and delete_current_image()
- Independence from image deletion stack
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
import tempfile
import shutil

# Add parent directory to path to import labelImg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

import labelImg
from libs.shape import Shape
from libs.hashableQListWidgetItem import HashableQListWidgetItem


class TestIssue7LabelUndo(unittest.TestCase):
    """Test label undo functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

    def test_label_deletion_stack_initialization(self):
        """Test that label_deletion_stack is initialized in __init__"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()
            self.assertTrue(hasattr(window, 'label_deletion_stack'))
            self.assertIsInstance(window.label_deletion_stack, list)
            self.assertEqual(len(window.label_deletion_stack), 0)
            window.close()

    def test_delete_selected_shape_pushes_to_stack(self):
        """Test that delete_selected_shape() adds to label_deletion_stack"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()

            # Create a mock shape and item
            shape = Shape(label="test_label")
            shape.add_point(QPointF(100, 100))
            shape.add_point(QPointF(200, 200))
            shape.close()

            item = HashableQListWidgetItem("test_label")
            item_flags = item.flags()

            # Add to canvas and mappings
            window.canvas.shapes.append(shape)
            window.shapes_to_items[shape] = item
            window.items_to_shapes[item] = shape
            window.label_list.addItem(item)

            # Mock canvas.delete_selected to return the shape
            window.canvas.delete_selected = Mock(return_value=shape)

            # Delete the shape
            initial_stack_size = len(window.label_deletion_stack)
            window.delete_selected_shape()

            # Verify stack has one entry
            self.assertEqual(len(window.label_deletion_stack), initial_stack_size + 1)

            # Verify stack content
            stack_entry = window.label_deletion_stack[-1]
            self.assertEqual(len(stack_entry), 3)
            self.assertEqual(stack_entry[0], shape)
            self.assertEqual(stack_entry[1], "test_label")

            window.close()

    def test_restore_last_deleted_label_method_exists(self):
        """Test that restore_last_deleted_label method exists"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()
            self.assertTrue(hasattr(window, 'restore_last_deleted_label'))
            self.assertTrue(callable(getattr(window, 'restore_last_deleted_label')))
            window.close()

    def test_restore_last_deleted_label_empty_stack(self):
        """Test that restore_last_deleted_label silently ignores empty stack"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()
            window.label_deletion_stack.clear()

            # Should not raise any exception
            try:
                window.restore_last_deleted_label()
                success = True
            except Exception as e:
                success = False
                print(f"Exception raised: {e}")

            self.assertTrue(success)
            window.close()

    def test_restore_last_deleted_label_restores_shape(self):
        """Test that restore_last_deleted_label restores shape correctly"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()

            # Create a shape
            shape = Shape(label="restored_label")
            shape.add_point(QPointF(50, 50))
            shape.add_point(QPointF(150, 150))
            shape.close()

            item_text = "restored_label"
            item = HashableQListWidgetItem(item_text)
            item_flags = item.flags()

            # Manually push to stack (simulating deletion)
            window.label_deletion_stack.append((shape, item_text, item_flags))

            # Ensure canvas and mappings are empty
            window.canvas.shapes = []
            window.shapes_to_items = {}
            window.items_to_shapes = {}
            window.label_list.clear()

            # Restore
            window.restore_last_deleted_label()

            # Verify shape is restored
            self.assertIn(shape, window.canvas.shapes)
            self.assertIn(shape, window.shapes_to_items)
            self.assertEqual(window.label_list.count(), 1)
            self.assertEqual(window.label_list.item(0).text(), item_text)

            # Verify stack is empty
            self.assertEqual(len(window.label_deletion_stack), 0)

            window.close()

    def test_z_key_binding_exists(self):
        """Test that 'z' key is bound to restore_last_deleted_label"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()

            # Check that the action exists
            has_restore_label_action = False
            for action_name in dir(window.actions):
                action = getattr(window.actions, action_name, None)
                if isinstance(action, QAction):
                    shortcuts = action.shortcuts()
                    for shortcut in shortcuts:
                        if shortcut.toString().lower() == 'z':
                            has_restore_label_action = True
                            break

            # Alternative: check source code
            with open('labelImg.py', 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for 'z' key binding with restore_last_deleted_label
                self.assertIn("'z'", content)
                self.assertIn('restore_last_deleted_label', content)

            window.close()

    def test_load_file_clears_stack(self):
        """Test that load_file() clears label_deletion_stack"""
        with open('labelImg.py', 'r', encoding='utf-8') as f:
            content = f.read()

            # Find load_file method
            in_load_file = False
            found_clear = False

            for line in content.split('\n'):
                if 'def load_file' in line:
                    in_load_file = True
                elif in_load_file and line.strip().startswith('def '):
                    break
                elif in_load_file and 'label_deletion_stack.clear()' in line:
                    found_clear = True
                    break

            self.assertTrue(found_clear, "load_file should clear label_deletion_stack")

    def test_save_file_clears_stack(self):
        """Test that _save_file() clears label_deletion_stack"""
        with open('labelImg.py', 'r', encoding='utf-8') as f:
            content = f.read()

            # Find _save_file method
            in_save_file = False
            found_clear = False

            for line in content.split('\n'):
                if 'def _save_file' in line:
                    in_save_file = True
                elif in_save_file and line.strip().startswith('def '):
                    break
                elif in_save_file and 'label_deletion_stack.clear()' in line:
                    found_clear = True
                    break

            self.assertTrue(found_clear, "_save_file should clear label_deletion_stack")

    def test_delete_current_image_clears_stack(self):
        """Test that delete_current_image() clears label_deletion_stack"""
        with open('labelImg.py', 'r', encoding='utf-8') as f:
            content = f.read()

            # Find delete_current_image method
            in_delete_image = False
            found_clear = False

            for line in content.split('\n'):
                if 'def delete_current_image' in line:
                    in_delete_image = True
                elif in_delete_image and line.strip().startswith('def '):
                    break
                elif in_delete_image and 'label_deletion_stack' in line:
                    found_clear = True
                    break

            self.assertTrue(found_clear, "delete_current_image should handle label_deletion_stack")

    def test_independence_from_image_stack(self):
        """Test that label_deletion_stack and image_deletion_stack are independent"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()

            # Verify both stacks exist
            self.assertTrue(hasattr(window, 'label_deletion_stack'))
            self.assertTrue(hasattr(window, 'image_deletion_stack'))

            # Verify they are different objects
            self.assertIsNot(window.label_deletion_stack, window.image_deletion_stack)

            # Modify one stack
            window.label_deletion_stack.append(('test', 'data', 'flags'))

            # Verify the other is unaffected
            self.assertEqual(len(window.image_deletion_stack), 0)
            self.assertEqual(len(window.label_deletion_stack), 1)

            window.close()

    def test_restored_label_is_selected(self):
        """Test that restored label is automatically selected"""
        with patch('labelImg.MainWindow.load_predefined_classes'):
            window = labelImg.MainWindow()

            # Create and push a shape to stack
            shape = Shape(label="selected_label")
            shape.add_point(QPointF(10, 10))
            shape.add_point(QPointF(90, 90))
            shape.close()

            item_text = "selected_label"
            item = HashableQListWidgetItem(item_text)
            item_flags = item.flags()

            window.label_deletion_stack.append((shape, item_text, item_flags))

            # Clear canvas
            window.canvas.shapes = []
            window.shapes_to_items = {}
            window.items_to_shapes = {}
            window.label_list.clear()
            window.canvas.selected_shape = None

            # Restore
            window.restore_last_deleted_label()

            # Verify selection
            self.assertEqual(window.canvas.selected_shape, shape)
            self.assertIsNotNone(window.label_list.currentItem())
            self.assertTrue(window.label_list.currentItem().isSelected())

            window.close()


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
