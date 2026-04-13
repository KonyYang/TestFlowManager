from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QWidget

from src.features.matrix.service.matrix_session_entry_policy import MatrixSessionEntryPolicyTable
from src.features.matrix.service.matrix_session_manager import MatrixSessionManager
from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator
from src.features.matrix.service.matrix_session_debug_facade import MatrixSessionDebugFacade
from src.features.matrix.service.matrix_session_entry_facade import MatrixSessionEntryFacade
from src.features.matrix.service.matrix_session_registry import MatrixSessionRegistry
from src.features.matrix.workspace.matrix_workspace_coordinator import MatrixWorkspaceCoordinator


class MatrixWorkspaceFacade:
    """矩阵工作区协同件，封装 session 相关 lifecycle"""

    def __init__(
        self,
        parent_view: Optional[QWidget],
        matrix_session_registry: Optional[MatrixSessionRegistry] = None,
        matrix_session_entry_policies: Optional[MatrixSessionEntryPolicyTable] = None,
        matrix_session_manager: Optional[MatrixSessionManager] = None,
        matrix_session_orchestrator: Optional[MatrixSessionOrchestrator] = None,
        matrix_session_debug_facade: Optional[MatrixSessionDebugFacade] = None,
        matrix_session_entry_facade: Optional[MatrixSessionEntryFacade] = None,
        matrix_workspace_coordinator: Optional[MatrixWorkspaceCoordinator] = None,
    ):
        self.parent_view = parent_view
        self._matrix_page = None  # MatrixPage 引用，由 shell 注入
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
        return self.matrix_session_manager

    # =========================================================================
    # Page Visibility Handlers
    # =========================================================================
    # 这些方法由 MainWindowController 调用，用于处理页面切换时的 Matrix 逻辑。
    # Shell 不应知道 matrix.main 的内部绑定规则。

    def set_matrix_page(self, matrix_page) -> None:
        """
        注入 MatrixPage 引用，使 facade 可以直接操作页面。

        Args:
            matrix_page: MatrixPage 实例
        """
        self._matrix_page = matrix_page

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
