from __future__ import annotations

import os
from typing import Mapping, Optional, TYPE_CHECKING, Any, Tuple

from PyQt5.QtWidgets import QWidget

from src.core.logger import logger
from src.features.matrix.service.matrix_session_entry_policy import MatrixSessionEntryPolicyTable
from src.features.matrix.service.matrix_session_manager import MatrixSessionManager
from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator
from src.features.matrix.service.matrix_session_debug_facade import MatrixSessionDebugFacade
from src.features.matrix.service.matrix_session_entry_facade import MatrixSessionEntryFacade
from src.features.matrix.service.matrix_session_registry import MatrixSessionRegistry
from src.features.matrix.workspace.matrix_workspace_coordinator import MatrixWorkspaceCoordinator

if TYPE_CHECKING:
    from src.features.matrix.view.matrix_page import MatrixPage


class MatrixWorkspaceFacade:
    """矩阵工作区协同件，封装 session 和 page 相关 lifecycle

    这是 Matrix 拥有的官方边界组件，位于 src/features/matrix/workspace/。
    Shell 代码应从此路径导入。

    Step 8 更新：此 facade 现在也是 MatrixPage 的拥有者，负责：
    - Page 构造（替代 shell 直接创建）
    - Page runtime 方法代理（替代 shell 直接调用）
    - Session/page 绑定管理
    """

    def __init__(
        self,
        parent_view: Optional[QWidget],
        matrix_controller: Optional = None,
        matrix_session_registry: Optional[MatrixSessionRegistry] = None,
        matrix_session_entry_policies: Optional[MatrixSessionEntryPolicyTable] = None,
        matrix_session_manager: Optional[MatrixSessionManager] = None,
        matrix_session_orchestrator: Optional[MatrixSessionOrchestrator] = None,
        matrix_session_debug_facade: Optional[MatrixSessionDebugFacade] = None,
        matrix_session_entry_facade: Optional[MatrixSessionEntryFacade] = None,
        matrix_workspace_coordinator: Optional[MatrixWorkspaceCoordinator] = None,
    ):
        self.parent_view = parent_view
        self._matrix_controller = matrix_controller
        self._matrix_page = None  # MatrixPage 引用，由 facade 自己创建并持有
        self.matrix_session_registry = matrix_session_registry or MatrixSessionRegistry()
        self.matrix_session_entry_policies = matrix_session_entry_policies or MatrixSessionEntryPolicyTable()
        self.matrix_session_manager = matrix_session_manager or MatrixSessionManager(
            parent_view=self.parent_view,
            registry=self.matrix_session_registry,
        )
        self.matrix_session_orchestrator = matrix_session_orchestrator or MatrixSessionOrchestrator(self.matrix_session_manager)
        self.matrix_session_debug_facade = matrix_session_debug_facade or MatrixSessionDebugFacade(
            orchestrator=self.matrix_session_orchestrator,
            entry_policies=self.matrix_session_entry_policies,
        )
        self.matrix_session_entry_facade = matrix_session_entry_facade or MatrixSessionEntryFacade(
            entry_policies=self.matrix_session_entry_policies,
        )
        self.matrix_workspace_coordinator = matrix_workspace_coordinator or MatrixWorkspaceCoordinator(
            parent_view=self.parent_view,
            matrix_session_registry=self.matrix_session_registry,
            matrix_session_manager=self.matrix_session_manager,
            matrix_session_orchestrator=self.matrix_session_orchestrator,
            matrix_session_debug_facade=self.matrix_session_debug_facade,
            matrix_session_entry_facade=self.matrix_session_entry_facade,
            matrix_session_entry_policies=self.matrix_session_entry_policies,
        )
        self._shared_session = None

    def assemble_shared_session(self, session_id: str, entry_name: str):
        """绑定视图并组装共享 session"""
        if self.parent_view:
            self.matrix_workspace_coordinator.bind_parent_view(self.parent_view)
        self._shared_session = self.matrix_workspace_coordinator.assemble_shared_session(
            parent_view=self.parent_view,
            session_id=session_id,
            entry_name=entry_name,
        )
        return self._shared_session

    def ensure_preview_session_manager(self) -> MatrixSessionManager:
        """提供预览会话管理器（延迟访问点）"""
        return self.matrix_workspace_coordinator.matrix_session_manager

    # =========================================================================
    # Pilot Flag Checks (Facade-level)
    # =========================================================================
    # 这些方法将 session entry policy 知识封装在 facade 内部，
    # 避免 shell 代码直接导入 MatrixSessionEntryFacade。

    def is_new_file_pilot_enabled(self, env: Mapping[str, str] | None = None) -> bool:
        """检查新建文件隔离 session pilot 是否启用"""
        return self.matrix_workspace_coordinator.is_new_file_pilot_enabled(env)

    def is_preview_pilot_enabled(self, env: Mapping[str, str] | None = None) -> bool:
        """检查预览隔离 session pilot 是否启用"""
        return self.matrix_workspace_coordinator.is_preview_pilot_enabled(env)

    def is_debug_commands_enabled(self) -> bool:
        """检查 debug 命令是否启用（通过环境变量 TFM_ENABLE_DEBUG_COMMANDS）"""
        value = os.getenv("TFM_ENABLE_DEBUG_COMMANDS", "")
        return value.strip().lower() in {"1", "true", "yes", "on"}

    # =========================================================================
    # Preview/Debug Session Operations (Facade-level)
    # =========================================================================

    def open_preview_session(self, session_id: str, *, entry_name: str = "preview"):
        """打开隔离预览 session"""
        return self.matrix_workspace_coordinator.open_preview_session(
            session_id,
            entry_name=entry_name,
        )

    def close_preview_session(self, session_id: str) -> bool:
        """关闭隔离预览 session"""
        return self.matrix_workspace_coordinator.close_preview_session(session_id)

    def open_debug_preview_session(self, session_id: str | None = None) -> Tuple[str | None, Any]:
        """打开 debug 预览 session，返回 (resolved_session_id, session)"""
        return self.matrix_workspace_coordinator.open_debug_preview_session(
            session_id=session_id
        )

    def close_debug_preview_session(self, session_id: str | None = None) -> tuple[bool, str | None]:
        """关闭 debug 预览 session，返回 (closed, target_id)"""
        return self.matrix_workspace_coordinator.close_debug_preview_session(
            session_id=session_id
        )

    def switch_preview_session(self, session_id: str):
        """切换到指定预览 session"""
        return self.matrix_workspace_coordinator.switch_preview_session(session_id)

    def resolve_preview_pilot_session_id(self, *, pilot_enabled: bool) -> str | None:
        """根据 pilot 启用状态解析预览 session ID"""
        return self.matrix_workspace_coordinator.resolve_preview_pilot_session_id(
            pilot_enabled=pilot_enabled
        )

    def resolve_new_file_session_config(self, *, pilot_enabled: bool):
        """解析新建文件的 session 配置"""
        return self.matrix_workspace_coordinator.resolve_new_file_session_config(
            pilot_enabled=pilot_enabled
        )

    # =========================================================================
    # Debug State and Formatting (Facade-level)
    # =========================================================================

    def get_debug_state(self, registry_snapshot=None) -> dict:
        """获取 debug 状态快照"""
        return self.matrix_workspace_coordinator.get_debug_state(
            registry_snapshot=registry_snapshot
        )

    def format_debug_state_status(self, action: str, state: dict) -> str:
        """格式化 debug 状态为状态栏文本"""
        return self.matrix_workspace_coordinator.format_debug_state_status(
            action,
            state,
        )

    def format_switch_success(self, session_id: str, entry_name: str, state: dict) -> str:
        """格式化切换成功消息"""
        return self.matrix_workspace_coordinator.format_switch_success(
            session_id,
            entry_name,
            state,
        )

    def format_switch_failed(self, reason: str, session_id: str) -> str:
        """格式化切换失败消息"""
        return self.matrix_workspace_coordinator.format_switch_failed(
            reason,
            session_id,
        )

    def get_registry_snapshot(self):
        """获取 registry 快照（用于 debug state）"""
        return self.matrix_workspace_coordinator.get_registry_snapshot()

    def activate_session(self, session_id: str) -> bool:
        """激活指定 session"""
        return self.matrix_workspace_coordinator.activate_session(session_id)

    def get_active_session_id(self) -> str | None:
        """获取当前 active session ID"""
        return self.matrix_workspace_coordinator.get_active_session_id()

    # =========================================================================
    # Page Visibility Handlers
    # =========================================================================
    # 这些方法由 MainWindowController 调用，用于处理页面切换时的 Matrix 逻辑。
    # Shell 不应知道 matrix.main 的内部绑定规则。

    def on_page_visible(self, page_id: str) -> dict:
        """
        当某个页面变为可见时调用。

        Shell 只转发页面身份，Matrix 可见性策略由 Facade 内部处理。

        Args:
            page_id: 页面标识符，如 "matrix.main"

        Returns:
            包含 session binding 信息的字典
        """
        if page_id != "matrix.main":
            return {"bound": False}

        # 确保 workspace session 一致性
        consistency = self._ensure_workspace_session_consistency(page_id)

        # 获取 session binding 信息
        binding = self._get_session_binding(page_id)

        # 直接绑定 MatrixPage session 元数据（Shell 不再直接调用）
        if self._matrix_page is not None:
            self._matrix_page.bind_session(
                binding.get("session_id"),
                entry_name=binding.get("entry_name"),
            )

            # 首次激活时加载表格数据
            if not self._matrix_page._matrix_table_initialized:
                try:
                    self._matrix_page.handle_page_activated()
                except Exception as e:
                    logger.error(f"Matrix表格延迟加载失败: {e}")

        return {
            "bound": True,
            "session_id": binding.get("session_id"),
            "entry_name": binding.get("entry_name"),
            "mode": binding.get("mode", "shared"),
            "consistency": consistency,
        }

    def on_page_hidden(self, page_id: str) -> bool:
        """
        当某个页面被隐藏时调用。

        Args:
            page_id: 页面标识符

        Returns:
            是否成功处理
        """
        if page_id != "matrix.main":
            return False

        manager = self.matrix_session_manager
        if hasattr(manager, "unbind_page_session"):
            return bool(manager.unbind_page_session(page_id))
        return False

    # =========================================================================
    # Page Provider API (Step 8)
    # =========================================================================
    # 这些方法将 MatrixPage 的构造和运行时操作从 shell 移动到 Matrix 边界

    def get_or_create_matrix_page(self, parent_view: QWidget, matrix_controller) -> "MatrixPage":
        """
        获取或创建 MatrixPage 实例。

        这是 shell 获取 Matrix page widget 的主要入口，替代直接构造 MatrixPage。

        Args:
            parent_view: 父视图组件
            matrix_controller: Matrix 控制器实例

        Returns:
            MatrixPage 实例
        """
        if self._matrix_page is None:
            from src.features.matrix.view.matrix_page import MatrixPage
            self._matrix_page = MatrixPage(matrix_controller, parent_view)
            self._matrix_controller = matrix_controller

        return self._matrix_page

    def get_matrix_page_widget(self) -> Optional["MatrixPage"]:
        """
        获取当前 Matrix page widget（如果已创建）。

        Returns:
            MatrixPage 实例或 None
        """
        return self._matrix_page

    def has_matrix_page(self) -> bool:
        """检查 MatrixPage 是否已创建"""
        return self._matrix_page is not None

    # =========================================================================
    # Page Runtime Delegation (Step 8)
    # =========================================================================
    # 这些方法将 shell 对 MatrixPage 的直接调用代理到 facade

    def sync_matrix_to_model(self) -> None:
        """代理 sync_to_model 调用"""
        if self._matrix_page is not None:
            self._matrix_page.sync_to_model()

    def refresh_matrix_table(self) -> None:
        """代理 refresh_table 调用"""
        if self._matrix_page is not None:
            self._matrix_page.refresh_table()

    def save_matrix_merged_cells_info(self) -> None:
        """代理 save_merged_cells_info 调用"""
        if self._matrix_page is not None:
            self._matrix_page.save_merged_cells_info()

    def auto_import_matrix_from_project(self) -> None:
        """代理 auto_import_from_project 调用"""
        if self._matrix_page is not None:
            self._matrix_page.auto_import_from_project()

    def set_matrix_project_context(self, project_context) -> None:
        """代理 set_project_context 调用"""
        if self._matrix_page is not None:
            self._matrix_page.set_project_context(project_context)

    def initialize_matrix_table(self) -> None:
        """代理 initialize_table 调用"""
        if self._matrix_page is not None:
            self._matrix_page.initialize_table()

    def _ensure_workspace_session_consistency(self, page_id: str) -> dict:
        """内部方法：确保 workspace session 与页面绑定一致"""
        orchestrator = self.matrix_session_orchestrator
        active_session_id = None
        bound_session_id = None

        if hasattr(orchestrator, "_manager"):
            manager = orchestrator._manager
            if hasattr(manager, "snapshot"):
                snapshot = manager.snapshot()
                active_session_id = getattr(snapshot, "active_session_id", None)
                page_bindings = dict(getattr(snapshot, "page_session_bindings", {}) or {})
                bound_session_id = page_bindings.get(page_id)
            elif hasattr(manager, "get_active_session_id"):
                active_session_id = manager.get_active_session_id()
                if hasattr(manager, "get_page_session_id"):
                    bound_session_id = manager.get_page_session_id(page_id)

        if not bound_session_id and active_session_id and hasattr(orchestrator, "bind_page_session"):
            result = orchestrator.bind_page_session(
                page_id,
                bound_session_id,
                expected_entry_names=("main", "new_file_pilot", "preview", "debug_preview"),
                requested_by="main_window.matrix_workspace.page_visible",
            )
            return {
                "success": bool(getattr(result, "success", False)),
                "reason": getattr(result, "reason", None),
                "rollback_performed": bool(getattr(result, "rollback_performed", False)),
            }

        return {"success": True, "reason": None, "rollback_performed": False}

    def _get_session_binding(self, page_id: str) -> dict:
        """内部方法：获取页面绑定的 session 信息"""
        manager = self.matrix_session_manager
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
                    "entry_name": session_entries.get(bound_session_id) or "main",
                    "mode": session_modes.get(bound_session_id, "shared"),
                }
            if active_session_id is not None:
                active_mode = session_modes.get(active_session_id, active_mode)
                active_entry_name = session_entries.get(active_session_id)

        if not active_session_id:
            return {
                "session_id": "main:shared",
                "entry_name": "main",
                "mode": "shared",
            }

        return {
            "session_id": active_session_id,
            "entry_name": active_entry_name or "main",
            "mode": active_mode,
        }
