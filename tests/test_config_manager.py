"""
测试配置管理器是否能正确读取paths.ini中的所有配置项
"""

import sys
import os
import unittest
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    
    def test_config_loading(self):
        """测试配置管理器是否能正确加载所有配置项"""
        # 创建配置管理器实例
        config_manager = ConfigManager()
        
        # 检查LTR文件路径配置
        ltr_file = config_manager.get("paths.ltr_file")
        self.assertEqual(ltr_file, "D:\\Source\\Office Auto\\TestDocument\\LTR_number.xls")
        
        # 检查密码配置
        ltr_password = config_manager.get("passwords.ltr_password")
        self.assertEqual(ltr_password, "DGLAB")
        
        # 检查默认值配置
        project_leader = config_manager.get("defaults.project_leader")
        self.assertEqual(project_leader, "Even Yang")
        
        # 检查标准文件路径配置
        standard_file = config_manager.get("standard_files.standard_version_info_file")
        self.assertEqual(standard_file, "D:\\Source\\Foreign file directory_20240422.xls")


if __name__ == '__main__':
    unittest.main()