"""
Matrix workspace coordination helper.

This module centralizes the shared/matrix session composition and exposes a
single point for later page/ProjectContext integration.
"""

from typing import Optional

from src.features.matrix.controller.matrix_project_controller import MatrixProjectController
from src.features.matrix.service.matrix_session_components import (
    MatrixSessionComponents,
)
from src.features.matrix.service.matrix_session_factory import MatrixSessionFactory
from src.features.matrix.service.matrix_session_manager import MatrixSessionManager
from src.features.matrix.service.matrix_session_registry import MatrixSessionRegistry
from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator
from src.features.matrix.service.matrix_session_debug_facade import MatrixSessionDebugFacade
from src.features.matrix.service.matrix_session_entry_facade import MatrixSessionEntryFacade
from src.features.matrix.service.matrix_session_entry_policy import (
    MatrixSessionEntryPolicyTable,
)


DEFAULT_MATRIX_SESSION_ID = "main:shared"
DEFAULT_MATRIX_ENTRY_NAME = "main"


class MatrixWorkspaceCoordinator:
    """
    Encapsulates Matrix session assembly, registration, and helper facades.
    """

    def __init__(
        self,
        parent_view=None,
        *,
        matrix_session_registry: Optional[MatrixSessionRegistry] = None,
        matrix_session_manager: Optional[MatrixSessionManager] = None,
        matrix_session_orchestrator: Optional[MatrixSessionOrchestrator] = None,
        matrix_session_debug_facade: Optional[MatrixSessionDebugFacade] = None,
        matrix_session_entry_facade: Optional[MatrixSessionEntryFacade] = None,
        matrix_session_entry_policies: Optional[MatrixSessionEntryPolicyTable] = None,
    ):
        self.parent_view = parent_view
        self.matrix_session_registry = matrix_session_registry or MatrixSessionRegistry()
        self._matrix_session_entry_policies = (
            matrix_session_entry_policies or MatrixSessionEntryPolicyTable()
        )
        self.matrix_session_manager = matrix_session_manager or MatrixSessionManager(
            parent_view=self.parent_view,
            registry=self.matrix_session_registry,
        )
        self.matrix_session_orchestrator = matrix_session_orchestrator or MatrixSessionOrchestrator(
            self.matrix_session_manager
        )
        self.matrix_session_debug_facade = matrix_session_debug_facade or MatrixSessionDebugFacade(
            orchestrator=self.matrix_session_orchestrator,
            entry_policies=self._matrix_session_entry_policies,
        )
        self.matrix_session_entry_facade = matrix_session_entry_facade or MatrixSessionEntryFacade(
            entry_policies=self._matrix_session_entry_policies
        )
        self._shared_matrix_session: Optional[MatrixSessionComponents] = None
        self.matrix_project_controller: Optional[MatrixProjectController] = None

    @property
    def entry_policies(self) -> MatrixSessionEntryPolicyTable:
        return self._matrix_session_entry_policies

    def bind_parent_view(self, parent_view) -> None:
        """Bind the parent view to the manager so it can access QWidget assistance."""
        if parent_view:
            self.parent_view = parent_view
            if hasattr(self.matrix_session_manager, "bind_parent_view"):
                self.matrix_session_manager.bind_parent_view(parent_view)

    def assemble_shared_session(
        self,
        parent_view=None,
        *,
        session_id: str = DEFAULT_MATRIX_SESSION_ID,
        entry_name: str = DEFAULT_MATRIX_ENTRY_NAME,
    ) -> MatrixSessionComponents:
        """
        Ensure the shared Matrix session exists and is registered with the manager.
        """
        if self._shared_matrix_session is not None:
            return self._shared_matrix_session

        matrix_view_parent = parent_view or self.parent_view
        session_components = MatrixSessionFactory.create(
            matrix_view_parent,
            registry=self.matrix_session_registry,
            session_id=session_id,
        )

        self._shared_matrix_session = session_components
        self.matrix_project_controller = session_components.matrix_project_controller

        self._register_shared_session(
            session_id=session_id,
            entry_name=entry_name,
            components=session_components,
        )

        return session_components

    def _register_shared_session(
        self,
        session_id: str,
        entry_name: str,
        *,
        mode: str = "shared",
        components: Optional[MatrixSessionComponents] = None,
    ) -> None:
        manager = self.matrix_session_manager
        if hasattr(manager, "register_existing"):
            try:
                manager.register_existing(
                    session_id,
                    mode=mode,
                    entry_name=entry_name,
                    components=components or self._shared_matrix_session,
                )
            except Exception:
                # best effort registration; failure should not break startup
                pass

    def has_shared_session(self) -> bool:
        return self._shared_matrix_session is not None

    def get_matrix_project_controller(self) -> Optional[MatrixProjectController]:
        return self.matrix_project_controller

    def get_matrix_controller(self):
        if not self.matrix_project_controller:
            return None
        return self.matrix_project_controller.matrix_controller
