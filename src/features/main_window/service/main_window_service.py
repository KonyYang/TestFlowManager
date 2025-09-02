"""
主窗口服务模块
提供主窗口相关的业务逻辑服务
"""

from typing import List, Optional
from src.core.logger import logger
from src.features.main_window.model.main_window_data import MainWindowData


class MainWindowService:
    """
    主窗口服务类
    提供主窗口相关的业务逻辑服务
    """

    def __init__(self, data_model: MainWindowData):
        """
        初始化主窗口服务

        Args:
            data_model: 主窗口数据模型实例
        """
        self.data_model = data_model

    def load_recent_files(self) -> List[str]:
        """
        加载最近打开的文件列表

        Returns:
            文件路径列表
        """
        try:
            recent_files = self.data_model.get_recent_files()
            logger.debug(f"Loaded {len(recent_files)} recent files")
            return recent_files
        except Exception as e:
            logger.error(f"Failed to load recent files: {e}")
            return []

    def add_recent_file(self, file_path: str) -> None:
        """
        添加最近打开的文件

        Args:
            file_path: 文件路径
        """
        try:
            self.data_model.add_recent_file(file_path)
            logger.debug(f"Added recent file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to add recent file '{file_path}': {e}")

    def clear_recent_files(self) -> None:
        """清空最近打开的文件列表"""
        try:
            self.data_model.clear_recent_files()
            logger.debug("Cleared recent files")
        except Exception as e:
            logger.error(f"Failed to clear recent files: {e}")

    def update_status(self, status: str) -> None:
        """
        更新状态信息

        Args:
            status: 状态信息
        """
        try:
            self.data_model.update_status(status)
            logger.debug(f"Updated status: {status}")
        except Exception as e:
            logger.error(f"Failed to update status to '{status}': {e}")

    def get_status(self) -> str:
        """
        获取状态信息

        Returns:
            当前状态信息
        """
        try:
            return self.data_model.get_status()
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return "未知"

    def save_application_state(self) -> bool:
        """
        保存应用程序状态

        Returns:
            是否保存成功
        """
        try:
            # TODO: 实现应用程序状态保存逻辑
            logger.debug("Application state saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save application state: {e}")
            return False

    def load_application_state(self) -> bool:
        """
        加载应用程序状态

        Returns:
            是否加载成功
        """
        try:
            # TODO: 实现应用程序状态加载逻辑
            logger.debug("Application state loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load application state: {e}")
            return False
