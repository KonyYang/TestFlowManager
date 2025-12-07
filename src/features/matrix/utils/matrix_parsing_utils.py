"""
Matrix解析工具模块
提供Matrix数据处理中常用的数据解析函数
"""

from typing import List


def find_sample_size_row(matrix_data: List[List[str]]) -> int:
    """
    查找Sample size行索引
    
    Args:
        matrix_data: Matrix数据
        
    Returns:
        Sample size行索引，如果未找到则返回-1
    """
    sample_size_row_index = -1
    
    # 优先查找严格匹配"sample size"的行
    for row_idx, row in enumerate(matrix_data):
        if row_idx == 0:  # 跳过表头行
            continue
        first_col_value = row[0] if len(row) > 0 else ""
        if first_col_value.lower() == "sample size":
            return row_idx
    
    # 如果没有找到严格匹配的，查找包含"sample"关键字且位于末尾几行的行
    # 检查倒数第一、二、三行
    for i in range(1, min(4, len(matrix_data))):  # 检查最多前3行（倒数第1、2、3行）
        row_idx = len(matrix_data) - i
        if row_idx > 0 and row_idx < len(matrix_data):  # 确保不是表头行
            row = matrix_data[row_idx]
            first_col_value = row[0] if len(row) > 0 else ""
            # 检查是否包含"sample"关键字（不区分大小写）
            if "sample" in first_col_value.lower():
                return row_idx
    
    return sample_size_row_index