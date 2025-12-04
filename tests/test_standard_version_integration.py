"""
测试标准版本更新功能与配置管理器的集成
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.standard_version_updater import update_test_method_versions
from src.core.config_manager import config_manager


class TestStandardVersionIntegration(unittest.TestCase):
    
    @patch('src.utils.standard_version_updater.load_standard_data')
    def test_update_test_method_versions_with_config(self, mock_load_standard_data):
        """测试更新测试方法版本时是否正确使用配置管理器"""
        # 模拟标准数据
        mock_load_standard_data.return_value = {
            "364-01": "EIA-364-01A",
            "364-10": "EIA-364-10B"
        }
        
        # 模拟矩阵数据
        matrix_data = [
            ["Test Items", "Section", "Test Method", "Condition", "Requirement"],
            ["", "", "EIA-364-01", "", ""],
            ["", "", "EIA-364-10", "", ""]
        ]
        
        # 调用更新函数
        result = update_test_method_versions(matrix_data)
        
        # 验证结果
        self.assertEqual(result, 2)  # 应该更新2行
        self.assertEqual(matrix_data[1][2], "EIA-364-01A")  # 第一行应更新为EIA-364-01A
        self.assertEqual(matrix_data[2][2], "EIA-364-10B")  # 第二行应更新为EIA-364-10B
        
        # 验证是否调用了配置管理器获取路径
        standard_file_path = config_manager.get("standard_files.standard_version_info_file")
        self.assertEqual(standard_file_path, "D:\\Source\\Foreign file directory_20240422.xls")


if __name__ == '__main__':
    unittest.main()