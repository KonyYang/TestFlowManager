"""
日志管理模块
提供统一的日志记录功能
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
from src.core.config_manager import config_manager


class Logger:
    """
    日志管理类
    提供日志记录功能，支持不同级别的日志输出
    """

    def __init__(self, name: str = "TestFlowManager", log_file: Optional[str] = None):
        # 禁用根日志记录器的传播，防止重复日志
        logging.getLogger().propagate = False
        logging.getLogger().handlers.clear()
        
        self.logger = logging.getLogger(name)
        
        # 从配置中获取日志级别，默认为INFO
        log_level_str = config_manager.get_logging("level", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # 清除现有的处理器，避免重复日志
        self.logger.handlers.clear()
        
        # 防止日志传播到父级logger
        self.logger.propagate = False
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)  # 使用与logger相同的级别

        # 创建文件处理器（如果指定了日志文件）
        file_handler = None
        if log_file:
            try:
                # 确保日志目录存在
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(log_level)  # 使用与logger相同的级别
            except Exception as e:
                sys.stderr.write(f"无法创建日志文件 {log_file}: {e}\n")
                # 如果无法创建文件处理器，将继续只使用控制台处理器

        # 创建格式器（不包含logger名称，避免重复）
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # 设置格式器
        console_handler.setFormatter(formatter)
        if file_handler:
            file_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(console_handler)
        if file_handler:
            self.logger.addHandler(file_handler)

    def debug(self, message: str, exc_info: bool = False) -> None:
        """记录调试信息"""
        self.logger.debug(message, exc_info=exc_info)

    def info(self, message: str, exc_info: bool = False) -> None:
        """记录一般信息"""
        self.logger.info(message, exc_info=exc_info)

    def warning(self, message: str, exc_info: bool = False) -> None:
        """记录警告信息"""
        self.logger.warning(message, exc_info=exc_info)

    def error(self, message: str, exc_info: bool = False) -> None:
        """记录错误信息"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        """记录严重错误信息"""
        self.logger.critical(message, exc_info=exc_info)


# 创建全局日志实例
# 从配置中获取日志文件路径
# 预期日志位置：{项目根目录}/logs/testflow.log
log_file_path = config_manager.get_logging("file", "testflow.log")

# 如果是相对路径，将其转换为绝对路径
if not os.path.isabs(log_file_path):
    # 获取项目根目录
    # 开发模式：向上三级到达项目根目录
    # 打包模式：使用可执行文件所在目录（非 _MEIPASS，确保日志持久化）
    if getattr(sys, 'frozen', False):
        # 可执行文件模式：日志写到 exe 同级目录
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发模式
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    log_file_path = os.path.join(base_path, log_file_path)

logger = Logger("TestFlowManager", log_file_path)
