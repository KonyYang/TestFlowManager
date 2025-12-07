"""
Matrix文本处理工具模块
提供Matrix数据处理中常用的文本处理函数
"""

import re


def clean_step_numbers(step_str: str) -> list:
    """
    清理并提取步骤号，支持各种格式
    
    Args:
        step_str: 原始步骤字符串
        
    Returns:
        清理后的步骤号列表
    """
    if not step_str or not step_str.strip():
        return []
        
    # 保留数字、逗号、空格、星号、括号和字母
    # 先把中文逗号替换为英文逗号
    step_str = step_str.replace('，', ',')
    
    # 提取所有数字（支持带修饰符的数字，如1*、5(a)等）
    # 匹配模式: 数字后面可能跟星号、括号和字母
    pattern = r'(\d+)[*]?(?:$$[a-zA-Z]$$)?'
    matches = re.findall(pattern, step_str)
            
    return matches


def clean_group_name(group_header: str) -> str:
    """
    清理组别名称，去除前后非数字或字母的符号，处理Group前缀
    
    Args:
        group_header: 原始组别表头
        
    Returns:
        清理后的组别名称
    """
    if not group_header or not group_header.strip():
        return ""
        
    # 去除前后空格
    cleaned = group_header.strip()
    
    # 如果以Group开头（不区分大小写），则去除Group前缀
    if cleaned.lower().startswith("group"):
        # 提取Group后的部分
        cleaned = cleaned[5:].strip()  # 去掉"Group"前缀（5个字符）
        
    # 去除前后的非字母数字字符
    # 使用正则表达式提取中间的字母数字组合
    match = re.search(r'[a-zA-Z0-9]+', cleaned)
    if match:
        cleaned = match.group(0)
        
    return cleaned