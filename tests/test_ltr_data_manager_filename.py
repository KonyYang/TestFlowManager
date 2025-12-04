"""
测试LTR数据管理器中选中文件名的记录功能
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.ltr_data_manager import LTRDataManager


class TestLTRDataManagerFilename(unittest.TestCase):
    """测试LTR数据管理器中选中文件名的记录功能"""

    def setUp(self):
        """测试前准备"""
        self.ltr_data_manager = LTRDataManager()
        self.test_form_data = {
            'project_type': 'NPD',
            'sample_information': '测试样品',
            'tests_to_be_performed': '功能测试',
            'test_type': 'Partial Qualification',
            'requested_by': '张三',
            'location': '实验室A',
            'project_leader': '李四'
        }

    def test_collect_application_data_with_filename(self):
        """测试收集申请数据时包含文件名"""
        # 准备测试数据
        dl_number = "DL-2025-10-001"
        selected_filename = "test_application.docx"
        
        # 调用方法
        result = self.ltr_data_manager.collect_application_data(
            self.test_form_data, 
            dl_number, 
            selected_filename
        )
        
        # 验证结果
        self.assertEqual(result['DL'], dl_number)
        self.assertEqual(result['selected_filename'], selected_filename)
        self.assertEqual(result['status'], 'new')
        self.assertEqual(result['project_type'], 'NPD')
        self.assertEqual(result['requested_by'], '张三')

    def test_collect_application_data_without_filename(self):
        """测试收集申请数据时不包含文件名"""
        # 准备测试数据
        dl_number = "DL-2025-10-001"
        
        # 调用方法
        result = self.ltr_data_manager.collect_application_data(
            self.test_form_data, 
            dl_number
        )
        
        # 验证结果
        self.assertEqual(result['DL'], dl_number)
        self.assertEqual(result['selected_filename'], '')
        self.assertEqual(result['status'], 'new')
        self.assertEqual(result['project_type'], 'NPD')
        self.assertEqual(result['requested_by'], '张三')

    def test_save_to_project_file_includes_filename(self):
        """测试保存到项目文件时包含文件名"""
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 模拟配置管理器返回临时目录
            with patch('src.utils.ltr_data_manager.config_manager') as mock_config:
                mock_config.get.return_value = temp_dir
                
                # 准备测试数据
                dl_number = "DL-2025-10-001"
                selected_filename = "test_application.docx"
                
                application_data = self.ltr_data_manager.collect_application_data(
                    self.test_form_data,
                    dl_number,
                    selected_filename
                )
                
                # 调用保存方法
                result = self.ltr_data_manager.save_to_project_file(dl_number, application_data)
                
                # 验证保存成功
                self.assertTrue(result)
                
                # 验证文件存在
                project_dir = os.path.join(temp_dir, dl_number)
                json_file_path = os.path.join(project_dir, "application_data.json")
                self.assertTrue(os.path.exists(json_file_path))
                
                # 验证文件内容
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    
                self.assertEqual(saved_data['DL'], dl_number)
                self.assertEqual(saved_data['selected_filename'], selected_filename)
                self.assertEqual(saved_data['project_type'], 'NPD')
                self.assertEqual(saved_data['requested_by'], '张三')


if __name__ == '__main__':
    unittest.main()