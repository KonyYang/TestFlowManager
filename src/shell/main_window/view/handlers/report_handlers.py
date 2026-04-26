"""
报告操作处理器
处理报告创建、更新等动作
"""

from typing import Any
from PyQt5.QtWidgets import QMessageBox

from src.core.logger import logger


class ReportActionHandlers:
    """报告操作动作处理器"""

    def __init__(self, main_window: Any):
        self._main_window = main_window

    def on_create_report(self) -> None:
        """创建报告（切换到报告向导页面）"""
        logger.debug("Create report action triggered")

        # 使用内嵌页面模式
        result = self._main_window.controller.handle_create_report()
        if result and result.get("success"):
            self._update_status()
        # 错误消息已在 handle_create_report 中显示

    def on_update_report(self) -> None:
        """更新报告"""
        logger.debug("Update report action triggered")
        self._main_window._feature_registry.run_update_report(
            self._main_window.controller.project_context
        )
        self._update_status()

    def on_convert_customer_version(self) -> None:
        """转客户版"""
        logger.debug("Convert to customer version action triggered")
        if self._main_window._feature_registry.run_convert_customer_report(
            self._main_window.controller.project_context
        ):
            self._update_status()
        else:
            self._update_status()

    def _update_status(self) -> None:
        """更新状态栏"""
        self._main_window._update_status()
