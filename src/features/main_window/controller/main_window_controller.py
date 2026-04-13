"""
主窗口控制器模块
处理主窗口的业务逻辑和事件
"""
import os
import json
from typing import List, Optional
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QFileDialog
from src.core.logger import logger
from src.core.event_dispatcher import event_dispatcher
from src.core.project_session_coordinator import ProjectSessionCoordinator
from src.core.project_session_service import project_session_service
from src.features.ltr_manager.controller.ltr_editor_controller import LTREditorController
from src.features.main_window.model.main_window_data import MainWindowData
from src.features.main_window.service.project_open_service import ProjectOpenService
from src.features.main_window.service.main_window_service import MainWindowService
from src.features.ltr_manager.controller.ltr_viewer_controller import LTRViewerController
from src.features.main_window.view.dialogs.dl_input_dialog import DLInputDialog
from src.features.project_creator.controller.project_creator_controller import ProjectCreatorController
from src.core.project_context import ProjectContext
from src.features.main_window.facade.matrix_workspace_facade import MatrixWorkspaceFacade
from src.features.matrix.service.matrix_session_manager import MatrixSessionManager
from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator
from src.features.matrix.service.matrix_session_debug_facade import MatrixSessionDebugFacade
from src.features.matrix.service.matrix_session_entry_facade import MatrixSessionEntryFacade
from src.features.matrix.service.matrix_session_entry_policy import MatrixSessionEntryPolicyTable


class MainWindowController:
    """
    主窗口控制器类
    处理主窗口的业务逻辑和事件
    """
    DEFAULT_MATRIX_WORKSPACE_SESSION_ID = "main:shared"
    DEFAULT_MATRIX_WORKSPACE_ENTRY = "main"
    MATRIX_MAIN_PAGE_ID = "matrix.main"
    MATRIX_WORKSPACE_SWITCH_REQUESTED_BY = "main_window.matrix_workspace.page_visible"
    MATRIX_WORKSPACE_SWITCHABLE_ENTRIES = (
        "main",
        "new_file_pilot",
        "preview",
        "debug_preview",
    )

    def __init__(
        self,
        view: QWidget,
        matrix_workspace_facade: Optional[MatrixWorkspaceFacade] = None,
    ):
        """
        初始化主窗口控制器

        Args:
            view: 主窗口视图实例
            matrix_workspace_facade: Matrix 工作区协同件
        """
        self.view = view
        self.data_model = MainWindowData()
        self.service = MainWindowService(self.data_model)
        self.project_open_service = ProjectOpenService()

        # 初始化状态
        self.service.update_status("就绪")
        self.ltr_controller = LTRViewerController()
        self.ltr_editor_controller = LTREditorController(
            self.ltr_controller.data_model,
            self.ltr_controller.service
        )
        
        # 初始化当前项目路径
        self._project_context: Optional[ProjectContext] = None

        # 通过 facade 访问所有 Matrix session 对象（私有属性，不对外暴露）
        self._facade = matrix_workspace_facade or MatrixWorkspaceFacade(parent_view=view)
        self._facade.parent_view = view

        # 组装共享 session
        matrix_session = self._facade.assemble_shared_session(
            session_id=self.DEFAULT_MATRIX_WORKSPACE_SESSION_ID,
            entry_name=self.DEFAULT_MATRIX_WORKSPACE_ENTRY,
        )
        self.matrix_project_controller = matrix_session.matrix_project_controller if matrix_session else None

        self.project_session_coordinator = ProjectSessionCoordinator(
            view,
            matrix_project_controller=self.matrix_project_controller,
            status_updater=self.service.update_status,
        )

        # 订阅事件
        event_dispatcher.subscribe("ltr.processing.started", self._on_ltr_processing_started)
        event_dispatcher.subscribe("ltr.processing.completed", self._on_ltr_processing_completed)
        event_dispatcher.subscribe("ltr.processing.failed", self._on_ltr_processing_failed)
        event_dispatcher.subscribe("state.changed", self._on_state_changed)
        event_dispatcher.subscribe("ltr.application.confirmed", self._on_ltr_application_confirmed)
        event_dispatcher.subscribe("ltr.application.processed", self._on_ltr_application_processed)
        event_dispatcher.subscribe("project.opened", self._on_project_opened)

    @staticmethod
    def _is_isolated_matrix_session_pilot_enabled() -> bool:
        """
        Experimental switch for project-creation entry only.
        Default is disabled, which keeps shared behavior unchanged.
        """
        return MatrixSessionEntryFacade.is_new_file_pilot_enabled(os.environ)

    @staticmethod
    def _is_isolated_matrix_preview_pilot_enabled() -> bool:
        """
        Experimental switch for opening a non-default isolated preview session.
        Default is disabled, which keeps shared behavior unchanged.
        """
        return MatrixSessionEntryFacade.is_preview_pilot_enabled(os.environ)

    @staticmethod
    def _is_debug_matrix_command_enabled() -> bool:
        value = os.getenv("TFM_ENABLE_DEBUG_COMMANDS", "")
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _ensure_preview_session_manager(self) -> MatrixSessionManager:
        """通过 facade 获取预览会话管理器"""
        return self._facade.ensure_preview_session_manager()

    def _ensure_matrix_session_orchestrator(self) -> MatrixSessionOrchestrator:
        """通过 facade 获取会话编排器"""
        return self._facade.matrix_session_orchestrator

    def _ensure_matrix_session_debug_facade(self) -> MatrixSessionDebugFacade:
        """通过 facade 获取调试协同件"""
        return self._facade.matrix_session_debug_facade

    def _ensure_matrix_session_entry_facade(self) -> MatrixSessionEntryFacade:
        """通过 facade 获取入口协同件"""
        return self._facade.matrix_session_entry_facade

    def open_isolated_matrix_preview_session(
        self,
        session_id: str,
        *,
        entry_name: str = MatrixSessionEntryPolicyTable.PREVIEW,
    ):
        """
        Non-default controlled entry for future standalone/preview matrix sessions.
        Does not affect default shared mainline behavior.
        """
        if not session_id:
            raise ValueError("session_id is required for isolated matrix preview session")
        facade = self._ensure_matrix_session_debug_facade()
        return facade.open_preview_session(
            session_id,
            entry_name=entry_name,
        )

    def handle_open_isolated_matrix_preview_pilot(self) -> str | None:
        """
        Controlled non-default entry (pilot) for isolated preview session.
        Default is disabled; when enabled it opens a fixed isolated preview session id.
        """
        entry_facade = self._ensure_matrix_session_entry_facade()
        pilot_enabled = self._is_isolated_matrix_preview_pilot_enabled()
        session_id = entry_facade.resolve_preview_pilot_session_id(pilot_enabled=pilot_enabled)
        if not session_id:
            return None
        session = self.open_isolated_matrix_preview_session(
            session_id,
            entry_name=MatrixSessionEntryPolicyTable.PREVIEW,
        )
        matrix_project_controller = getattr(session, "matrix_project_controller", None)
        if matrix_project_controller and hasattr(matrix_project_controller, "open_matrix_workspace"):
            matrix_project_controller.open_matrix_workspace()
        return session_id

    def close_isolated_matrix_preview_session(self, session_id: str) -> bool:
        facade = self._ensure_matrix_session_debug_facade()
        return bool(facade.close_preview_session(session_id))

    def handle_close_isolated_matrix_preview_pilot(self) -> bool:
        """
        Controlled non-default close entry (pilot) for isolated preview session.
        Default is disabled; when enabled it closes the fixed isolated preview session id.

        Close semantics:
        - closes the managed session and clears any page binding via manager lifecycle.
        - best-effort restores active session to the default workspace session id if present.
        - triggers workspace consistency check after close.
        """
        entry_facade = self._ensure_matrix_session_entry_facade()
        pilot_enabled = self._is_isolated_matrix_preview_pilot_enabled()
        session_id = entry_facade.resolve_preview_pilot_session_id(pilot_enabled=pilot_enabled)
        if not session_id:
            return False

        manager = self._ensure_preview_session_manager()
        active_session_id = None
        if hasattr(manager, "get_active_session_id"):
            active_session_id = manager.get_active_session_id()

        closed = self.close_isolated_matrix_preview_session(session_id)
        if not closed:
            return False

        if active_session_id == session_id and hasattr(manager, "activate"):
            manager.activate(self.DEFAULT_MATRIX_WORKSPACE_SESSION_ID)

        self.ensure_matrix_workspace_session_consistency()
        return True

    def debug_open_isolated_matrix_preview_session(self, session_id: Optional[str] = None) -> Optional[str]:
        if not self._is_debug_matrix_command_enabled():
            return None

        facade = self._ensure_matrix_session_debug_facade()
        resolved_session_id, session = facade.open_debug_preview_session(session_id=session_id)

        matrix_project_controller = getattr(session, "matrix_project_controller", None)
        if matrix_project_controller and hasattr(matrix_project_controller, "open_matrix_workspace"):
            matrix_project_controller.open_matrix_workspace()
        self._debug_publish_matrix_session_state("open")

        return resolved_session_id

    def debug_close_isolated_matrix_preview_session(self, session_id: Optional[str] = None) -> bool:
        if not self._is_debug_matrix_command_enabled():
            return False

        facade = self._ensure_matrix_session_debug_facade()
        closed, target_id = facade.close_debug_preview_session(session_id=session_id)
        if not closed or not target_id:
            return False
        self._debug_publish_matrix_session_state("close")
        return True

    def debug_switch_isolated_matrix_preview_session(self, session_id: str) -> bool:
        if not self._is_debug_matrix_command_enabled():
            return False
        facade = self._ensure_matrix_session_debug_facade()
        result = facade.switch_preview_session(session_id)
        if not getattr(result, "success", False):
            reason = getattr(result, "reason", None) or "unknown"
            service = getattr(self, "service", None)
            if service is not None and hasattr(service, "update_status"):
                service.update_status(
                    MatrixSessionDebugCommands.format_switch_failed(reason, session_id)
                )
            return False
        state = self._build_matrix_session_debug_state()
        entry_name = getattr(result, "entry_name", None) or "unknown"
        service = getattr(self, "service", None)
        if service is not None and hasattr(service, "update_status"):
            service.update_status(
                MatrixSessionDebugCommands.format_switch_success(
                    session_id,
                    entry_name,
                    state,
                )
            )
        return True

    def debug_get_matrix_session_state(self) -> Optional[dict]:
        """Returns debug-only matrix session state snapshot."""
        if not self._is_debug_matrix_command_enabled():
            return None
        return self._build_matrix_session_debug_state()

    def get_matrix_workspace_session_binding(self, *, page_id: str = MATRIX_MAIN_PAGE_ID) -> dict:
        """Returns matrix workspace session metadata for page-level binding."""
        manager = self._ensure_preview_session_manager()
        active_session_id = None
        active_entry_name = None
        active_mode = "shared"
        bound_session_id = None
        if hasattr(manager, "snapshot"):
            snapshot = manager.snapshot()
            active_session_id = getattr(snapshot, "active_session_id", None)
            session_modes = dict(getattr(snapshot, "session_modes", {}) or {})
            session_entries = dict(getattr(snapshot, "session_entries", {}) or {})
            page_bindings = dict(getattr(snapshot, "page_session_bindings", {}) or {})
            bound_session_id = page_bindings.get(page_id)
            if bound_session_id:
                return {
                    "session_id": bound_session_id,
                    "entry_name": session_entries.get(bound_session_id) or self.DEFAULT_MATRIX_WORKSPACE_ENTRY,
                    "mode": session_modes.get(bound_session_id, "shared"),
                }
            if active_session_id is not None:
                active_mode = session_modes.get(active_session_id, active_mode)
                active_entry_name = session_entries.get(active_session_id)
        if not active_session_id:
            return {
                "session_id": self.DEFAULT_MATRIX_WORKSPACE_SESSION_ID,
                "entry_name": self.DEFAULT_MATRIX_WORKSPACE_ENTRY,
                "mode": "shared",
            }
        return {
            "session_id": active_session_id,
            "entry_name": active_entry_name or self.DEFAULT_MATRIX_WORKSPACE_ENTRY,
            "mode": active_mode,
        }

    def ensure_matrix_workspace_session_consistency(
        self,
        *,
        page_id: str = MATRIX_MAIN_PAGE_ID,
    ) -> dict:
        """
        Ensures matrix workspace visible page is aligned with active session routing.
        Returns a structured result with rollback semantics from switch contract.
        """
        manager = self._ensure_preview_session_manager()
        active_session_id = None
        bound_session_id = None
        if hasattr(manager, "snapshot"):
            snapshot = manager.snapshot()
            active_session_id = getattr(snapshot, "active_session_id", None)
            page_bindings = dict(getattr(snapshot, "page_session_bindings", {}) or {})
            bound_session_id = page_bindings.get(page_id)
        elif hasattr(manager, "get_active_session_id"):
            active_session_id = manager.get_active_session_id()
            if hasattr(manager, "get_page_session_id"):
                bound_session_id = manager.get_page_session_id(page_id)

        if not bound_session_id:
            if active_session_id and hasattr(manager, "bind_page_session"):
                manager.bind_page_session(page_id, active_session_id)
                return {
                    "success": True,
                    "reason": None,
                    "page_id": page_id,
                    "active_session_id": active_session_id,
                    "bound_session_id": active_session_id,
                    "rollback_performed": False,
                }
            return {
                "success": True,
                "reason": "default_shared_binding",
                "page_id": page_id,
                "active_session_id": active_session_id,
                "bound_session_id": None,
                "rollback_performed": False,
            }

        if bound_session_id == active_session_id:
            return {
                "success": True,
                "reason": None,
                "page_id": page_id,
                "active_session_id": active_session_id,
                "bound_session_id": bound_session_id,
                "rollback_performed": False,
            }

        orchestrator = self._ensure_matrix_session_orchestrator()
        result = orchestrator.bind_page_session(
            page_id,
            bound_session_id,
            expected_entry_names=self.MATRIX_WORKSPACE_SWITCHABLE_ENTRIES,
            requested_by=self.MATRIX_WORKSPACE_SWITCH_REQUESTED_BY,
        )
        return {
            "success": bool(getattr(result, "success", False)),
            "reason": getattr(result, "reason", None),
            "page_id": page_id,
            "active_session_id": getattr(result, "active_session_id", active_session_id),
            "bound_session_id": bound_session_id,
            "rollback_performed": bool(getattr(result, "rollback_performed", False)),
        }

    def handle_matrix_workspace_hidden(self, *, page_id: str = MATRIX_MAIN_PAGE_ID) -> bool:
        """
        Clears page-level session binding when matrix workspace is no longer visible.
        This does not close sessions; it only releases page->session association.
        """
        manager = self._ensure_preview_session_manager()
        if hasattr(manager, "unbind_page_session"):
            return bool(manager.unbind_page_session(page_id))
        return False

    def _build_matrix_session_debug_state(self) -> dict:
        facade = self._ensure_matrix_session_debug_facade()
        registry_snapshot = None
        registry = self._facade.matrix_session_registry
        if registry is not None and hasattr(registry, "snapshot"):
            registry_snapshot = registry.snapshot()
        return facade.get_debug_state(registry_snapshot=registry_snapshot)

    def _debug_publish_matrix_session_state(self, action: str) -> None:
        if not self._is_debug_matrix_command_enabled():
            return
        state = self._build_matrix_session_debug_state()
        status_text = MatrixSessionDebugCommands.format_state_status(action, state)
        logger.info(f"Matrix session debug state: {state}")
        service = getattr(self, "service", None)
        if service is not None and hasattr(service, "update_status"):
            service.update_status(status_text)

    # 添加事件处理方法
    def _on_ltr_processing_started(self, data):
        """处理LTR处理开始事件"""
        file_path = data.get("file_path", "未知文件")
        self.service.update_status(f"正在处理LTR申请单: {os.path.basename(file_path)}")

    def _on_ltr_processing_completed(self, data):
        """处理LTR处理完成事件"""
        file_path = data.get("file_path", "未知文件")
        self.service.update_status(f"LTR申请单处理完成: {os.path.basename(file_path)}")

    def _on_ltr_processing_failed(self, data):
        """处理LTR处理失败事件"""
        file_path = data.get("file_path", "未知文件")
        error = data.get("error", "未知错误")
        self.service.update_status(f"LTR申请单处理失败: {os.path.basename(file_path)}")

    def _on_ltr_application_confirmed(self, data):
        """处理LTR申请单确认事件"""
        dl_number = data.get("dl_number")
        self.service.update_status(f"确认LTR申请单: {dl_number}")

    def _on_ltr_application_processed(self, data):
        """处理LTR申请单处理完成事件"""
        dl_number = data.get("dl_number")
        status = data.get("status")

        logger.debug(f"_on_ltr_application_processed in MainWindowController called with dl_number={dl_number}, status={status}")

        if status == "success":
            self.service.update_status(f"LTR申请单处理完成: {dl_number}")
            # Project-open side effects (title/dl/matrix binding/auto import) must be orchestrated by
            # `project.opened` consumption -> ProjectSessionCoordinator.apply_project_context(...).
        else:
            self.service.update_status(f"LTR申请单处理失败: {dl_number}")

    def _on_project_opened(self, data):
        """处理项目打开事件"""
        project_context = ProjectContext.from_event_data(data)
        project_path = project_context.project_path if project_context else data.get("project_path")
        dl_number = project_context.dl_number if project_context else data.get("dl_number")
        
        logger.debug(f"_on_project_opened called with project_path={project_path}, dl_number={dl_number}")
        
        if project_path:
            if self._matches_project_context(project_path, dl_number):
                return
            self._apply_project_context(
                project_context,
                trigger_matrix_auto_import=True,
                status_message=f"当前项目: {dl_number or os.path.basename(project_path)}",
                log_message=f"Project opened successfully: {project_path} with DL number: {dl_number}",
            )
            return

    def _on_state_changed(self, data):
        """处理状态变更事件。

        项目打开主流程统一由 `project.opened` 事件驱动。
        这里只保留通用状态更新和清理动作，避免重复编排项目打开副作用。
        """
        key = data.get("key")
        new_value = data.get("new_value")

        if key == "current_project_context":
            if not isinstance(new_value, ProjectContext):
                self._project_context = None
            return

        if key == "application_status":
            self.service.update_status(new_value)

    @property
    def project_context(self) -> Optional[ProjectContext]:
        return self._project_context

    @property
    def current_project_path(self) -> Optional[str]:
        if not self._project_context:
            return None
        return self._project_context.project_path

    @property
    def _current_project_path(self) -> Optional[str]:
        """兼容旧调用，真实状态已迁移到 project_context。"""
        return self.current_project_path

    @_current_project_path.setter
    def _current_project_path(self, project_path: Optional[str]) -> None:
        if project_path:
            existing_dl_number = self._project_context.dl_number if self._project_context else None
            self._project_context = self._build_project_context(project_path, existing_dl_number)
        else:
            self._project_context = None

    def _build_project_context(self, project_path: str, dl_number: Optional[str] = None) -> ProjectContext:
        return ProjectContext.from_project_path(project_path, dl_number)

    def _matches_project_context(self, project_path: str, dl_number: Optional[str] = None) -> bool:
        if not self._project_context:
            return False
        normalized_path = os.path.normcase(os.path.normpath(project_path))
        current_path = os.path.normcase(os.path.normpath(self._project_context.project_path))
        return normalized_path == current_path and dl_number == self._project_context.dl_number

    def _apply_project_context(
        self,
        project_context: ProjectContext,
        *,
        trigger_matrix_auto_import: bool = False,
        status_message: Optional[str] = None,
        log_message: Optional[str] = None,
    ) -> None:
        self._project_context = project_context
        self.project_session_coordinator.apply_project_context(
            project_context,
            status_message=status_message,
            log_message=log_message,
            trigger_matrix_auto_import=trigger_matrix_auto_import,
        )

    def initialize(self) -> bool:
        """
        初始化控制器

        Returns:
            初始化是否成功
        """
        try:
            logger.info("Initializing MainWindowController")

            # 加载应用程序状态
            self.service.load_application_state()

            # 加载最近文件列表
            recent_files = self.service.load_recent_files()
            logger.info(f"Loaded {len(recent_files)} recent files")

            logger.info("MainWindowController initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MainWindowController: {e}")
            return False

    def handle_view_ltr(self) -> bool:
        """
        处理查看LTR文件事件

        Returns:
            是否成功打开LTR文件
        """
        try:
            logger.debug("Handling view LTR file request from main window")

            # 显示DL编号输入对话框
            dialog = DLInputDialog(self.view)
            result = dialog.exec_()

            # 如果用户点击取消，则直接返回
            if result != QDialog.Accepted:
                return False

            # 获取用户输入的DL编号
            dl_number = dialog.get_dl_number()

            # 如果用户输入了DL编号，则先验证并处理DL编号查询逻辑
            if dl_number:
                # 调用LTR控制器处理DL编号查询
                result = self.ltr_controller.handle_view_dl_number(dl_number)

                if result["success"]:
                    # 成功找到DL编号，使用LTR编辑器控制器显示编辑对话框并处理更新
                    # 准备数据
                    ltr_data = {
                        'dl_number': dl_number,
                        'data': result['data']
                    }

                    # 使用LTR编辑器控制器打开编辑对话框并处理更新
                    update_success = self.ltr_editor_controller.open_editor_and_update(ltr_data, self.view)

                    if update_success:
                        logger.info(f"成功更新DL编号 {dl_number} 的数据")
                    elif update_success is False:
                        logger.info(f"用户取消了DL编号 {dl_number} 的更新操作")

                    self.service.update_status(f"已定位到DL编号: {dl_number}")
                    logger.info(f"Successfully found and positioned to DL number: {dl_number}")
                    success = True  # 设置成功标志
                else:
                    # 关闭Excel应用程序，因为handle_view_dl_number已经打开了它
                    from src.utils.excel_utils import release_excel_app
                    release_excel_app()
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self.view,
                        "查找结果",
                        f"未找到DL编号: {dl_number}\n错误信息: {result.get('error', '未知错误')}"
                    )
                    self.service.update_status(f"未找到DL编号: {dl_number}")
                    # 重新显示DL编号输入对话框
                    return self.handle_view_ltr()
            else:
                # 用户选择跳过，执行默认的LTR查看逻辑
                success = self.ltr_controller.handle_view_ltr()

            if success:
                if not dl_number:  # 只有在非DL编号查询时才更新状态
                    file_path = self.ltr_controller.get_ltr_file_path()
                    self.service.update_status(f"已处理LTR文件: {file_path}")
                    logger.info(f"LTR file processed successfully from main window: {file_path}")
            else:
                file_path = self.ltr_controller.get_ltr_file_path()
                self.service.update_status(f"处理LTR文件失败: {file_path}")
                logger.error(f"Failed to process LTR file from main window: {file_path}")

            return success
        except Exception as e:
            logger.error(f"Failed to handle view LTR request from main window: {e}")
            self.service.update_status("处理LTR文件时发生错误")
            return False


    def handle_open_file(self, file_path: str) -> bool:
        """
        处理打开文件事件

        Args:
            file_path: 文件路径

        Returns:
            是否处理成功
        """
        try:
            logger.debug(f"Handling open file request: {file_path}")

            # 添加到最近文件列表
            self.service.add_recent_file(file_path)

            # 更新状态
            self.service.update_status(f"已打开文件: {file_path}")

            logger.info(f"File opened successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to open file '{file_path}': {e}")
            self.service.update_status(f"打开文件失败: {file_path}")
            return False

    def handle_new_file(self) -> bool:
        """
        处理新建文件事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("Handling new file request")

            # 创建项目创建控制器并处理新建项目请求
            use_isolated_pilot = self._is_isolated_matrix_session_pilot_enabled()
            entry_facade = self._ensure_matrix_session_entry_facade()
            session_config = entry_facade.resolve_new_file_session_config(
                pilot_enabled=use_isolated_pilot
            )
            project_creator = ProjectCreatorController(
                self.view,
                matrix_session_registry=self._facade.matrix_session_registry,
                matrix_session_mode=session_config.mode,
                matrix_session_id=session_config.session_id,
            )
            success = project_creator.handle_create_new_project()
            
            # 清理资源
            project_creator.cleanup()
            
            logger.debug(f"New file handling completed, success: {success}")
            return success
        except Exception as e:
            logger.error(f"Failed to handle new file request: {e}")
            self.service.update_status("新建项目失败")
            return False

    def handle_open_project(self) -> bool:
        """
        处理打开项目事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("Handling open project request")

            default_project_path = self.project_open_service.resolve_default_project_path()

            # 显示文件夹选择对话框
            project_path = QFileDialog.getExistingDirectory(
                self.view,
                "选择项目文件夹",
                default_project_path,  # 使用配置的默认路径作为初始目录
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )

            if not project_path:  # 用户取消了选择
                return False

            project_result = self.project_open_service.prepare_project(project_path)
            if project_result.created_application_data:
                logger.info("显示基本信息对话框供用户确认和编辑")
                self._show_basic_info_dialog(project_result.project_data, project_result.json_file_path)
                project_result = self.project_open_service.prepare_project(project_path)

            project_session_service.apply_project_context(project_result.project_context)
            logger.info(f"Project opened successfully: {project_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to open project: {e}")
            self.service.update_status("打开项目失败")
            QMessageBox.critical(self.view, "错误", f"打开项目失败: {str(e)}")
            return False

    def _show_basic_info_dialog(self, project_data: dict, json_file_path: str):
        """
        显示项目基本信息对话框用于更新项目信息
        
        Args:
            project_data: 项目数据
            json_file_path: JSON文件路径
        """
        try:
            logger.info("开始显示项目基本信息对话框")
            # 使用项目基本信息对话框来更新项目信息
            from src.features.main_window.view.dialogs.basic_info_dialog import BasicInfoDialog
            
            # 创建并显示对话框
            dialog = BasicInfoDialog(
                project_data,
                self.view,
                project_data_file_path=json_file_path,
            )
            result = dialog.exec_()
            
            # 如果用户确认了更改，保存到JSON文件
            if result == BasicInfoDialog.Accepted:
                modified_data = dialog.get_modified_data()
                logger.info(f"用户确认了修改，准备保存数据到: {json_file_path}")
                
                # 保存到JSON文件
                try:
                    with open(json_file_path, 'w', encoding='utf-8') as f:
                        json.dump(modified_data, f, ensure_ascii=False, indent=4)
                    logger.info(f"Updated application_data.json: {json_file_path}")
                except Exception as e:
                    logger.error(f"Failed to update application_data.json: {e}")
                    QMessageBox.warning(self.view, "保存失败", f"无法保存数据: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to show basic info dialog: {e}")
            QMessageBox.warning(self.view, "错误", f"无法显示更新对话框: {str(e)}")

    def handle_about(self) -> None:
        """处理关于事件

        Returns:
            None
        """
        try:
            # 从Service获取应用信息
            app_info = self.service.get_application_info()

            # 显示关于对话框
            QMessageBox.about(
                self.view,
                f"关于 {app_info['name']}",
                f"""<h2>{app_info['name']}</h2>
            <p><b>版本:</b> {app_info['version']}</p>
            <p><b>作者:</b> {app_info['author']}</p>
            <p>这是一个用于管理测试流程的工具，专注于处理测试申请单、邮件通信和相关文档管理。</p>"""
            )
        except Exception as e:
            logger.error(f"Failed to show about dialog: {e}")

    def get_recent_files(self) -> List[str]:
        """
        获取最近打开的文件列表

        Returns:
            文件路径列表
        """
        return self.service.load_recent_files()

    def clear_recent_files(self) -> None:
        """清空最近打开的文件列表"""
        self.service.clear_recent_files()

    def get_status(self) -> str:
        """
        获取当前状态

        Returns:
            当前状态信息
        """
        return self.service.get_status()

    def _cleanup_non_default_matrix_sessions(self) -> tuple[str, ...]:
        manager = getattr(self, "_matrix_preview_session_manager", None)
        if manager is None:
            return ()
        if hasattr(manager, "close_by_mode"):
            return tuple(manager.close_by_mode("isolated"))
        if hasattr(manager, "close_all"):
            return tuple(manager.close_all())
        return ()

    def shutdown(self) -> None:
        """关闭控制器"""
        try:
            logger.info("Shutting down MainWindowController")
            try:
                manager = getattr(self, "_matrix_preview_session_manager", None)
                if manager is not None and hasattr(manager, "clear_page_session_bindings"):
                    cleared_pages = tuple(manager.clear_page_session_bindings())
                    if cleared_pages:
                        logger.info(
                            f"Cleared matrix workspace page-session bindings during shutdown: {cleared_pages}"
                        )
                closed_ids = self._cleanup_non_default_matrix_sessions()
                if closed_ids:
                    logger.info(
                        f"Closed non-default matrix sessions during shutdown: {closed_ids}"
                    )
            except Exception as session_cleanup_error:
                logger.error(
                    f"Failed to cleanup non-default matrix sessions: {session_cleanup_error}"
                )

            # 在关闭前自动导出Matrix数据
            if self.view and hasattr(self.view, 'matrix_controller'):
                self.view.matrix_controller.auto_export_matrix_data_on_shutdown()
            
            # 保存应用程序状态
            self.service.save_application_state()
            
            # 确保所有COM对象被释放
            try:
                from src.utils import word_utils, excel_utils
                word_utils.release_word_app()
                excel_utils.release_excel_app()
            except:
                pass

            logger.info("MainWindowController shut down successfully")
        except Exception as e:
            logger.error(f"Error during MainWindowController shutdown: {e}")
