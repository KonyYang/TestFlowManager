from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.core.project_session_service import project_session_service
from src.core.project_session_coordinator import ProjectSessionCoordinator
from src.features.main_window.service.project_open_service import ProjectOpenService
from src.features.main_window.view.dialogs.basic_info_dialog import BasicInfoDialog


class ProjectLifecycleCoordinator:
    """组织项目打开 / 创建的业务流"""

    def __init__(
        self,
        view: QWidget,
        status_updater: Callable[[str], None],
        project_open_service: Optional[ProjectOpenService] = None,
    ):
        self.view = view
        self.status_updater = status_updater
        self.project_open_service = project_open_service or ProjectOpenService()
        self._matrix_project_controller = None
        self.project_session_coordinator: Optional[ProjectSessionCoordinator] = None

    def set_matrix_project_controller(self, matrix_project_controller):
        """在 Matrix 装配完成时注入 controller"""
        if self._matrix_project_controller == matrix_project_controller:
            return
        self._matrix_project_controller = matrix_project_controller
        self.project_session_coordinator = ProjectSessionCoordinator(
            self.view,
            matrix_project_controller=self._matrix_project_controller,
            status_updater=self.status_updater,
        )

    def open_project_dialog(self) -> bool:
        """显示文件夹选择并打开项目"""
        default_project_path = self.project_open_service.resolve_default_project_path()
        project_path = QFileDialog.getExistingDirectory(
            self.view,
            "选择项目文件夹",
            default_project_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if not project_path:
            return False

        result = self.project_open_service.prepare_project(project_path)
        if result.created_application_data:
            self._show_basic_info_dialog(result.project_data, result.json_file_path)
            result = self.project_open_service.prepare_project(project_path)

        self.project_session_coordinator_trigger(result.project_context)
        logger.info(f"Project opened successfully: {project_path}")
        return True

    def project_session_coordinator_trigger(self, project_context: ProjectContext, *, status_message: Optional[str] = None, log_message: Optional[str] = None, trigger_matrix_auto_import: bool = False):
        """应用项目上下文并执行状态更新"""
        if not self.project_session_coordinator or not project_context:
            logger.warning("ProjectSessionCoordinator 未就绪或 project_context 无效")
            return
        self.project_session_coordinator.apply_project_context(
            project_context,
            status_message=status_message,
            log_message=log_message,
            trigger_matrix_auto_import=trigger_matrix_auto_import,
        )

    def handle_project_opened_event(self, data: Dict) -> None:
        project_context = ProjectContext.from_event_data(data)
        project_path = project_context.project_path if project_context else data.get("project_path")
        dl_number = project_context.dl_number if project_context else data.get("dl_number")
        if project_path:
            self.project_session_coordinator_trigger(
                project_context,
                status_message=f"当前项目: {dl_number or os.path.basename(project_path)}",
                log_message=f"Project opened successfully: {project_path} with DL number: {dl_number}",
                trigger_matrix_auto_import=True,
            )

    def _show_basic_info_dialog(self, project_data: Dict, json_file_path: str) -> None:
        """在首次打开项目时提示用户补填基础信息"""
        try:
            dialog = BasicInfoDialog(
                project_data,
                self.view,
                project_data_file_path=json_file_path,
            )
            result = dialog.exec_()
            if result == BasicInfoDialog.Accepted:
                modified_data = dialog.get_modified_data()
                with open(json_file_path, "w", encoding="utf-8") as handle:
                    json.dump(modified_data, handle, ensure_ascii=False, indent=4)
                logger.info(f"Updated application_data.json: {json_file_path}")
        except Exception as exc:
            logger.error(f"Failed to show basic info dialog: {exc}")
            QMessageBox.warning(self.view, "错误", f"无法显示更新对话框: {str(exc)}")
