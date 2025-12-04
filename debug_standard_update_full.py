"""
调试标准版本更新功能的完整流程
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.utils.standard_version_updater import update_test_method_versions
from src.core.config_manager import ConfigManager


def debug_standard_update_full():
    print("开始调试标准版本更新功能的完整流程...")
    
    # 创建配置管理器实例
    config_manager = ConfigManager()
    
    # 检查配置
    standard_file_path = config_manager.get("standard_files.standard_version_info_file")
    print(f"标准文件路径配置: {standard_file_path}")
    
    # 打印所有配置
    all_config = config_manager.get_all()
    print(f"当前所有配置: {all_config}")
    
    # 模拟Matrix数据
    matrix_data = [
        ["Test Items", "Section", "Test Method", "Condition", "Requirement"],
        ["", "", "EIA-364-18", "", ""],
        ["", "", "EIA-364-23", "", ""],
        ["", "", "EIA-364-06", "", ""]
    ]
    
    print("调用update_test_method_versions函数...")
    result = update_test_method_versions(matrix_data)
    
    print(f"更新结果: {result}")
    print("更新后的矩阵数据:")
    for i, row in enumerate(matrix_data):
        print(f"  第{i}行: {row}")

if __name__ == "__main__":
    debug_standard_update_full()