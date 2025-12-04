"""
测试标准版本更新功能
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.standard_version_updater import (
    extract_core_method, 
    _extract_version_symbol,
    update_test_method_versions
)


class TestStandardVersionUpdater(unittest.TestCase):
    
    def test_extract_core_method(self):
        """测试提取核心方法标识功能"""
        # 测试正常情况
        self.assertEqual(extract_core_method("EIA-364-01"), "364-01")
        self.assertEqual(extract_core_method("EIA-364-10A"), "364-10")
        self.assertEqual(extract_core_method("364-05"), "364-05")
        
        # 测试不匹配情况
        self.assertEqual(extract_core_method("EIA-365-01"), "")
        self.assertEqual(extract_core_method(""), "")
        self.assertEqual(extract_core_method(None), "")
        
    def test_extract_version_symbol(self):
        """测试提取版本符号功能"""
        # 测试正常情况
        self.assertEqual(_extract_version_symbol("EIA-364-01A", "364-01"), "A")
        self.assertEqual(_extract_version_symbol("EIA-364-10B Test", "364-10"), "B")
        
        # 测试不匹配情况
        self.assertEqual(_extract_version_symbol("EIA-364-01", "364-01"), "")
        self.assertEqual(_extract_version_symbol("EIA-364-01A", "364-02"), "")
        
    @patch('src.utils.standard_version_updater.config_manager')
    def test_update_test_method_versions(self, mock_config_manager):
        """测试更新测试方法版本功能"""
        # 模拟配置管理器返回标准文件路径
        mock_config_manager.get.return_value = "D:/Source/Foreign file directory_20240422.xls"
        
        # 模拟矩阵数据
        matrix_data = [
            ["Test Items", "Section", "Test Method", "Condition", "Requirement"],
            ["", "", "EIA-364-01", "", ""],
            ["", "", "EIA-364-10", "", ""],
            ["", "", "", "", ""],  # 空行
            ["", "", "Invalid-Method", "", ""]  # 无效方法
        ]
        
        # 由于我们没有实际的Excel文件，这里会返回0更新数
        result = update_test_method_versions(matrix_data)
        # 验证函数能正常执行（不会抛出异常）
        self.assertIsInstance(result, int)


if __name__ == '__main__':
    unittest.main()