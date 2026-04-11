from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.matrix.service.matrix_session_manager import MatrixSessionManager


@dataclass(frozen=True)
class SessionSwitchResult:
    success: bool
    session_id: str
    reason: str | None = None
    session: object | None = None
    entry_name: str | None = None
    requested_by: str | None = None
    previous_active_session_id: str | None = None
    active_session_id: str | None = None
    rollback_performed: bool = False


class MatrixSessionOrchestrator:
    """Minimal session orchestration layer for non-default matrix entries."""

    DEBUG_PREVIEW_KEY = "debug_preview"
    SWITCH_REASON_MISSING_SESSION_ID = "missing_session_id"
    SWITCH_REASON_SESSION_NOT_FOUND = "session_not_found"
    SWITCH_REASON_ENTRY_NOT_ALLOWED = "entry_not_allowed"
    SWITCH_REASON_ACTIVATION_FAILED = "activation_failed"

    def __init__(self, manager: "MatrixSessionManager"):
        self._manager = manager
        self._debug_preview_counter = 0
        self._last_debug_preview_session_id: Optional[str] = None

    def open_session(
        self,
        session_id: str,
        *,
        mode: str = "isolated",
        entry_name: str = "preview",
    ):
        return self._manager.create_or_get(
            session_id,
            mode=mode,
            entry_name=entry_name,
        )

    def switch_to_session(
        self,
        session_id: str,
        *,
        expected_entry_names: tuple[str, ...] | None = None,
        requested_by: str | None = None,
    ) -> SessionSwitchResult:
        if not session_id:
            return SessionSwitchResult(
                success=False,
                session_id=session_id,
                reason=self.SWITCH_REASON_MISSING_SESSION_ID,
                requested_by=requested_by,
            )

        session = self._manager.get(session_id)
        if session is None:
            return SessionSwitchResult(
                success=False,
                session_id=session_id,
                reason=self.SWITCH_REASON_SESSION_NOT_FOUND,
                requested_by=requested_by,
            )

        entry_name = self._resolve_entry_name(session_id)
        previous_active_session_id = self._get_active_session_id()
        allowed_entries = set(expected_entry_names or ())
        if allowed_entries and entry_name is not None and entry_name not in allowed_entries:
            return SessionSwitchResult(
                success=False,
                session_id=session_id,
                reason=self.SWITCH_REASON_ENTRY_NOT_ALLOWED,
                session=session,
                entry_name=entry_name,
                requested_by=requested_by,
                previous_active_session_id=previous_active_session_id,
                active_session_id=previous_active_session_id,
                rollback_performed=True,
            )

        if hasattr(self._manager, "activate"):
            activated = self._manager.activate(session_id)
            if not activated:
                return SessionSwitchResult(
                    success=False,
                    session_id=session_id,
                    reason=self.SWITCH_REASON_ACTIVATION_FAILED,
                    session=session,
                    entry_name=entry_name,
                    requested_by=requested_by,
                    previous_active_session_id=previous_active_session_id,
                    active_session_id=self._get_active_session_id(),
                    rollback_performed=True,
                )

        return SessionSwitchResult(
            success=True,
            session_id=session_id,
            reason=None,
            session=session,
            entry_name=entry_name,
            requested_by=requested_by,
            previous_active_session_id=previous_active_session_id,
            active_session_id=self._get_active_session_id() or session_id,
            rollback_performed=False,
        )

    def close_session(self, session_id: str) -> bool:
        return self._manager.close(session_id)

    def bind_page_session(
        self,
        page_id: str,
        session_id: str,
        *,
        expected_entry_names: tuple[str, ...] | None = None,
        requested_by: str | None = None,
    ) -> SessionSwitchResult:
        switch_result = self.switch_to_session(
            session_id,
            expected_entry_names=expected_entry_names,
            requested_by=requested_by,
        )
        if not switch_result.success:
            return switch_result
        if not hasattr(self._manager, "bind_page_session"):
            return switch_result
        bound = self._manager.bind_page_session(page_id, session_id)
        if bound:
            return switch_result
        return SessionSwitchResult(
            success=False,
            session_id=session_id,
            reason=self.SWITCH_REASON_ACTIVATION_FAILED,
            session=switch_result.session,
            entry_name=switch_result.entry_name,
            requested_by=requested_by,
            previous_active_session_id=switch_result.previous_active_session_id,
            active_session_id=switch_result.active_session_id,
            rollback_performed=True,
        )

    def get_bound_session_for_page(self, page_id: str) -> str | None:
        if hasattr(self._manager, "get_page_session_id"):
            return self._manager.get_page_session_id(page_id)
        return None

    def open_debug_preview(
        self,
        *,
        session_id: Optional[str] = None,
        mode: str = "isolated",
        session_id_prefix: str = "debug:preview:",
        entry_name: str = "debug_preview",
    ) -> tuple[str, object]:
        target_id = session_id
        if not target_id:
            self._debug_preview_counter += 1
            target_id = f"{session_id_prefix}{self._debug_preview_counter}"

        session = self.open_session(
            target_id,
            mode=mode,
            entry_name=entry_name,
        )
        self._last_debug_preview_session_id = target_id
        return target_id, session

    def close_debug_preview(self, session_id: Optional[str] = None) -> tuple[bool, Optional[str]]:
        target_id = session_id or self._last_debug_preview_session_id
        if not target_id:
            return False, None

        closed = self.close_session(target_id)
        if closed and target_id == self._last_debug_preview_session_id:
            self._last_debug_preview_session_id = None
        return closed, target_id

    def get_debug_state(self, registry_snapshot=None) -> dict:
        preview_session_ids = ()
        manager_session_modes = {}
        manager_session_entries = {}
        manager_entry_counts = {}
        manager_active_isolated_session_ids = ()
        manager_total_sessions = 0

        manager = getattr(self, "_manager", None)
        if manager is not None and hasattr(manager, "snapshot"):
            manager_snapshot = manager.snapshot()
            preview_session_ids = tuple(getattr(manager_snapshot, "session_ids", ()) or ())
            manager_session_modes = dict(
                getattr(manager_snapshot, "session_modes", {}) or {}
            )
            manager_session_entries = dict(
                getattr(manager_snapshot, "session_entries", {}) or {}
            )
            manager_entry_counts = dict(
                getattr(manager_snapshot, "entry_counts", {}) or {}
            )
            manager_active_isolated_session_ids = tuple(
                getattr(manager_snapshot, "active_isolated_session_ids", ()) or ()
            )
            manager_total_sessions = int(
                getattr(manager_snapshot, "total_sessions", len(preview_session_ids)) or 0
            )
        elif manager is not None and hasattr(manager, "list_session_ids"):
            preview_session_ids = tuple(manager.list_session_ids())
            manager_total_sessions = len(preview_session_ids)

        if registry_snapshot is not None:
            return {
                "preview_session_ids": preview_session_ids,
                "registry_default_mode": registry_snapshot.default_mode,
                "registry_session_modes": dict(registry_snapshot.session_modes),
                "registry_active_isolated_session_ids": tuple(
                    registry_snapshot.active_isolated_session_ids
                ),
                "registry_has_default_isolated_instance": bool(
                    registry_snapshot.has_default_isolated_instance
                ),
                "manager_total_sessions": manager_total_sessions,
                "manager_session_modes": manager_session_modes,
                "manager_session_entries": manager_session_entries,
                "manager_entry_counts": manager_entry_counts,
                "manager_active_isolated_session_ids": manager_active_isolated_session_ids,
                "last_debug_preview_session_id": self._last_debug_preview_session_id,
            }

        return {
            "preview_session_ids": preview_session_ids,
            "registry_default_mode": None,
            "registry_session_modes": {},
            "registry_active_isolated_session_ids": (),
            "registry_has_default_isolated_instance": False,
            "manager_total_sessions": manager_total_sessions,
            "manager_session_modes": manager_session_modes,
            "manager_session_entries": manager_session_entries,
            "manager_entry_counts": manager_entry_counts,
            "manager_active_isolated_session_ids": manager_active_isolated_session_ids,
            "last_debug_preview_session_id": self._last_debug_preview_session_id,
        }

    def _resolve_entry_name(self, session_id: str) -> str | None:
        if hasattr(self._manager, "snapshot"):
            snapshot = self._manager.snapshot()
            entries = dict(getattr(snapshot, "session_entries", {}) or {})
            return entries.get(session_id)
        return None

    def _get_active_session_id(self) -> str | None:
        if hasattr(self._manager, "get_active_session_id"):
            return self._manager.get_active_session_id()
        return None
