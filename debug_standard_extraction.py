import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.utils.standard_version_updater import extract_standard_identifier

def debug_issue():
    """调试为什么还会提取出带有"ANSI/"前缀的结果"""
    print("调试标准提取问题:")
    
    # 模拟实际Excel中的数据
    excel_data = "ANSI/EIA-364-110-2006"
    result = extract_standard_identifier(excel_data)
    print(f"输入: '{excel_data}'")
    print(f"输出: '{result}'")
    print(f"是否还包含ANSI前缀: {'ANSI/' in result}")

if __name__ == "__main__":
    debug_issue()