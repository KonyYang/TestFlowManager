"""
主窗口控制器模块
处理主窗口的业务逻辑和事件
"""

from typing import List, Optional
from PyQt5.QtWidgets import QWidget
from src.core.logger import logger
from src.features.main_window.model.main_window_data import MainWindowData
from src.features.main_window.service.main_window_service import MainWindowService


class MainWindowController:
    """
    主窗口控制器类
    处理主窗口的业务逻辑和事件
    """

    def __init__(self, view: QWidget):
        """
        初始化主窗口控制器

        Args:
            view: 主窗口视图实例
        """
        self.view = view
        self.data_model = MainWindowData()
        self.service = MainWindowService(self.data_model)

        # 初始化状态
        self.service.update_status("就绪")

    def initialize(self) -> bool:
        """
        初始化控制器

        Returns:
            初始化是否成功
        """
        try:
            logger.info("Initializing MainWindowController")

            # 加载应用程序状态
            self.service.load_application_state()

            # 加载最近文件列表
            recent_files = self.service.load_recent_files()
            logger.info(f"Loaded {len(recent_files)} recent files")

            logger.info("MainWindowController initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MainWindowController: {e}")
            return False

    def handle_open_file(self, file_path: str) -> bool:
        """
        处理打开文件事件

        Args:
            file_path: 文件路径

        Returns:
            是否处理成功
        """
        try:
            logger.debug(f"Handling open file request: {file_path}")

            # 添加到最近文件列表
            self.service.add_recent_file(file_path)

            # 更新状态
            self.service.update_status(f"已打开文件: {file_path}")

            # TODO: 实际的文件打开逻辑
            logger.info(f"File opened successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to open file '{file_path}': {e}")
            self.service.update_status(f"打开文件失败: {file_path}")
            return False

    def handle_save_file(self, file_path: str) -> bool:
        """
        处理保存文件事件

        Args:
            file_path: 文件路径

        Returns:
            是否处理成功
        """
        try:
            logger.debug(f"Handling save file request: {file_path}")

            # TODO: 实际的文件保存逻辑
            logger.info(f"File saved successfully: {file_path}")

            # 更新状态
            self.service.update_status(f"文件已保存: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save file '{file_path}': {e}")
            self.service.update_status(f"保存文件失败: {file_path}")
            return False

    def handle_new_file(self) -> bool:
        """
        处理新建文件事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("Handling new file request")

            # TODO: 实际的新建文件逻辑
            logger.info("New file created successfully")

            # 更新状态
            self.service.update_status("已创建新文件")
            return True
        except Exception as e:
            logger.error(f"Failed to create new file: {e}")
            self.service.update_status("创建新文件失败")
            return False

    def get_recent_files(self) -> List[str]:
        """
        获取最近打开的文件列表

        Returns:
            文件路径列表
        """
        return self.service.load_recent_files()

    def clear_recent_files(self) -> None:
        """清空最近打开的文件列表"""
        self.service.clear_recent_files()

    def get_status(self) -> str:
        """
        获取当前状态

        Returns:
            当前状态信息
        """
        return self.service.get_status()

    def shutdown(self) -> None:
        """关闭控制器"""
        try:
            logger.info("Shutting down MainWindowController")

            # 保存应用程序状态
            self.service.save_application_state()

            logger.info("MainWindowController shut down successfully")
        except Exception as e:
            logger.error(f"Error during MainWindowController shutdown: {e}")
