from __future__ import annotations

from typing import Optional

from src.features.main_window.view.main_window_ui import MainWindow
from src.features.matrix.service.matrix_session_debug_facade import MatrixSessionDebugFacade
from src.features.matrix.service.matrix_session_entry_facade import MatrixSessionEntryFacade
from src.features.matrix.service.matrix_session_entry_policy import MatrixSessionEntryPolicyTable
from src.features.matrix.service.matrix_session_manager import MatrixSessionManager
from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator
from src.features.matrix.service.matrix_session_registry import MatrixSessionRegistry
from src.features.matrix.workspace.matrix_workspace_coordinator import (
    MatrixWorkspaceCoordinator,
)


def assemble_main_window(splash_screen=None) -> MainWindow:
    """
    Composition root for MainWindow.

    Default behavior remains shared. This only moves assembly ownership out of the UI layer,
    while keeping runtime behavior unchanged.
    """
    registry = MatrixSessionRegistry()
    entry_policies = MatrixSessionEntryPolicyTable()

    # The manager needs the view reference, but we can bind it inside MainWindow.__init__.
    session_manager = MatrixSessionManager(parent_view=None, registry=registry)
    orchestrator = MatrixSessionOrchestrator(session_manager)
    debug_facade = MatrixSessionDebugFacade(
        orchestrator=orchestrator,
        entry_policies=entry_policies,
    )
    entry_facade = MatrixSessionEntryFacade(
        entry_policies=entry_policies,
    )
    matrix_workspace_coordinator = MatrixWorkspaceCoordinator(
        matrix_session_registry=registry,
        matrix_session_entry_policies=entry_policies,
        matrix_session_manager=session_manager,
        matrix_session_orchestrator=orchestrator,
        matrix_session_debug_facade=debug_facade,
        matrix_session_entry_facade=entry_facade,
    )

    return MainWindow(
        splash_screen,
        matrix_workspace_coordinator=matrix_workspace_coordinator,
    )
