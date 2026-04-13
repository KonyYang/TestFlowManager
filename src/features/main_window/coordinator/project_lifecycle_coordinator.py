from __future__ import annotations

import json
import os
from typing import Callable, Optional

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.core.project_session_service import project_session_service
from src.features.main_window.service.project_open_service import ProjectOpenService
from src.features.main_window.view.dialogs.basic_info_dialog import BasicInfoDialog


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
        project_open_service: Optional[ProjectOpenService] = None,
    ):
        self.view = view
        self.status_updater = status_updater
        self.project_open_service = project_open_service or ProjectOpenService()

    def handle_open_project(self) -> bool:
        """
        处理打开项目事件 - 项目生命周期的统一入口。

        流程：
        1. 显示文件夹选择对话框
        2. 调用 ProjectOpenService 准备项目
        3. 如需补填信息，显示 BasicInfoDialog
        4. 通过事件系统派发 project.opened 事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("LifecycleCoordinator: Handling open project request")

            default_project_path = self.project_open_service.resolve_default_project_path()

            # 显示文件夹选择对话框
            project_path = QFileDialog.getExistingDirectory(
                self.view,
                "选择项目文件夹",
                default_project_path,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )

            if not project_path:
                return False

            project_result = self.project_open_service.prepare_project(project_path)
            if project_result.created_application_data:
                logger.info("LifecycleCoordinator: 显示基本信息对话框供用户确认和编辑")
                self._show_basic_info_dialog(project_result.project_data, project_result.json_file_path)
                project_result = self.project_open_service.prepare_project(project_path)

            # 通过事件系统派发项目打开事件
            # 项目打开的副作用由事件消费者（MainWindowController）统一处理
            project_session_service.apply_project_context(project_result.project_context)

            logger.info(f"LifecycleCoordinator: Project opened successfully: {project_path}")
            return True

        except Exception as e:
            logger.error(f"LifecycleCoordinator: Failed to open project: {e}")
            QMessageBox.critical(self.view, "错误", f"打开项目失败: {str(e)}")
            if self.status_updater:
                self.status_updater("打开项目失败")
            return False

    def _show_basic_info_dialog(self, project_data: dict, json_file_path: str) -> None:
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
