"""
FileOperationsFacade - 文件操作统一入口

职责：
- 统一管理文件操作（打开、新建）
- 管理最近文件列表
- 协调 ProjectLifecycleCoordinator 处理项目生命周期

位置：src/features/main_window/integration/file_operations_facade.py
"""

from __future__ import annotations

import os
from typing import List, Optional, TYPE_CHECKING

from src.core.logger import logger
from src.shell.main_window.model.main_window_data import MainWindowData

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget
    from src.features.matrix.workspace.matrix_workspace_facade import MatrixWorkspaceFacade
    from src.shell.main_window.coordinator.project_lifecycle_coordinator import ProjectLifecycleCoordinator


class FileOperationsFacade:
    """
    文件操作统一 Facade

    封装所有文件操作逻辑，提供统一入口：
    - 打开文件（添加最近文件 + 更新状态）
    - 新建文件（委托给 ProjectLifecycleCoordinator）
    - 最近文件管理
    """

    def __init__(
        self,
        parent_view: "QWidget",
        data_model: MainWindowData,
        matrix_facade: Optional["MatrixWorkspaceFacade"] = None,
        lifecycle_coordinator: Optional["ProjectLifecycleCoordinator"] = None,
    ):
        """
        初始化文件操作 Facade

        Args:
            parent_view: 父窗口视图实例
            data_model: 主窗口数据模型（用于最近文件管理）
            matrix_facade: Matrix 工作区 Facade（用于 session 配置）
            lifecycle_coordinator: 生命周期协调器（用于项目打开）
        """
        self._parent_view = parent_view
        self._data_model = data_model
        self._matrix_facade = matrix_facade
        self._lifecycle_coordinator = lifecycle_coordinator

    def set_matrix_facade(self, matrix_facade: "MatrixWorkspaceFacade") -> None:
        """设置 Matrix Facade（延迟注入）"""
        self._matrix_facade = matrix_facade

    def set_lifecycle_coordinator(self, coordinator: "ProjectLifecycleCoordinator") -> None:
        """设置生命周期协调器（延迟注入）"""
        self._lifecycle_coordinator = coordinator

    # =========================================================================
    # 文件操作方法
    # =========================================================================

    def handle_open_file(self, file_path: str) -> bool:
        """
        处理打开文件事件

        统一入口，负责：
        1. 添加到最近文件列表
        2. 更新状态

        Args:
            file_path: 文件路径

        Returns:
            是否处理成功
        """
        try:
            logger.debug(f"FileOperationsFacade: Handling open file request: {file_path}")

            # 添加到最近文件列表
            self._data_model.add_recent_file(file_path)

            # 更新状态
            self._data_model.update_status(f"已打开文件: {file_path}")

            logger.info(f"File opened successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to open file '{file_path}': {e}")
            self._data_model.update_status(f"打开文件失败: {file_path}")
            return False

    def handle_new_file(self) -> bool:
        """
        处理新建文件事件

        统一入口，委托给 ProjectLifecycleCoordinator 处理：
        1. 解析 session 配置
        2. 创建 ProjectCreatorController
        3. 执行新建项目流程
        4. 清理资源

        Returns:
            是否处理成功
        """
        try:
            logger.debug("FileOperationsFacade: Handling new file request")

            # 委托给 lifecycle_coordinator
            if self._lifecycle_coordinator is not None:
                result = self._lifecycle_coordinator.handle_new_file()
                return result

            # Fallback：如果没有 lifecycle_coordinator，使用原有逻辑
            return self._handle_new_file_fallback()
        except Exception as e:
            logger.error(f"Failed to handle new file request: {e}")
            self._data_model.update_status("新建项目失败")
            return False

    def handle_open_project(self) -> bool:
        """
        处理打开项目事件

        统一入口，委托给 ProjectLifecycleCoordinator 处理：
        1. 显示项目选择对话框
        2. 验证项目路径
        3. 触发 project.opened 事件
        4. 协调副作用

        Returns:
            是否处理成功
        """
        if self._lifecycle_coordinator is not None:
            return self._lifecycle_coordinator.handle_open_project()

        logger.warning("FileOperationsFacade: No lifecycle_coordinator configured")
        return False

    # =========================================================================
    # 最近文件管理方法
    # =========================================================================

    def get_recent_files(self) -> List[str]:
        """
        获取最近打开的文件列表

        Returns:
            文件路径列表
        """
        return self._data_model.get_recent_files()

    def clear_recent_files(self) -> None:
        """清空最近打开的文件列表"""
        self._data_model.clear_recent_files()

    # =========================================================================
    # 内部方法
    # =========================================================================

    def _handle_new_file_fallback(self) -> bool:
        """
        Fallback 逻辑：当没有 lifecycle_coordinator 时使用原有逻辑

        此方法保留了原有 MainWindowController.handle_new_file() 的核心逻辑，
        用于渐进式迁移期间的兼容性。
        """
        try:
            from src.features.project_creator.controller.project_creator_controller import (
                ProjectCreatorController,
            )

            # 解析 session 配置
            use_isolated_pilot = False
            session_config = self._resolve_new_file_session_config_fallback()

            # 创建项目创建控制器
            project_creator = ProjectCreatorController(
                self._parent_view,
                matrix_session_registry=(
                    self._matrix_facade.matrix_session_registry
                    if self._matrix_facade
                    else None
                ),
                matrix_session_mode=session_config.mode,
                matrix_session_id=session_config.session_id,
            )
            success = project_creator.handle_create_new_project()

            # 清理资源
            project_creator.cleanup()

            logger.debug(f"FileOperationsFacade: New file handling completed, success: {success}")
            return success
        except Exception as e:
            logger.error(f"FileOperationsFacade: Failed to handle new file (fallback): {e}")
            return False

    def _resolve_new_file_session_config_fallback(self):
        """Fallback：解析新建文件的 session 配置"""

        class SessionConfig:
            def __init__(self, mode: str, session_id: str):
                self.mode = mode
                self.session_id = session_id

        if self._matrix_facade is not None:
            use_isolated_pilot = self._matrix_facade.is_new_file_pilot_enabled(os.environ)
            session_config = self._matrix_facade.resolve_new_file_session_config(
                pilot_enabled=use_isolated_pilot
            )
            return session_config

        # Default fallback
        return SessionConfig(mode="shared", session_id="main:shared")
