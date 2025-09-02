"""
日志管理模块
提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime
from typing import Optional


class Logger:
    """
    日志管理类
    提供日志记录功能，支持不同级别的日志输出
    """

    def __init__(self, name: str = "TestFlowManager", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 避免重复添加处理器
        if not self.logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # 创建文件处理器（如果指定了日志文件）
            file_handler = None
            if log_file:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)

            # 创建格式器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 设置格式器
            console_handler.setFormatter(formatter)
            if file_handler:
                file_handler.setFormatter(formatter)

            # 添加处理器
            self.logger.addHandler(console_handler)
            if file_handler:
                self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """记录一般信息"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """记录警告信息"""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """记录错误信息"""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """记录严重错误信息"""
        self.logger.critical(message)


# 创建全局日志实例
logger = Logger("TestFlowManager", "testflow.log")
