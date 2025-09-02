"""
日志处理工具模块
提供日志处理相关的工具函数
"""

import logging
import os
from datetime import datetime
from typing import Optional
from src.core.logger import logger


class LogHandler:
    """
    日志处理类
    提供日志处理相关的工具函数
    """

    @staticmethod
    def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
        """
        设置日志记录器

        Args:
            name: 日志记录器名称
            log_file: 日志文件路径（可选）
            level: 日志级别

        Returns:
            配置好的日志记录器
        """
        logger_instance = logging.getLogger(name)
        logger_instance.setLevel(level)

        # 避免重复添加处理器
        if not logger_instance.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger_instance.addHandler(console_handler)

            # 如果指定了日志文件，添加文件处理器
            if log_file:
                try:
                    # 确保日志目录存在
                    log_dir = os.path.dirname(log_file)
                    if log_dir and not os.path.exists(log_dir):
                        os.makedirs(log_dir)

                    file_handler = logging.FileHandler(log_file, encoding='utf-8')
                    file_handler.setFormatter(formatter)
                    logger_instance.addHandler(file_handler)
                except Exception as e:
                    logger.error(f"Failed to setup file handler for '{log_file}': {e}")

        return logger_instance

    @staticmethod
    def get_log_filename(prefix: str = "log", extension: str = ".log") -> str:
        """
        生成带时间戳的日志文件名

        Args:
            prefix: 文件名前缀
            extension: 文件扩展名

        Returns:
            日志文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}{extension}"

    @staticmethod
    def clear_log_file(log_file: str) -> bool:
        """
        清空日志文件

        Args:
            log_file: 日志文件路径

        Returns:
            是否清空成功
        """
        try:
            if os.path.exists(log_file):
                with open(log_file, 'w', encoding='utf-8'):
                    pass  # 清空文件内容
            return True
        except Exception as e:
            logger.error(f"Failed to clear log file '{log_file}': {e}")
            return False


def get_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    获取日志记录器的便捷函数

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    return LogHandler.setup_logger(name, log_file, level)
