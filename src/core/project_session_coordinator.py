import os
from typing import Optional

from PyQt5.QtCore import QTimer

from src.core.logger import logger
from src.core.project_context import ProjectContext


class ProjectSessionCoordinator:
    """
    统一编排项目会话建立后的跨模块副作用。
    
    现在作为 project.opened 事件的独立消费者，
    不依赖 MainWindowController 的直接调用。
    """

    def __init__(self, view, matrix_project_controller=None, status_updater=None):
        self.view = view
        self.matrix_project_controller = matrix_project_controller
        self.status_updater = status_updater
        self._bound = False
        
        # 直接订阅 project.opened 事件
        self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """订阅项目打开事件"""
        if not self._bound:
            from src.core.event_dispatcher import event_dispatcher
            event_dispatcher.subscribe("project.opened", self._on_project_opened)
            self._bound = True
            logger.info("ProjectSessionCoordinator: Subscribed to project.opened")

    def _on_project_opened(self, data: dict) -> None:
        """
        处理项目打开事件 - 作为独立的事件消费者。
        
        Args:
            data: 包含 project_path 和 dl_number 的事件数据
        """
        try:
            project_context = ProjectContext.from_event_data(data)
            if not project_context:
                logger.warning("ProjectSessionCoordinator: Invalid project context in event")
                return
            
            # 执行所有副作用
            self.apply_project_context(
                project_context,
                status_message=f"当前项目: {project_context.dl_number or os.path.basename(project_context.project_path)}",
                log_message=f"Project opened: {project_context.project_path}",
                trigger_matrix_auto_import=True,
            )
        except Exception as e:
            logger.error(f"ProjectSessionCoordinator: Failed to handle project.opened: {e}")

    def cleanup(self) -> None:
        """取消事件订阅"""
        if self._bound:
            from src.core.event_dispatcher import event_dispatcher
            event_dispatcher.unsubscribe("project.opened", self._on_project_opened)
            self._bound = False
            logger.info("ProjectSessionCoordinator: Unsubscribed from project.opened")

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
