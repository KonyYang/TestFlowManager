"""
检查标准文件内容的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.core.config_manager import config_manager
import pandas as pd

def check_standard_file():
    print("开始检查标准文件...")
    
    # 从配置管理器获取标准文件路径和工作表名称
    standard_file_path = config_manager.get("standard_files.standard_version_info_file")
    sheet_name = config_manager.get("standard_files.standard_version_sheet_name", "认可标准")
    
    print(f"标准文件路径: {standard_file_path}")
    print(f"工作表名称: {sheet_name}")
    
    if not standard_file_path or not os.path.exists(standard_file_path):
        print("错误: 标准文件不存在")
        return
    
    try:
        # 读取Excel文件中的指定工作表
        df = pd.read_excel(standard_file_path, sheet_name=sheet_name, header=None)
        print(f"成功读取工作表 '{sheet_name}'")
        print(f"数据形状: {df.shape}")
        
        # 显示前几行数据
        print("\n前10行数据:")
        for index in range(min(10, len(df))):
            if len(df.columns) > 1:
                file_number = df.iloc[index, 1]  # 第2列是文件编号
                print(f"  第{index+1}行: {file_number}")
                
        # 统计包含"364-"的数据行数
        count_364 = 0
        for index in range(2, len(df)):  # 从第3行开始
            if len(df.columns) > 1 and index < len(df):
                file_number = df.iloc[index, 1]  # 第2列是文件编号
                if pd.notna(file_number) and "364-" in str(file_number):
                    count_364 += 1
                    
        print(f"\n包含'364-'的标准数量: {count_364}")
        
    except Exception as e:
        print(f"读取标准文件时出错: {e}")

if __name__ == "__main__":
    check_standard_file()