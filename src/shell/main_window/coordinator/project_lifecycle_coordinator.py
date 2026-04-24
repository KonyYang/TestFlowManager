from __future__ import annotations

import json
import os
from importlib import import_module
from typing import Any, Callable, Optional

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from src.core.logger import logger


def _load_symbol(module_path: str, symbol_name: str):
    """Load project-lifecycle collaborators lazily without adding static feature import edges."""
    module = import_module(module_path)
    return getattr(module, symbol_name)


class ProjectLifecycleCoordinator:
    """
    项目生命周期的编排器。
    
    职责：
    - UI 交互编排（文件夹选择、对话框）
    - 通过事件系统触发项目打开流程
    - 不直接持有 Matrix 或 ProjectSessionCoordinator 的引用
    """

    def __init__(
        self,
        view: QWidget,
        status_updater: Callable[[str], None],
        project_initialization_service: Optional[Any] = None,
    ):
        self.view = view
        self.status_updater = status_updater
        if project_initialization_service is None:
            ProjectInitializationService = _load_symbol(
                "src.domain.project.project_initialization_service",
                "ProjectInitializationService",
            )
            project_initialization_service = ProjectInitializationService()
        self.project_initialization_service = project_initialization_service

    def handle_open_project(self) -> bool:
        """
        处理打开项目事件 - 项目生命周期的统一入口。

        流程：
        1. 显示文件夹选择对话框
        2. 调用 ProjectOpenService 准备项目
        3. 如需补填信息，显示 ProjectInfoDialog
        4. 通过事件系统派发 project.opened 事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("LifecycleCoordinator: Handling open project request")

            default_project_path = self.project_initialization_service.resolve_default_project_path()

            # 显示文件夹选择对话框
            project_path = QFileDialog.getExistingDirectory(
                self.view,
                "选择项目文件夹",
                default_project_path,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )

            if not project_path:
                return False

            project_result = self.project_initialization_service.prepare_project(project_path)
            if project_result.created_application_data:
                logger.info("LifecycleCoordinator: 显示基本信息对话框供用户确认和编辑")
                self._show_basic_info_dialog(project_result.project_data, project_result.json_file_path)
                project_result = self.project_initialization_service.prepare_project(project_path)

            # 通过统一入口完成项目打开（S1-2: ProjectSessionApplicationService）
            project_session_app_service = _load_symbol(
                "src.app.composition.project_session_application_service",
                "project_session_app_service",
            )
            project_session_app_service.open_project(
                project_path,
                dl_number=project_result.project_context.dl_number,
            )

            logger.info(f"LifecycleCoordinator: Project opened successfully: {project_path}")
            return True

        except Exception as e:
            logger.error(f"LifecycleCoordinator: Failed to open project: {e}")
            QMessageBox.critical(self.view, "错误", f"打开项目失败: {str(e)}")
            if self.status_updater:
                self.status_updater("打开项目失败")
            return False

    def handle_new_file(self) -> bool:
        """
        处理新建项目事件。

        委托给 ProjectCreatorController 执行新建流程。

        Returns:
            是否处理成功
        """
        try:
            logger.debug("LifecycleCoordinator: Handling new file request")

            ProjectCreatorController = _load_symbol(
                "src.features.project_creator.controller.project_creator_controller",
                "ProjectCreatorController",
            )

            # 创建项目创建控制器
            project_creator = ProjectCreatorController(
                self.view,
                matrix_session_registry=None,
                matrix_session_mode="isolated",
                matrix_session_id=None,
            )
            success = project_creator.handle_create_new_project()

            # 清理资源
            project_creator.cleanup()

            return success
        except Exception as e:
            logger.error(f"LifecycleCoordinator: Failed to create new project: {e}")
            QMessageBox.critical(self.view, "错误", f"新建项目失败: {str(e)}")
            if self.status_updater:
                self.status_updater("新建项目失败")
            return False

    def _show_basic_info_dialog(self, project_data: dict, json_file_path: str) -> None:
        """在首次打开项目时提示用户补填基础信息"""
        try:
            ProjectInfoDialog = _load_symbol(
                "src.features.project_creator.view",
                "ProjectInfoDialog",
            )
            dialog = ProjectInfoDialog(
                project_data,
                self.view,
                project_data_file_path=json_file_path,
            )
            result = dialog.exec_()
            if result == ProjectInfoDialog.Accepted:
                modified_data = dialog.get_modified_data()
                with open(json_file_path, "w", encoding="utf-8") as handle:
                    json.dump(modified_data, handle, ensure_ascii=False, indent=4)
                logger.info(f"Updated application_data.json: {json_file_path}")
        except Exception as exc:
            logger.error(f"Failed to show basic info dialog: {exc}")
            QMessageBox.warning(self.view, "错误", f"无法显示更新对话框: {str(exc)}")
