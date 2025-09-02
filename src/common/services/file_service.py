"""
文件服务模块
提供文件操作相关的服务功能
"""

import os
import shutil
from typing import List, Optional
from src.core.logger import logger


class FileService:
    """
    文件服务类
    提供文件操作相关的服务功能
    """

    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        读取文件内容

        Args:
            file_path: 文件路径
            encoding: 文件编码，默认为utf-8

        Returns:
            文件内容或None（如果读取失败）
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file '{file_path}': {e}")
            return None

    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        写入文件内容

        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 文件编码，默认为utf-8

        Returns:
            是否写入成功
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write file '{file_path}': {e}")
            return False

    @staticmethod
    def copy_file(src_path: str, dst_path: str) -> bool:
        """
        复制文件

        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径

        Returns:
            是否复制成功
        """
        try:
            # 确保目标目录存在
            directory = os.path.dirname(dst_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            logger.error(f"Failed to copy file from '{src_path}' to '{dst_path}': {e}")
            return False

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file '{file_path}': {e}")
            return False

    @staticmethod
    def list_files(directory: str, extension: Optional[str] = None) -> List[str]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            extension: 文件扩展名过滤器（可选），如 '.txt'

        Returns:
            文件路径列表
        """
        try:
            files = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    if extension is None or item.endswith(extension):
                        files.append(item)
            return files
        except Exception as e:
            logger.error(f"Failed to list files in directory '{directory}': {e}")
            return []


# 全局文件服务实例
file_service = FileService()
