from __future__ import annotations

from typing import Optional

from src.features.matrix.service.matrix_session_entry_policy import MatrixSessionEntryPolicyTable
from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator


class MatrixSessionDebugFacade:
    """Thin facade for non-default matrix session debug operations."""

    SWITCHABLE_PREVIEW_ENTRIES = (
        MatrixSessionEntryPolicyTable.PREVIEW,
        MatrixSessionEntryPolicyTable.DEBUG_PREVIEW,
    )
    SWITCH_REQUESTED_BY = "main_window.debug_preview_switch"

    def __init__(
        self,
        *,
        orchestrator: MatrixSessionOrchestrator,
        entry_policies=None,
    ):
        self._orchestrator = orchestrator
        self._entry_policies = entry_policies or MatrixSessionEntryPolicyTable()

    def _get_policy(self, entry_name: str):
        return self._entry_policies.get(entry_name)

    def open_preview_session(
        self,
        session_id: str,
        *,
        entry_name: str = MatrixSessionEntryPolicyTable.PREVIEW,
    ):
        policy = self._get_policy(MatrixSessionEntryPolicyTable.PREVIEW)
        return self._orchestrator.open_session(
            session_id,
            mode=policy.mode,
            entry_name=entry_name,
        )

    def close_preview_session(self, session_id: str) -> bool:
        return self._orchestrator.close_session(session_id)

    def open_debug_preview_session(self, session_id: Optional[str] = None):
        policy = self._get_policy(MatrixSessionEntryPolicyTable.DEBUG_PREVIEW)
        return self._orchestrator.open_debug_preview(
            session_id=session_id,
            mode=policy.mode,
            session_id_prefix=policy.session_id_prefix or "debug:preview:",
            entry_name=MatrixSessionEntryPolicyTable.DEBUG_PREVIEW,
        )

    def close_debug_preview_session(self, session_id: Optional[str] = None):
        return self._orchestrator.close_debug_preview(session_id=session_id)

    def switch_preview_session(self, session_id: str):
        return self._orchestrator.switch_to_session(
            session_id,
            expected_entry_names=self.SWITCHABLE_PREVIEW_ENTRIES,
            requested_by=self.SWITCH_REQUESTED_BY,
        )

    def get_debug_state(self, registry_snapshot=None) -> dict:
        return self._orchestrator.get_debug_state(registry_snapshot=registry_snapshot)
