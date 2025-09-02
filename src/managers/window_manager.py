"""
窗口管理器模块
负责管理应用程序中的各种窗口
"""

from typing import Dict, Optional
from PyQt5.QtWidgets import QMainWindow
from src.core.logger import logger


class WindowManager:
    """
    窗口管理器类
    管理应用程序中的各种窗口实例
    """

    def __init__(self):
        self._windows: Dict[str, QMainWindow] = {}
        self._main_window: Optional[QMainWindow] = None

    def register_window(self, name: str, window: QMainWindow) -> None:
        """
        注册窗口实例

        Args:
            name: 窗口名称
            window: 窗口实例
        """
        self._windows[name] = window
        logger.debug(f"Window '{name}' registered")

    def unregister_window(self, name: str) -> None:
        """
        注销窗口实例

        Args:
            name: 窗口名称
        """
        if name in self._windows:
            del self._windows[name]
            logger.debug(f"Window '{name}' unregistered")

    def get_window(self, name: str) -> Optional[QMainWindow]:
        """
        获取窗口实例

        Args:
            name: 窗口名称

        Returns:
            窗口实例或None
        """
        return self._windows.get(name)

    def show_main_window(self) -> None:
        """显示主窗口"""
        try:
            # 延迟导入以避免循环依赖
            from src.features.main_window.view.main_window_ui import MainWindow

            if not self._main_window:
                self._main_window = MainWindow()
                self.register_window("main", self._main_window)

            self._main_window.show()
            logger.info("Main window shown")

        except Exception as e:
            logger.error(f"Failed to show main window: {e}")

    def close_all_windows(self) -> None:
        """关闭所有窗口"""
        logger.info("Closing all windows")

        # 先关闭主窗口
        if self._main_window:
            self._main_window.close()
            self._main_window = None

        # 关闭其他窗口
        for window in self._windows.values():
            try:
                window.close()
            except Exception as e:
                logger.error(f"Error closing window: {e}")

        self._windows.clear()

    def get_main_window(self) -> Optional[QMainWindow]:
        """
        获取主窗口实例

        Returns:
            主窗口实例或None
        """
        return self._main_window
