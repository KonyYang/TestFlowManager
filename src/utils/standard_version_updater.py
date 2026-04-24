"""
标准版本更新工具模块（协调器版本）

提供从外部标准文件中获取最新版本号并更新测试方法的功能。
重构于 2026-04-24：从 534 行瘦身至约 100 行。

向后兼容：保留所有原有函数接口，内部委托给新的模块化实现。
"""

from typing import Dict, Tuple, List, Any
from .version_comparator import VersionComparator
from .version_loader import VersionLoader
from .version_updater import VersionUpdater


# ============================================================================
# 向后兼容的函数接口（委托给新模块）
# ============================================================================

def extract_core_method(method: str) -> str:
    """
    从测试方法字符串中提取核心方法标识（如 364-xx 部分）
    
    注意：此函数为向后兼容保留，委托给 VersionComparator
    
    Args:
        method: 完整的测试方法字符串
        
    Returns:
        提取到的核心方法标识，如果未找到则返回空字符串
    """
    return VersionComparator.extract_core_method(method)


def extract_version_letter(method: str) -> str:
    """
    从测试方法字符串中提取版本字母
    
    注意：此函数为向后兼容保留，委托给 VersionComparator
    
    Args:
        method: 完整的测试方法字符串
        
    Returns:
        版本字母，如果未找到则返回空字符串
    """
    return VersionComparator.extract_version_letter(method)


def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本字母
    
    注意：此函数为向后兼容保留，委托给 VersionComparator
    
    Args:
        version1: 第一个版本字母
        version2: 第二个版本字母
        
    Returns:
        如果version1 > version2返回1，相等返回0，小于返回-1
    """
    return VersionComparator.compare_versions(version1, version2)


def extract_standard_identifier(full_standard: str) -> str:
    """
    从完整标准号中提取标准标识符（如从"ANSI/EIA-364-18B-2007"提取"EIA-364-18B"）
    
    注意：此函数为向后兼容保留，委托给 VersionComparator
    
    Args:
        full_standard: 完整的标准号字符串
        
    Returns:
        提取的标准标识符
    """
    return VersionComparator.extract_standard_identifier(full_standard)


def is_network_path(file_path: str) -> bool:
    """
    判断文件路径是否为网络路径（UNC路径）
    
    注意：此函数为向后兼容保留，委托给 VersionLoader
    
    Args:
        file_path: 文件路径
        
    Returns:
        如果是网络路径返回True，否则返回False
    """
    return VersionLoader.is_network_path(file_path)


def load_standard_data(file_path: str) -> Tuple[Dict[str, str], bool, bool]:
    """
    从外部Excel文件加载标准数据
    
    注意：此函数为向后兼容保留，委托给 VersionLoader
    
    Args:
        file_path: 标准文件路径
        
    Returns:
        (standards_dict, file_exists, is_network_disconnect)
        - standards_dict: 标准数据字典 {core_method: full_standard}
        - file_exists: 文件是否存在
        - is_network_disconnect: 是否为网络断开
    """
    return VersionLoader.load_standard_data(file_path)


def update_test_method_versions(matrix_data: List[List[str]]) -> Dict[str, Any]:
    """
    更新矩阵数据中的测试方法版本号
    
    注意：此函数为向后兼容保留，委托给 VersionUpdater
    
    Args:
        matrix_data: 矩阵数据，二维列表形式
        
    Returns:
        更新结果字典，包含：
        - updated_count: 更新数量
        - details: 更新详情列表
        - file_exists: 文件是否存在
        - is_network_disconnect: 是否为网络断开
        - standards_loaded: 是否成功加载标准数据
    """
    return VersionUpdater.update_test_method_versions(matrix_data)


# ============================================================================
# 示例用法（保留用于调试）
# ============================================================================

if __name__ == "__main__":
    # 示例数据
    matrix_data = [
        ["Test Items", "Section", "Test Method", "Condition", "Requirement"],
        ["", "", "EIA-364-01", "", ""],
        ["", "", "EIA-364-10", "", ""]
    ]
    
    # 更新版本号
    result = update_test_method_versions(matrix_data)
    from src.core.logger import logger
    logger.info(f"成功更新 {result['updated_count']} 行")
    logger.info("更新后的数据:")
    for row in matrix_data:
        logger.info(row)
