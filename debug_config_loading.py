"""
调试配置文件加载过程
"""

import sys
import os
import configparser

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.core.config_manager import ConfigManager

def debug_config_loading():
    print("开始调试配置文件加载过程...")
    
    # 创建配置管理器实例
    config_manager = ConfigManager()
    
    # 打印所有配置
    all_config = config_manager.get_all()
    print("所有配置:")
    print(all_config)
    
    # 特别检查标准文件路径配置
    standard_file_path = config_manager.get("standard_files.standard_version_info_file")
    print(f"标准文件路径配置: {standard_file_path}")
    
    # 检查配置文件是否存在
    paths_file = "src/app/config/paths.ini"
    if os.path.exists(paths_file):
        print(f"配置文件 {paths_file} 存在")
        
        # 读取配置文件
        paths_config = configparser.ConfigParser()
        paths_config.read(paths_file, encoding='utf-8')
        
        print("配置文件中的节:")
        print(paths_config.sections())
        
        if 'STANDARD_FILES' in paths_config:
            print("STANDARD_FILES节中的配置项:")
            for key, value in paths_config['STANDARD_FILES'].items():
                print(f"  {key} = {value}")
        else:
            print("未找到STANDARD_FILES节")
    else:
        print(f"配置文件 {paths_file} 不存在")

if __name__ == "__main__":
    debug_config_loading()