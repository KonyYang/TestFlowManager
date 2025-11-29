#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Matrix模块测试文件
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修复导入路径问题
from src.features.matrix.model.matrix_data import MatrixData
from src.features.matrix.service.spec.spec_extractor import SpecExtractor
from src.features.matrix.service.matrix_service import MatrixService
from src.features.matrix.service.template.template_filler import TemplateFiller
from src.features.matrix.service.defaults.test_method_defaults import TestMethodDefaults


class TestMatrixModule(unittest.TestCase):
    """Matrix模块测试类"""

    def setUp(self):
        """测试前准备"""
        self.matrix_data = MatrixData()
        self.service = MatrixService()

    def test_matrix_data_initialization(self):
        """测试MatrixData初始化"""
        # 检查表头是否正确初始化
        self.assertEqual(len(self.matrix_data.headers), 7)
        self.assertEqual(self.matrix_data.headers[0], "A")
        self.assertEqual(self.matrix_data.headers[1], "B")
        
        # 检查数据行是否正确初始化
        self.assertEqual(len(self.matrix_data.rows), 5)
        self.assertEqual(self.matrix_data.rows[0][0], "Test Item")
        self.assertEqual(self.matrix_data.rows[1][0], "Visual Examination")

    def test_add_column(self):
        """测试添加列功能"""
        original_column_count = len(self.matrix_data.headers)
        self.matrix_data.add_column()
        self.assertEqual(len(self.matrix_data.headers), original_column_count + 1)

    def test_remove_column(self):
        """测试删除列功能"""
        original_column_count = len(self.matrix_data.headers)
        self.matrix_data.remove_column(1)
        self.assertEqual(len(self.matrix_data.headers), original_column_count - 1)

    def test_add_row(self):
        """测试添加行功能"""
        original_row_count = len(self.matrix_data.rows)
        self.matrix_data.add_row()
        self.assertEqual(len(self.matrix_data.rows), original_row_count + 1)

    def test_remove_row(self):
        """测试删除行功能"""
        original_row_count = len(self.matrix_data.rows)
        self.matrix_data.remove_row(1)
        self.assertEqual(len(self.matrix_data.rows), original_row_count - 1)

    def test_get_cell_value(self):
        """测试获取单元格值功能"""
        # 测试获取已知单元格的值
        value = self.matrix_data.get_cell_value(1, 0)
        self.assertEqual(value, "Visual Examination")

    def test_set_cell_value(self):
        """测试设置单元格值功能"""
        # 设置单元格值
        self.matrix_data.set_cell_value(1, 0, "Updated Value")
        # 验证值是否正确设置
        value = self.matrix_data.get_cell_value(1, 0)
        self.assertEqual(value, "Updated Value")

    def test_spec_extractor_creation(self):
        """测试SpecExtractor创建"""
        # 测试能否成功创建SpecExtractor实例
        extractor = SpecExtractor()
        self.assertIsInstance(extractor, SpecExtractor)


if __name__ == '__main__':
    unittest.main()