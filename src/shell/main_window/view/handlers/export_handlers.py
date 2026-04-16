"""
导出操作处理器
处理导出相关的动作
"""

from typing import Any
from PyQt5.QtWidgets import QMessageBox

from src.core.logger import logger


class ExportActionHandlers:
    """导出操作动作处理器"""

    def __init__(self, main_window: Any):
        self._main_window = main_window

    def on_export_matrix(self) -> None:
        """导出Matrix"""
        logger.debug("Export matrix action triggered")
        result = self._main_window.controller.handle_export_matrix_to_excel()
        if result.get("success"):
            self._update_status()
        elif result.get("message"):
            QMessageBox.warning(self._main_window, "错误", result["message"])

    def on_export_llcr(self) -> None:
        """导出LLCR"""
        logger.debug("Export LLCR action triggered")
        if self._main_window.controller.handle_export_llcr():
            self._update_status()

    def on_export_cr(self) -> None:
        """导出CR"""
        logger.debug("Export CR action triggered")
        if self._main_window.controller.handle_export_cr():
            self._update_status()

    def _update_status(self) -> None:
        """更新状态栏"""
        self._main_window._update_status()
