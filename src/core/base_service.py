"""
基础服务模块
提供服务类的基类和通用功能
"""

import os
import tempfile
import shutil
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from src.core.logger import logger
from src.core.config_manager import config_manager


class BaseService(ABC):
    """
    基础服务类
    提供所有服务类的通用功能，包括日志、异常处理、配置管理等
    """

    def __init__(self, service_name: str):
        """
        初始化基础服务

        Args:
            service_name: 服务名称，用于日志标识
        """
        self.service_name = service_name
        self.logger = logger

    def log_info(self, message: str):
        """记录信息日志"""
        self.logger.info(f"[{self.service_name}] {message}")

    def log_debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(f"[{self.service_name}] {message}")

    def log_warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(f"[{self.service_name}] {message}")

    def log_error(self, message: str):
        """记录错误日志"""
        self.logger.error(f"[{self.service_name}] {message}")

    def handle_processing_error(self, message: str, operation: str = None) -> Exception:
        """
        处理操作错误

        Args:
            message: 错误消息
            operation: 操作名称

        Returns:
            Exception 异常实例
        """
        error_msg = f"[{self.service_name}] {message}"
        self.log_error(message)
        return Exception(error_msg)

    def handle_configuration_error(self, message: str, config_key: str = None) -> Exception:
        """
        处理配置错误

        Args:
            message: 错误消息
            config_key: 配置键名

        Returns:
            Exception 异常实例
        """
        error_msg = f"[{self.service_name}] {message}"
        self.log_error(message)
        return Exception(error_msg)

    def handle_file_operation_error(self, message: str, file_path: str = None) -> Exception:
        """
        处理文件操作错误

        Args:
            message: 错误消息
            file_path: 相关文件路径

        Returns:
            Exception 异常实例
        """
        error_msg = f"[{self.service_name}] {message}"
        self.log_error(message)
        return Exception(error_msg)

    # 配置管理相关功能
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        从配置管理器获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键名，如 "paths.template_dir"）
            default: 默认值

        Returns:
            配置值
        """
        try:
            value = config_manager.get(key, default)
            self.log_debug(f"获取配置 [{key}]: {value}")
            return value
        except Exception as e:
            self.log_error(f"获取配置失败 [{key}]: {e}")
            raise self.handle_configuration_error(f"获取配置失败: {str(e)}", key)

    def get_path_config(self, path_key: str, default_path: str = "") -> str:
        """
        获取路径配置值

        Args:
            path_key: 路径配置键名（如 "template_dir"）
            default_path: 默认路径

        Returns:
            路径配置值
        """
        full_key = f"paths.{path_key}"
        return self.get_config_value(full_key, default_path)

    def get_default_value(self, default_key: str, default_value: str = "") -> str:
        """
        获取默认值配置

        Args:
            default_key: 默认值配置键名（如 "project_leader"）
            default_value: 默认值

        Returns:
            默认值配置
        """
        full_key = f"defaults.{default_key}"
        return self.get_config_value(full_key, default_value)

    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化服务
        每个服务都需要实现自己的初始化逻辑

        Returns:
            是否初始化成功
        """
        pass