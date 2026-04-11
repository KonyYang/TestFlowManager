import os
from typing import Optional

from PyQt5.QtCore import QTimer

from src.core.logger import logger
from src.core.project_context import ProjectContext


class ProjectSessionCoordinator:
    """统一编排项目会话建立后的跨模块副作用。"""

    def __init__(self, view, matrix_project_controller=None, status_updater=None):
        self.view = view
        self.matrix_project_controller = matrix_project_controller
        self.status_updater = status_updater

    def apply_project_context(
        self,
        project_context: ProjectContext,
        *,
        status_message: Optional[str] = None,
        log_message: Optional[str] = None,
        trigger_matrix_auto_import: bool = False,
    ) -> None:
        project_label = project_context.dl_number or os.path.basename(project_context.project_path)

        if status_message and self.status_updater:
            self.status_updater(status_message)

        if self.view:
            self.view.setWindowTitle(f"TestFlow Manager - 项目: {project_label}")
            if hasattr(self.view, "update_dl_number_display"):
                self.view.update_dl_number_display(project_context.dl_number)

        matrix_controller = None
        if self.matrix_project_controller:
            matrix_controller = getattr(self.matrix_project_controller, "matrix_controller", None)

        if matrix_controller:
            matrix_controller.set_project_context(project_context)
            if project_context.dl_number:
                matrix_controller.set_ltr_number(project_context.dl_number)
                logger.debug(f"Set LTR number {project_context.dl_number} to Matrix controller")

        if self.view and hasattr(self.view, "set_matrix_project_context"):
            self.view.set_matrix_project_context(project_context)

        if self.view and hasattr(self.view, "report_updater_controller"):
            self.view.report_updater_controller.set_project_context(project_context)

        if trigger_matrix_auto_import:
            QTimer.singleShot(0, self._trigger_matrix_workspace_refresh)

        if log_message:
            logger.info(log_message)

    def _trigger_matrix_workspace_refresh(self) -> None:
        try:
            if self.view and hasattr(self.view, "auto_import_from_project") and self.view.has_matrix_workspace():
                self.view.auto_import_from_project()
                logger.debug("Triggered auto import of matrix.xlsx in MainWindow")
        except Exception as exc:
            logger.error(f"Failed to trigger matrix auto import: {exc}")

        QTimer.singleShot(50, self._update_matrix_display)
        QTimer.singleShot(100, self._activate_matrix_workspace)

    def _update_matrix_display(self) -> None:
        try:
            if self.view and hasattr(self.view, "refresh_table") and self.view.has_matrix_workspace():
                self.view.refresh_table()
                logger.debug("Successfully updated Matrix table display")
        except Exception as exc:
            logger.error(f"Failed to update Matrix display: {exc}")

    def _activate_matrix_workspace(self) -> None:
        try:
            if self.view and hasattr(self.view, "activate_matrix_workspace"):
                if self.view.activate_matrix_workspace():
                    logger.debug("Switched to Matrix editor workspace")
        except Exception as exc:
            logger.error(f"Failed to switch to Matrix page: {exc}")
