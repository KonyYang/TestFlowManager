"""
主窗口控制器模块
处理主窗口的业务逻辑和事件
"""
import os
import json
from typing import List, Optional, TYPE_CHECKING
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QFileDialog
from src.core.logger import logger
from src.core.event_dispatcher import event_dispatcher
from src.core.project_session_coordinator import ProjectSessionCoordinator
from src.features.ltr_manager.controller.ltr_editor_controller import LTREditorController
from src.features.main_window.model.main_window_data import MainWindowData
from src.features.main_window.service.main_window_service import MainWindowService
from src.features.ltr_manager.controller.ltr_viewer_controller import LTRViewerController
from src.features.main_window.view.dialogs.dl_input_dialog import DLInputDialog
from src.features.project_creator.controller.project_creator_controller import ProjectCreatorController
from src.core.project_context import ProjectContext
from src.features.matrix.workspace.matrix_workspace_facade import MatrixWorkspaceFacade
from src.features.main_window.coordinator.project_lifecycle_coordinator import ProjectLifecycleCoordinator

# 类型导入仅用于类型检查，运行时不依赖具体类
if TYPE_CHECKING:
    from src.features.matrix.service.matrix_session_manager import MatrixSessionManager


class MainWindowController:
    """
    主窗口控制器类
    处理主窗口的业务逻辑和事件
    """
    DEFAULT_MATRIX_WORKSPACE_SESSION_ID = "main:shared"
    DEFAULT_MATRIX_WORKSPACE_ENTRY = "main"
    MATRIX_MAIN_PAGE_ID = "matrix.main"

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

        # 项目生命周期统一编排器（通过事件系统触发，不持有 Matrix 引用）
        self.lifecycle_coordinator = ProjectLifecycleCoordinator(
            view=view,
            status_updater=self.service.update_status,
        )

        # 项目会话协调器（通过 facade 获取 matrix_project_controller）
        # 作为 project.opened 事件的消费者，处理项目打开后的副作用
        self.project_session_coordinator = ProjectSessionCoordinator(
            view,
            matrix_project_controller=self.matrix_project_controller,
            status_updater=self.service.update_status,
        )

        # 初始化事件绑定管理器（只订阅 project.opened 和 state.changed）
        from src.features.main_window.integration.event_bindings import EventBindingManager
        self.event_binding_manager = EventBindingManager(
            controller=self,
            status_service=self.service,
        )
        self.event_binding_manager.bind_all()
        
        # 初始化 LTR 状态协调器（处理 LTR 领域事件）
        from src.features.ltr_manager.integration.ltr_status_coordinator import LTRStatusCoordinator
        self.ltr_status_coordinator = LTRStatusCoordinator(
            status_updater=self.service.update_status,
        )

    def _is_isolated_matrix_session_pilot_enabled(self) -> bool:
        """
        Experimental switch for project-creation entry only.
        Default is disabled, which keeps shared behavior unchanged.
        """
        return self._facade.is_new_file_pilot_enabled(os.environ)

    def _is_isolated_matrix_preview_pilot_enabled(self) -> bool:
        """
        Experimental switch for opening a non-default isolated preview session.
        Default is disabled, which keeps shared behavior unchanged.
        """
        return self._facade.is_preview_pilot_enabled(os.environ)

    def _is_debug_matrix_command_enabled(self) -> bool:
        """通过 facade 检查 debug 命令是否启用"""
        return self._facade.is_debug_commands_enabled()

    def _ensure_preview_session_manager(self):
        """通过 facade 获取预览会话管理器"""
        return self._facade.ensure_preview_session_manager()

    def open_isolated_matrix_preview_session(
        self,
        session_id: str,
        *,
        entry_name: str = "preview",
    ):
        """
        Non-default controlled entry for future standalone/preview matrix sessions.
        Does not affect default shared mainline behavior.
        """
        if not session_id:
            raise ValueError("session_id is required for isolated matrix preview session")
        return self._facade.open_preview_session(session_id, entry_name=entry_name)

    def handle_open_isolated_matrix_preview_pilot(self) -> str | None:
        """
        Controlled non-default entry (pilot) for isolated preview session.
        Default is disabled; when enabled it opens a fixed isolated preview session id.
        """
        pilot_enabled = self._is_isolated_matrix_preview_pilot_enabled()
        session_id = self._facade.resolve_preview_pilot_session_id(pilot_enabled=pilot_enabled)
        if not session_id:
            return None
        session = self.open_isolated_matrix_preview_session(
            session_id,
            entry_name="preview",
        )
        matrix_project_controller = getattr(session, "matrix_project_controller", None)
        if matrix_project_controller and hasattr(matrix_project_controller, "open_matrix_workspace"):
            matrix_project_controller.open_matrix_workspace()
        return session_id

    def close_isolated_matrix_preview_session(self, session_id: str) -> bool:
        return self._facade.close_preview_session(session_id)

    def handle_close_isolated_matrix_preview_pilot(self) -> bool:
        """
        Controlled non-default close entry (pilot) for isolated preview session.
        Default is disabled; when enabled it closes the fixed isolated preview session id.

        Close semantics:
        - closes the managed session and clears any page binding via manager lifecycle.
        - best-effort restores active session to the default workspace session id if present.
        - triggers workspace consistency check after close.
        """
        pilot_enabled = self._is_isolated_matrix_preview_pilot_enabled()
        session_id = self._facade.resolve_preview_pilot_session_id(pilot_enabled=pilot_enabled)
        if not session_id:
            return False

        active_session_id = self._facade.get_active_session_id()

        closed = self.close_isolated_matrix_preview_session(session_id)
        if not closed:
            return False

        if active_session_id == session_id:
            self._facade.activate_session(self.DEFAULT_MATRIX_WORKSPACE_SESSION_ID)

        self.ensure_matrix_workspace_session_consistency()
        return True

    def debug_open_isolated_matrix_preview_session(self, session_id: Optional[str] = None) -> Optional[str]:
        if not self._is_debug_matrix_command_enabled():
            return None

        resolved_session_id, session = self._facade.open_debug_preview_session(session_id=session_id)

        matrix_project_controller = getattr(session, "matrix_project_controller", None)
        if matrix_project_controller and hasattr(matrix_project_controller, "open_matrix_workspace"):
            matrix_project_controller.open_matrix_workspace()
        self._debug_publish_matrix_session_state("open")

        return resolved_session_id

    def debug_close_isolated_matrix_preview_session(self, session_id: Optional[str] = None) -> bool:
        if not self._is_debug_matrix_command_enabled():
            return False

        closed, target_id = self._facade.close_debug_preview_session(session_id=session_id)
        if not closed or not target_id:
            return False
        self._debug_publish_matrix_session_state("close")
        return True

    def debug_switch_isolated_matrix_preview_session(self, session_id: str) -> bool:
        if not self._is_debug_matrix_command_enabled():
            return False
        result = self._facade.switch_preview_session(session_id)
        if not getattr(result, "success", False):
            reason = getattr(result, "reason", None) or "unknown"
            service = getattr(self, "service", None)
            if service is not None and hasattr(service, "update_status"):
                service.update_status(
                    self._facade.format_switch_failed(reason, session_id)
                )
            return False
        state = self._build_matrix_session_debug_state()
        entry_name = getattr(result, "entry_name", None) or "unknown"
        service = getattr(self, "service", None)
        if service is not None and hasattr(service, "update_status"):
            service.update_status(
                self._facade.format_switch_success(
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

    def on_page_visible(self, page_id: str) -> dict:
        """
        当页面变为可见时调用 - 委托给 MatrixWorkspaceFacade 处理。

        Shell 只负责转发页面变更，Matrix 内部逻辑由 Facade 处理。

        Args:
            page_id: 页面标识符

        Returns:
            包含 session binding 信息的字典
        """
        return self._facade.on_page_visible(page_id)

    def on_page_hidden(self, page_id: str) -> bool:
        """
        当页面被隐藏时调用 - 委托给 MatrixWorkspaceFacade 处理。

        Args:
            page_id: 页面标识符

        Returns:
            是否成功处理
        """
        return self._facade.on_page_hidden(page_id)

    def get_matrix_workspace_session_binding(self, *, page_id: str = MATRIX_MAIN_PAGE_ID) -> dict:
        """Returns matrix workspace session metadata for page-level binding."""
        return self._facade.on_page_visible(page_id)

    def ensure_matrix_workspace_session_consistency(
        self,
        *,
        page_id: str = MATRIX_MAIN_PAGE_ID,
    ) -> dict:
        """
        Ensures matrix workspace visible page is aligned with active session routing.
        委托给 MatrixWorkspaceFacade 处理。
        """
        result = self._facade.on_page_visible(page_id)
        return result.get("consistency", {"success": True})

    def handle_matrix_workspace_hidden(self, *, page_id: str = MATRIX_MAIN_PAGE_ID) -> bool:
        """
        Clears page-level session binding when matrix workspace is no longer visible.
        This does not close sessions; it only releases page->session association.
        委托给 MatrixWorkspaceFacade 处理。
        """
        return self._facade.on_page_hidden(page_id)

    def _build_matrix_session_debug_state(self) -> dict:
        registry_snapshot = self._facade.get_registry_snapshot()
        return self._facade.get_debug_state(registry_snapshot=registry_snapshot)

    def _debug_publish_matrix_session_state(self, action: str) -> None:
        if not self._is_debug_matrix_command_enabled():
            return
        state = self._build_matrix_session_debug_state()
        status_text = self._facade.format_debug_state_status(action, state)
        logger.info(f"Matrix session debug state: {state}")
        service = getattr(self, "service", None)
        if service is not None and hasattr(service, "update_status"):
            service.update_status(status_text)

    # LTR 事件处理已移至 LTRStatusCoordinator
    # project.opened 事件通过 EventBindingManager 转发
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
        """Handle state changed event - internal state management only.

        Note: application_status updates are handled by EventBindingManager directly.
        Project open flow is driven by `project.opened` event.
        """
        key = data.get("key")

        if key == "current_project_context":
            new_value = data.get("new_value")
            if not isinstance(new_value, ProjectContext):
                self._project_context = None
            return

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
            session_config = self._facade.resolve_new_file_session_config(
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
        处理打开项目事件 - 委托给 ProjectLifecycleCoordinator

        Returns:
            是否处理成功
        """
        return self.lifecycle_coordinator.handle_open_project()


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

    # ==================== Matrix 操作代理方法 ====================
    # 所有 UI 对 Matrix 的操作都通过 controller 代理，避免直接耦合

    def get_matrix_controller(self):
        """
        获取 MatrixController 实例。

        Returns:
            MatrixController 或 None（如果未初始化）
        """
        if not self.matrix_project_controller:
            return None
        return self.matrix_project_controller.matrix_controller

    def handle_export_matrix_to_excel(self) -> dict:
        """
        代理 Matrix 导出操作。

        Returns:
            包含 success 和 message 键的字典
        """
        matrix_ctrl = self.get_matrix_controller()
        if not matrix_ctrl:
            return {"success": False, "message": "Matrix未初始化"}
        return matrix_ctrl.handle_export_matrix_to_excel()

    def handle_export_llcr(self) -> bool:
        """
        代理 LLCR 导出操作。

        Returns:
            是否成功
        """
        matrix_ctrl = self.get_matrix_controller()
        if not matrix_ctrl:
            return False
        return matrix_ctrl.handle_export_llcr()

    def handle_export_cr(self) -> bool:
        """
        代理 CR 导出操作。

        Returns:
            是否成功
        """
        matrix_ctrl = self.get_matrix_controller()
        if not matrix_ctrl:
            return False
        return matrix_ctrl.handle_export_cr()

    def auto_export_matrix_data_on_shutdown(self) -> None:
        """代理关闭时自动导出 Matrix 数据"""
        matrix_ctrl = self.get_matrix_controller()
        if matrix_ctrl:
            matrix_ctrl.auto_export_matrix_data_on_shutdown()

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
            
            # 解绑事件订阅
            if hasattr(self, 'event_binding_manager'):
                try:
                    self.event_binding_manager.unbind_all()
                    logger.info("Event subscriptions unbound successfully")
                except Exception as e:
                    logger.error(f"Failed to unbind events: {e}")
            
            # 清理 LTR 状态协调器
            if hasattr(self, 'ltr_status_coordinator'):
                try:
                    self.ltr_status_coordinator.cleanup()
                    logger.info("LTR status coordinator cleaned up")
                except Exception as e:
                    logger.error(f"Failed to cleanup LTR status coordinator: {e}")
            
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

            # 在关闭前自动导出Matrix数据（通过代理方法）
            self.auto_export_matrix_data_on_shutdown()
            
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
