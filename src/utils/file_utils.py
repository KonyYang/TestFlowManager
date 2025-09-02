"""
文件工具模块
提供文件操作相关的工具函数
"""

import os
import shutil
from typing import List, Optional
from src.core.logger import logger


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名

    Args:
        file_path: 文件路径

    Returns:
        文件扩展名（包括点号），如 ".txt"
    """
    return os.path.splitext(file_path)[1].lower()


def get_file_name_without_extension(file_path: str) -> str:
    """
    获取不带扩展名的文件名

    Args:
        file_path: 文件路径

    Returns:
        不带扩展名的文件名
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def ensure_directory_exists(directory: str) -> bool:
    """
    确保目录存在，如果不存在则创建

    Args:
        directory: 目录路径

    Returns:
        是否成功确保目录存在
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        logger.error(f"Failed to ensure directory exists '{directory}': {e}")
        return False


def get_files_in_directory(directory: str, extension: Optional[str] = None) -> List[str]:
    """
    获取目录中的文件列表

    Args:
        directory: 目录路径
        extension: 文件扩展名过滤器（可选）

    Returns:
        文件路径列表
    """
    try:
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                if extension is None or get_file_extension(item_path) == extension:
                    files.append(item_path)
        return files
    except Exception as e:
        logger.error(f"Failed to get files in directory '{directory}': {e}")
        return []


def copy_directory(src_dir: str, dst_dir: str) -> bool:
    """
    复制目录

    Args:
        src_dir: 源目录路径
        dst_dir: 目标目录路径

    Returns:
        是否复制成功
    """
    try:
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        return True
    except Exception as e:
        logger.error(f"Failed to copy directory from '{src_dir}' to '{dst_dir}': {e}")
        return False


def get_file_size(file_path: str) -> int:
    """
    获取文件大小

    Args:
        file_path: 文件路径

    Returns:
        文件大小（字节），如果文件不存在则返回-1
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Failed to get file size for '{file_path}': {e}")
        return -1
