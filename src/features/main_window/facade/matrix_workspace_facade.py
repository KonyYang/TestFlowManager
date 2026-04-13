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

    def get_matrix_project_controller(self):
        if self._shared_session is None:
            return None
        return getattr(self._shared_session, "matrix_project_controller", None)

    def ensure_preview_session_manager(self) -> MatrixSessionManager:
        return self.matrix_session_manager

    def ensure_matrix_workspace_coordinator(self) -> MatrixWorkspaceCoordinator:
        return self.matrix_workspace_coordinator
