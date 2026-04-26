"""
主窗口控制器模块（Shell 协调层）
处理主窗口的业务逻辑和事件，协调各领域 Facade
"""
import os
from importlib import import_module
from typing import List, Optional, Any
from PyQt5.QtWidgets import QWidget, QMessageBox
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.shell.main_window.coordinator.project_lifecycle_coordinator import ProjectLifecycleCoordinator
from src.shell.main_window.model.main_window_data import MainWindowData
from src.core.project_context import ProjectContext


def _load_symbol(module_path: str, symbol_name: str):
    """Load shell collaborators lazily without adding static feature import edges."""
    module = import_module(module_path)
    return getattr(module, symbol_name)


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
        matrix_workspace_facade: Optional[Any] = None,
        project_session_coordinator=None,  # Phase 4: 从 Assembler 注入
        project_session_app_service=None,  # S1-2: 应用层编排器
    ):
        """
        初始化主窗口控制器（Shell 协调层）

        Args:
            view: 主窗口视图实例
            matrix_workspace_facade: Matrix 工作区协同件
            project_session_coordinator: 项目会话协调器（Phase 4: 从 Assembler 注入）
            project_session_app_service: 项目会话应用层编排器（S1-2: 唯一主入口）
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

        # Phase 4: 项目会话协调器（由 Assembler 注入）
        self.project_session_coordinator = project_session_coordinator
        if self.project_session_coordinator:
            self.project_session_coordinator.view = view
            self.project_session_coordinator.matrix_project_controller = self.matrix_project_controller
            self.project_session_coordinator.status_updater = self.data_model.update_status

        # S1-2: 应用层编排器（由 Assembler 注入，唯一主入口）
        self.project_session_app_service = project_session_app_service
        if self.project_session_app_service and self.project_session_coordinator:
            self.project_session_app_service.coordinator = self.project_session_coordinator

        # 非核心 Facade/Coordinator 延迟到 initialize() 中创建，避免启动时加载 COM 等重型依赖
        self.event_binding_manager = None
        self.ltr_status_coordinator = None
        self._file_operations_facade = None
        self._ltr_facade = None

    def apply_project_opened_event(self, data: dict) -> bool:
        """
        Update shell-held project context from a project.opened payload.

        Returns:
            True when the payload produced a valid ProjectContext.
        """
        project_context = ProjectContext.from_event_data(data)
        if not project_context:
            return False

        self._project_context = project_context
        logger.info(
            "MainWindowController: Updated project_context=%s",
            project_context.project_path,
        )
        return True

    @property
    def ltr_facade(self):
        """安全访问 LTR Facade（确保已初始化）"""
        if self._ltr_facade is None:
            LTRFacade = _load_symbol(
                "src.features.ltr_manager.facade.ltr_facade",
                "LTRFacade",
            )
            self._ltr_facade = LTRFacade()
        return self._ltr_facade

    @property
    def file_operations_facade(self):
        """安全访问 FileOperationsFacade（确保已初始化）"""
        if self._file_operations_facade is None:
            FileOperationsFacade = _load_symbol(
                "src.shell.main_window.integration.file_operations_facade",
                "FileOperationsFacade",
            )
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
            EventBindingManager = _load_symbol(
                "src.shell.main_window.integration.event_bindings",
                "EventBindingManager",
            )
            self.event_binding_manager = EventBindingManager(
                controller=self,
                status_service=self.data_model,
            )
            self.event_binding_manager.bind_all()

            # LTR 状态协调器
            LTRStatusCoordinator = _load_symbol(
                "src.features.ltr_manager.integration.ltr_status_coordinator",
                "LTRStatusCoordinator",
            )
            self.ltr_status_coordinator = LTRStatusCoordinator(
                status_updater=self.data_model.update_status,
            )

            # 文件操作 Facade
            FileOperationsFacade = _load_symbol(
                "src.shell.main_window.integration.file_operations_facade",
                "FileOperationsFacade",
            )
            self._file_operations_facade = FileOperationsFacade(
                parent_view=self.view,
                data_model=self.data_model,
                matrix_facade=self._matrix_facade,
                lifecycle_coordinator=self.lifecycle_coordinator,
            )

            # LTR Facade
            LTRFacade = _load_symbol(
                "src.features.ltr_manager.facade.ltr_facade",
                "LTRFacade",
            )
            self._ltr_facade = LTRFacade()

            # 加载最近文件列表
            recent_files = self.data_model.get_recent_files()
            logger.info(f"Loaded {len(recent_files)} recent files")

            logger.info("MainWindowController initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MainWindowController: {e}")
            return False

    def handle_view_ltr(self) -> dict:
        """
        处理查看LTR文件事件（委托给 LTRFacade）

        Returns:
            包含处理结果的字典:
            - success: 是否成功处理
            - ltr_data: LTR 数据字典（如果找到）
        """
        logger.debug("Handling view LTR file request (delegated to LTRFacade)")
        result = self.ltr_facade.handle_view_ltr(self.view)

        # 如果成功查找到了 LTR 数据，更新页面
        if result.get("success") and result.get("ltr_data"):
            self._update_ltr_page(result["ltr_data"])

        return result

    def _update_ltr_page(self, ltr_data: dict) -> None:
        """
        更新 LTR 申请单页面

        Args:
            ltr_data: 包含 dl_number 和 data 的字典
        """
        if not hasattr(self.view, '_nav_controller') or not self.view._nav_controller:
            return

        try:
            ltr_page = self.view._nav_controller.get_page_by_page_id("ltr.view")
            if ltr_page and hasattr(ltr_page, 'update_data'):
                ltr_page.update_data(ltr_data)
                logger.debug(f"MainWindowController: Updated LTR page with dl_number={ltr_data.get('dl_number', '')}")
        except Exception as e:
            logger.error(f"MainWindowController: Failed to update LTR page: {e}")

    def handle_edit_ltr(self) -> dict:
        """
        处理编辑LTR事件（切换到LTR编辑器页面）

        Returns:
            包含处理结果的字典:
            - success: 是否成功
        """
        logger.debug("Handling edit LTR request (switch to LTR editor page)")

        if not hasattr(self.view, '_nav_controller') or not self.view._nav_controller:
            logger.warning("Navigation controller not available")
            return {"success": False}

        try:
            # 切换到 LTR 编辑器页面
            entry = self.view._nav_controller.get_entry_by_page_id("ltr.editor")
            if entry:
                # 找到对应的列表索引并选中
                for idx, registered_entry in enumerate(self.view._nav_controller._entries):
                    if registered_entry.page_id == "ltr.editor":
                        self.view._nav_controller.select_entry(idx)
                        break
                return {"success": True}
            else:
                logger.warning("LTR editor page not found in navigation")
                return {"success": False}
        except Exception as e:
            logger.error(f"MainWindowController: Failed to switch to LTR editor page: {e}")
            return {"success": False}

    def _update_ltr_editor_page(self, ltr_data: dict) -> None:
        """
        更新 LTR 编辑器页面

        Args:
            ltr_data: 包含 dl_number 和 data 的字典
        """
        if not hasattr(self.view, '_nav_controller') or not self.view._nav_controller:
            return

        try:
            ltr_editor_page = self.view._nav_controller.get_page_by_page_id("ltr.editor")
            if ltr_editor_page and hasattr(ltr_editor_page, 'update_data'):
                ltr_editor_page.update_data(ltr_data)
                logger.debug(f"MainWindowController: Updated LTR editor page with dl_number={ltr_data.get('dl_number', '')}")
        except Exception as e:
            logger.error(f"MainWindowController: Failed to update LTR editor page: {e}")

    def handle_edit_project_info(self) -> dict:
        """
        处理编辑项目信息事件（切换到项目信息页面）

        Returns:
            包含处理结果的字典:
            - success: 是否成功
        """
        logger.debug("Handling edit project info request (switch to project info page)")

        if not hasattr(self.view, '_nav_controller') or not self.view._nav_controller:
            logger.warning("Navigation controller not available")
            return {"success": False}

        try:
            # 切换到项目信息页面
            entry = self.view._nav_controller.get_entry_by_page_id("project.info")
            if entry:
                # 找到对应的列表索引并选中
                for idx, registered_entry in enumerate(self.view._nav_controller._entries):
                    if registered_entry.page_id == "project.info":
                        self.view._nav_controller.select_entry(idx)
                        break
                return {"success": True}
            else:
                logger.warning("Project info page not found in navigation")
                return {"success": False}
        except Exception as e:
            logger.error(f"MainWindowController: Failed to switch to project info page: {e}")
            return {"success": False}

    def _update_project_info_page(self, project_data: dict, project_data_file_path: str = None) -> None:
        """
        更新项目信息页面

        Args:
            project_data: 项目数据字典
            project_data_file_path: 项目数据文件路径（可选）
        """
        if not hasattr(self.view, '_nav_controller') or not self.view._nav_controller:
            return

        try:
            project_info_page = self.view._nav_controller.get_page_by_page_id("project.info")
            if project_info_page and hasattr(project_info_page, 'update_data'):
                project_info_page.update_data(project_data, project_data_file_path)
                logger.debug(f"MainWindowController: Updated project info page")
        except Exception as e:
            logger.error(f"MainWindowController: Failed to update project info page: {e}")

    def handle_create_report(self) -> dict:
        """
        处理创建报告事件（切换到报告向导页面）

        Returns:
            包含处理结果的字典:
            - success: 是否成功
            - message: 错误信息（如果有）
        """
        from PyQt5.QtWidgets import QMessageBox

        logger.debug("Handling create report request (switch to report wizard page)")

        # 检查是否已打开项目
        if not self.project_context:
            QMessageBox.warning(
                self.view,
                "警告",
                "请先打开一个项目后再创建报告。\n\n操作步骤：\n1. 点击'文件' -> '打开项目'\n2. 选择项目文件夹\n3. 然后再尝试创建报告"
            )
            logger.warning("创建报告失败：项目未打开")
            return {"success": False, "message": "项目未打开"}

        if not hasattr(self.view, '_nav_controller') or not self.view._nav_controller:
            logger.warning("Navigation controller not available")
            return {"success": False, "message": "Navigation controller not available"}

        try:
            # 配置并切换到报告向导页面
            report_wizard_page = self.view._nav_controller.get_page_by_page_id("report.create")
            if report_wizard_page:
                # 设置项目上下文和 Matrix 控制器
                if hasattr(report_wizard_page, 'set_project_context'):
                    report_wizard_page.set_project_context(self.project_context)
                if hasattr(report_wizard_page, 'set_matrix_controller'):
                    report_wizard_page.set_matrix_controller(self.get_matrix_controller())

                # 切换到报告向导页面
                for idx, registered_entry in enumerate(self.view._nav_controller._entries):
                    if registered_entry.page_id == "report.create":
                        self.view._nav_controller.select_entry(idx)
                        break
                return {"success": True}
            else:
                logger.warning("Report wizard page not found in navigation")
                return {"success": False, "message": "报告向导页面未找到"}
        except Exception as e:
            logger.error(f"MainWindowController: Failed to switch to report wizard page: {e}")
            return {"success": False, "message": str(e)}


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
            shutdown_registry = _load_symbol(
                "src.core.shutdown_registry",
                "shutdown_registry",
            )
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
