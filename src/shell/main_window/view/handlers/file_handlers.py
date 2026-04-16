"""
文件操作处理器
处理文件菜单相关的动作
"""

from typing import Any
from PyQt5.QtWidgets import QMessageBox

from src.core.logger import logger


class FileActionHandlers:
    """文件操作动作处理器"""

    def __init__(self, main_window: Any):
        self._main_window = main_window

    def on_new_file(self) -> None:
        """新建项目"""
        logger.debug("New file action triggered")
        if self._main_window.controller.handle_new_file():
            self._update_status()

    def on_open_project(self) -> None:
        """打开项目"""
        logger.debug("Open project action triggered")
        if self._main_window.controller.handle_open_project():
            self._update_status()

    def on_exit(self) -> None:
        """退出应用"""
        logger.debug("Exit action triggered")
        self._main_window.close()

    def on_view_ltr(self) -> None:
        """查看LTR"""
        logger.debug("View LTR action triggered")
        if self._main_window.controller.handle_view_ltr():
            self._update_status()

    def on_about(self) -> None:
        """关于"""
        logger.debug("About action triggered")
        self._main_window.controller.handle_about()

    def _update_status(self) -> None:
        """更新状态栏"""
        self._main_window._update_status()
