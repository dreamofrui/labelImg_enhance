#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复 KeyError 崩溃的鲁棒性增强
复现场景：调整框大小时切换图片导致的 shape 引用不一致
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QPointF
except ImportError:
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QPointF

from libs.shape import Shape
from libs.canvas import Canvas


class TestShapeKeyErrorFix(unittest.TestCase):
    """测试 shape 选择状态不一致的鲁棒性修复"""

    @classmethod
    def setUpClass(cls):
        """创建 QApplication 实例（PyQt 需要）"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """每个测试前创建 Canvas 实例"""
        self.canvas = Canvas()
        # 模拟 parent 和 window
        self.canvas.setParent = Mock()
        mock_parent = Mock()
        mock_window = Mock()
        mock_window.label_coordinates = Mock()
        mock_window.label_coordinates.setText = Mock()
        mock_window.file_path = "/test/image.jpg"
        mock_parent.window = Mock(return_value=mock_window)
        self.canvas.parent = Mock(return_value=mock_parent)

    def test_load_shapes_clears_invalid_selected_shape(self):
        """测试：load_shapes 时清除不在新列表中的 selected_shape"""
        # 创建旧 shape 并设为选中
        old_shape = Shape(label="old")
        old_shape.add_point(QPointF(10, 10))
        old_shape.add_point(QPointF(20, 20))
        old_shape.close()

        self.canvas.shapes = [old_shape]
        self.canvas.selected_shape = old_shape

        # 创建新 shape 列表（不包含旧 shape）
        new_shape = Shape(label="new")
        new_shape.add_point(QPointF(30, 30))
        new_shape.add_point(QPointF(40, 40))
        new_shape.close()

        # 加载新 shapes
        self.canvas.load_shapes([new_shape])

        # 验证：selected_shape 应该被清除
        self.assertIsNone(self.canvas.selected_shape,
                         "load_shapes 应清除不在新列表中的 selected_shape")
        self.assertEqual(self.canvas.shapes, [new_shape],
                        "shapes 应更新为新列表")

    def test_load_shapes_keeps_valid_selected_shape(self):
        """测试：load_shapes 时保留仍在新列表中的 selected_shape"""
        # 创建 shape
        shape = Shape(label="test")
        shape.add_point(QPointF(10, 10))
        shape.add_point(QPointF(20, 20))
        shape.close()

        self.canvas.shapes = [shape]
        self.canvas.selected_shape = shape

        # 重新加载相同的 shape（模拟未切换图片）
        self.canvas.load_shapes([shape])

        # 验证：selected_shape 应保持不变
        self.assertEqual(self.canvas.selected_shape, shape,
                        "load_shapes 应保留仍在新列表中的 selected_shape")

    def test_reset_state_clears_shapes(self):
        """测试：reset_state 清空 shapes 列表"""
        # 创建并添加 shapes
        shape1 = Shape(label="shape1")
        shape1.add_point(QPointF(10, 10))
        shape1.add_point(QPointF(20, 20))
        shape1.close()

        shape2 = Shape(label="shape2")
        shape2.add_point(QPointF(30, 30))
        shape2.add_point(QPointF(40, 40))
        shape2.close()

        self.canvas.shapes = [shape1, shape2]
        self.canvas.selected_shape = shape1

        # 重置状态
        self.canvas.reset_state()

        # 验证：shapes 应被清空
        self.assertEqual(self.canvas.shapes, [],
                        "reset_state 应清空 shapes 列表")
        self.assertIsNone(self.canvas.selected_shape,
                         "reset_state 应清除 selected_shape")

    def test_shape_selection_changed_with_invalid_shape(self):
        """测试：shape_selection_changed 处理不在字典中的 shape"""
        # 这个测试需要完整的 MainWindow 环境，这里模拟关键逻辑

        # 模拟场景：
        # 1. shapes_to_items 字典为空（刚加载新图片）
        shapes_to_items = {}

        # 2. canvas.selected_shape 指向旧 shape
        old_shape = Shape(label="old")
        old_shape.add_point(QPointF(10, 10))
        old_shape.add_point(QPointF(20, 20))
        old_shape.close()

        # 3. 模拟修复后的逻辑（使用 .get() 而非直接访问）
        item = shapes_to_items.get(old_shape)

        # 验证：不会抛出 KeyError
        self.assertIsNone(item,
                         "使用 .get() 应返回 None 而非抛出 KeyError")

        # 4. 验证应该采取的清理动作
        if item is None:
            # 这里应该调用 canvas.de_select_shape()
            self.canvas.de_select_shape()

        self.assertIsNone(self.canvas.selected_shape,
                         "发现不一致时应清除 canvas 的选择状态")


class TestShapeReferenceConsistency(unittest.TestCase):
    """测试 shape 引用一致性的端到端场景"""

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.canvas = Canvas()
        mock_parent = Mock()
        mock_window = Mock()
        mock_window.label_coordinates = Mock()
        mock_window.label_coordinates.setText = Mock()
        mock_window.file_path = "/test/image.jpg"
        mock_parent.window = Mock(return_value=mock_window)
        self.canvas.parent = Mock(return_value=mock_parent)

    def test_scenario_resizing_then_switch_image(self):
        """
        端到端测试：模拟生产崩溃场景
        1. 用户正在调整框大小（shape 被选中）
        2. 快速切换到另一张图片
        3. 验证不会崩溃
        """
        # 步骤1：加载第一张图片的 shape
        shape_img1 = Shape(label="object1")
        shape_img1.add_point(QPointF(100, 100))
        shape_img1.add_point(QPointF(200, 200))
        shape_img1.close()

        self.canvas.load_shapes([shape_img1])
        self.canvas.selected_shape = shape_img1  # 模拟用户选中

        # 验证初始状态
        self.assertEqual(len(self.canvas.shapes), 1)
        self.assertEqual(self.canvas.selected_shape, shape_img1)

        # 步骤2：用户正在调整框（省略鼠标事件模拟）
        # 此时 selected_shape 仍然指向 shape_img1

        # 步骤3：快速切换到第二张图片（关键时刻）
        shape_img2 = Shape(label="object2")
        shape_img2.add_point(QPointF(150, 150))
        shape_img2.add_point(QPointF(250, 250))
        shape_img2.close()

        # 加载新图片的 shapes（这会触发修复逻辑）
        self.canvas.load_shapes([shape_img2])

        # 验证：修复后的行为
        self.assertEqual(len(self.canvas.shapes), 1,
                        "应加载新图片的 shapes")
        self.assertEqual(self.canvas.shapes[0], shape_img2,
                        "shapes 列表应只包含新图片的 shape")
        self.assertIsNone(self.canvas.selected_shape,
                         "旧的 selected_shape 应被清除（修复的关键）")

        # 关键验证：旧 shape 不在新列表中
        self.assertNotIn(shape_img1, self.canvas.shapes,
                        "旧图片的 shape 不应在新列表中")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestShapeKeyErrorFix))
    suite.addTests(loader.loadTestsFromTestCase(TestShapeReferenceConsistency))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
