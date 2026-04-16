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
        """创建报告"""
        logger.info(
            f"MainWindow._on_create_report - "
            f"controller.project_context={self._main_window.controller.project_context is not None}"
        )

        # 检查是否已打开项目
        if not self._main_window.controller.project_context:
            QMessageBox.warning(
                self._main_window,
                "警告",
                "请先打开一个项目后再创建报告。\n\n操作步骤：\n1. 点击'文件' -> '打开项目'\n2. 选择项目文件夹\n3. 然后再尝试创建报告"
            )
            logger.warning("创建报告失败：项目未打开")
            return

        if self._main_window.controller.project_context:
            logger.info(
                f"MainWindow._on_create_report - "
                f"project_context.project_path={self._main_window.controller.project_context.project_path}"
            )
        logger.debug("Create report action triggered")

        self._main_window._feature_registry.run_create_report(
            self._main_window.controller.project_context,
            self._main_window.controller.get_matrix_controller(),
        )
        self._update_status()

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
