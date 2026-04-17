"""
主窗口控制器模块（Shell 协调层）
处理主窗口的业务逻辑和事件，协调各领域 Facade
"""
import os
from typing import List, Optional, TYPE_CHECKING
from PyQt5.QtWidgets import QWidget, QMessageBox
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.shell.main_window.coordinator.project_session_coordinator import ProjectSessionCoordinator
from src.shell.main_window.model.main_window_data import MainWindowData
from src.core.project_context import ProjectContext
from src.features.matrix.workspace.matrix_workspace_facade import MatrixWorkspaceFacade
from src.shell.main_window.coordinator.project_lifecycle_coordinator import ProjectLifecycleCoordinator

# 类型导入仅用于类型检查，运行时不依赖具体类
if TYPE_CHECKING:
    from src.features.matrix.service.matrix_session_manager import MatrixSessionManager
    from src.features.ltr_manager.facade.ltr_facade import LTRFacade
    from src.shell.main_window.integration.file_operations_facade import FileOperationsFacade


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
        project_session_coordinator=None,  # Phase 4: 从 Assembler 注入
    ):
        """
        初始化主窗口控制器（Shell 协调层）

        Args:
            view: 主窗口视图实例
            matrix_workspace_facade: Matrix 工作区协同件
            project_session_coordinator: 项目会话协调器（Phase 4: 从 Assembler 注入）
        """
        self.view = view
        self.data_model = MainWindowData()

        # 初始化状态
        self.data_model.update_status("就绪")

        # 初始化当前项目路径
        self._project_context: Optional[ProjectContext] = None

        # =========================================================================
        # 领域 Facade 初始化（Shell 协调层持有各领域 Facade）
        # =========================================================================

        # Matrix Workspace Facade
        self._matrix_facade = matrix_workspace_facade or MatrixWorkspaceFacade(parent_view=view)
        self._matrix_facade.parent_view = view

        # 组装共享 session
        matrix_session = self._matrix_facade.assemble_shared_session(
            session_id=self.DEFAULT_MATRIX_WORKSPACE_SESSION_ID,
            entry_name=self.DEFAULT_MATRIX_WORKSPACE_ENTRY,
        )
        self.matrix_project_controller = matrix_session.matrix_project_controller if matrix_session else None

        # =========================================================================
        # 生命周期和会话管理
        # =========================================================================

        # 项目生命周期统一编排器（通过事件系统触发，不持有 Matrix 引用）
        self.lifecycle_coordinator = ProjectLifecycleCoordinator(
            view=view,
            status_updater=self.data_model.update_status,
        )

        # Phase 4: 项目会话协调器
        # 如果从 Assembler 注入了协调器，则使用注入的；否则向后兼容（自己创建）
        if project_session_coordinator is not None:
            # 使用注入的协调器，并更新其依赖引用
            self.project_session_coordinator = project_session_coordinator
            self.project_session_coordinator.view = view
            self.project_session_coordinator.matrix_project_controller = self.matrix_project_controller
            self.project_session_coordinator.status_updater = self.data_model.update_status
        else:
            # 向后兼容：自己创建协调器
            self.project_session_coordinator = ProjectSessionCoordinator(
                view,
                matrix_project_controller=self.matrix_project_controller,
                status_updater=self.data_model.update_status,
            )

        # 非核心 Facade/Coordinator 延迟到 initialize() 中创建，避免启动时加载 COM 等重型依赖
        self.event_binding_manager = None
        self.ltr_status_coordinator = None
        self._file_operations_facade = None
        self._ltr_facade = None

    @property
    def ltr_facade(self):
        """安全访问 LTR Facade（确保已初始化）"""
        if self._ltr_facade is None:
            from src.features.ltr_manager.facade.ltr_facade import LTRFacade
            self._ltr_facade = LTRFacade()
        return self._ltr_facade

    @property
    def file_operations_facade(self):
        """安全访问 FileOperationsFacade（确保已初始化）"""
        if self._file_operations_facade is None:
            from src.shell.main_window.integration.file_operations_facade import FileOperationsFacade
            self._file_operations_facade = FileOperationsFacade(
                parent_view=self.view,
                data_model=self.data_model,
                matrix_facade=self._matrix_facade,
                lifecycle_coordinator=self.lifecycle_coordinator,
            )
        return self._file_operations_facade

    def on_page_visible(self, page_id: str) -> dict:
        """当页面变为可见时调用 - 委托给 MatrixWorkspaceFacade 处理。"""
        return self._matrix_facade.on_page_visible(page_id)

    def on_page_hidden(self, page_id: str) -> bool:
        """当页面被隐藏时调用 - 委托给 MatrixWorkspaceFacade 处理。"""
        return self._matrix_facade.on_page_hidden(page_id)

    def get_matrix_workspace_session_binding(self, *, page_id: str = MATRIX_MAIN_PAGE_ID) -> dict:
        """Returns matrix workspace session metadata for page-level binding."""
        return self._matrix_facade.on_page_visible(page_id)

    def ensure_matrix_workspace_session_consistency(
        self,
        *,
        page_id: str = MATRIX_MAIN_PAGE_ID,
    ) -> dict:
        """Ensures matrix workspace visible page is aligned with active session routing."""
        result = self._matrix_facade.on_page_visible(page_id)
        return result.get("consistency", {"success": True})

    def handle_matrix_workspace_hidden(self, *, page_id: str = MATRIX_MAIN_PAGE_ID) -> bool:
        """Clears page-level session binding when matrix workspace is no longer visible."""
        return self._matrix_facade.on_page_hidden(page_id)

    # =========================================================================
    # 项目上下文管理（事件驱动的副作用已移至 ProjectSessionCoordinator）
    # =========================================================================

    @property
    def project_context(self) -> Optional[ProjectContext]:
        """获取当前项目上下文"""
        return self._project_context

    @property
    def current_project_path(self) -> Optional[str]:
        """获取当前项目路径"""
        if not self._project_context:
            return None
        return self._project_context.project_path

    def initialize(self) -> bool:
        """
        初始化控制器（延迟创建非核心 Facade/Coordinator，减少启动耗时）

        Returns:
            初始化是否成功
        """
        try:
            logger.info("Initializing MainWindowController")

            # --- 延迟创建非核心组件（启动优化） ---
            # 事件绑定管理器
            from src.shell.main_window.integration.event_bindings import EventBindingManager
            self.event_binding_manager = EventBindingManager(
                controller=self,
                status_service=self.data_model,
            )
            self.event_binding_manager.bind_all()

            # LTR 状态协调器
            from src.features.ltr_manager.integration.ltr_status_coordinator import LTRStatusCoordinator
            self.ltr_status_coordinator = LTRStatusCoordinator(
                status_updater=self.data_model.update_status,
            )

            # 文件操作 Facade
            from src.shell.main_window.integration.file_operations_facade import FileOperationsFacade
            self._file_operations_facade = FileOperationsFacade(
                parent_view=self.view,
                data_model=self.data_model,
                matrix_facade=self._matrix_facade,
                lifecycle_coordinator=self.lifecycle_coordinator,
            )

            # LTR Facade
            from src.features.ltr_manager.facade.ltr_facade import LTRFacade
            self._ltr_facade = LTRFacade()

            # 加载最近文件列表
            recent_files = self.data_model.get_recent_files()
            logger.info(f"Loaded {len(recent_files)} recent files")

            logger.info("MainWindowController initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MainWindowController: {e}")
            return False

    def handle_view_ltr(self) -> bool:
        """
        处理查看LTR文件事件（委托给 LTRFacade）

        Returns:
            是否成功打开LTR文件
        """
        logger.debug("Handling view LTR file request (delegated to LTRFacade)")
        return self.ltr_facade.handle_view_ltr(self.view)


    def handle_open_file(self, file_path: str) -> bool:
        """
        处理打开文件事件（委托给 FileOperationsFacade）

        Args:
            file_path: 文件路径

        Returns:
            是否处理成功
        """
        logger.debug(f"MainWindowController: Delegating handle_open_file to FileOperationsFacade")
        return self.file_operations_facade.handle_open_file(file_path)

    def handle_new_file(self) -> bool:
        """
        处理新建文件事件（委托给 FileOperationsFacade）

        Returns:
            是否处理成功
        """
        logger.debug("MainWindowController: Delegating handle_new_file to FileOperationsFacade")
        return self.file_operations_facade.handle_new_file()

    def handle_open_project(self) -> bool:
        """
        处理打开项目事件 - 委托给 ProjectLifecycleCoordinator

        Returns:
            是否处理成功
        """
        return self.lifecycle_coordinator.handle_open_project()


    def handle_about(self) -> None:
        """处理关于事件"""
        try:
            app_info = {
                'name': config_manager.get("app.name", "TestFlowManager"),
                'version': config_manager.get("app.version", "1.0.0"),
                'author': config_manager.get("app.author", "Even")
            }

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
        """获取最近打开的文件列表（委托给 FileOperationsFacade）"""
        return self.file_operations_facade.get_recent_files()

    def clear_recent_files(self) -> None:
        """清空最近打开的文件列表（委托给 FileOperationsFacade）"""
        self.file_operations_facade.clear_recent_files()

    def get_status(self) -> str:
        """获取当前状态"""
        return self.data_model.get_status()

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


    def shutdown(self) -> None:
        """
        关闭控制器 - 委托给全局清理注册表
        
        这个方法现在非常简洁，只负责触发统一的清理流程。
        各模块的清理逻辑通过注册表自动执行。
        """
        try:
            logger.info("Shutting down MainWindowController")
            
            # 一行代码执行所有清理
            from src.core.shutdown_registry import shutdown_registry
            result = shutdown_registry.execute_all()
            
            # 根据结果做进一步处理
            if result["failed"]:
                logger.warning(
                    f"Some shutdown hooks failed: "
                    f"{[f['name'] for f in result['failed']]}"
                )
            
            logger.info("MainWindowController shut down successfully")
        except Exception as e:
            logger.error(f"Error during MainWindowController shutdown: {e}")
