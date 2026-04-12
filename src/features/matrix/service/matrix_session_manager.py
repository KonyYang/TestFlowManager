from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from src.features.matrix.service.matrix_session_factory import MatrixSessionFactory
from src.features.matrix.service.matrix_session_registry import MatrixSessionRegistry

if TYPE_CHECKING:
    from src.features.matrix.service.matrix_session_components import (
        MatrixSessionComponents,
    )


@dataclass(frozen=True)
class ManagedMatrixSession:
    session_id: str
    mode: str
    entry_name: str | None
    components: "MatrixSessionComponents"
    scope: object | None = None


@dataclass(frozen=True)
class MatrixSessionManagerSnapshot:
    session_ids: tuple[str, ...]
    session_modes: dict[str, str]
    session_entries: dict[str, str]
    entry_counts: dict[str, int]
    active_isolated_session_ids: tuple[str, ...]
    active_session_id: str | None
    page_session_bindings: dict[str, str]
    total_sessions: int


class MatrixSessionManager:
    """Lightweight lifecycle manager for explicit matrix sessions."""

    def __init__(
        self,
        *,
        parent_view=None,
        registry: Optional[MatrixSessionRegistry] = None,
        session_factory=MatrixSessionFactory,
    ):
        self._parent_view = parent_view
        self._registry = registry
        self._session_factory = session_factory
        self._sessions: dict[str, ManagedMatrixSession] = {}
        self._active_session_id: str | None = None
        self._page_session_bindings: dict[str, str] = {}

    def bind_parent_view(self, parent_view) -> None:
        """
        Late-bind the Qt view (MainWindow / page host) used for assembling sessions.

        This enables moving composition ownership to the app layer without changing the
        MainWindow initialization order.
        """
        self._parent_view = parent_view

    def bind_registry(self, registry: Optional[MatrixSessionRegistry]) -> None:
        """Late-bind registry for mode routing (shared/isolated)."""
        self._registry = registry

    def create_or_get(
        self,
        session_id: str,
        *,
        mode: str = "isolated",
        entry_name: str | None = None,
    ) -> "MatrixSessionComponents":
        if not session_id:
            raise ValueError("session_id is required")
        if mode not in ("shared", "isolated"):
            raise ValueError(f"Unsupported matrix session mode: {mode}")

        existing = self._sessions.get(session_id)
        if existing is not None:
            return existing.components

        scope = None
        if self._registry is not None and hasattr(self._registry, "open_scope"):
            scope = self._registry.open_scope(session_id, mode=mode)

        try:
            components = self._session_factory.create(
                self._parent_view,
                mode=mode,
                registry=self._registry,
                session_id=session_id,
            )
        except Exception:
            if scope is not None and hasattr(scope, "close"):
                scope.close()
            raise

        self._sessions[session_id] = ManagedMatrixSession(
            session_id=session_id,
            mode=mode,
            entry_name=entry_name,
            components=components,
            scope=scope,
        )
        if self._active_session_id is None:
            self._active_session_id = session_id
        return components

    def register_existing(
        self,
        session_id: str,
        *,
        mode: str,
        entry_name: str | None,
        components: "MatrixSessionComponents",
        scope: object | None = None,
        set_active_if_none: bool = True,
    ) -> bool:
        """
        Registers externally-assembled session components into the manager without re-assembling.

        This is used to keep a single shared workspace session instance while letting the manager
        own page bindings, active-session selection, and close semantics.
        """
        if not session_id:
            raise ValueError("session_id is required")
        if mode not in ("shared", "isolated"):
            raise ValueError(f"Unsupported matrix session mode: {mode}")
        if components is None:
            raise ValueError("components is required")
        if session_id in self._sessions:
            return False

        self._sessions[session_id] = ManagedMatrixSession(
            session_id=session_id,
            mode=mode,
            entry_name=entry_name,
            components=components,
            scope=scope,
        )
        if set_active_if_none and self._active_session_id is None:
            self._active_session_id = session_id
        return True

    def get(self, session_id: str) -> Optional["MatrixSessionComponents"]:
        managed = self._sessions.get(session_id)
        if managed is None:
            return None
        return managed.components

    def close(self, session_id: str) -> bool:
        managed = self._sessions.pop(session_id, None)
        if managed is None:
            return False
        if self._active_session_id == session_id:
            self._active_session_id = None
        self._unbind_session_from_pages(session_id)

        if managed.scope is not None and hasattr(managed.scope, "close"):
            managed.scope.close()
            return True

        if (
            self._registry is not None
            and hasattr(self._registry, "release_session")
            and session_id
        ):
            self._registry.release_session(session_id)
        return True

    def list_session_ids(self) -> tuple[str, ...]:
        return tuple(self._sessions.keys())

    def activate(self, session_id: str) -> bool:
        if not session_id:
            return False
        if session_id not in self._sessions:
            return False
        self._active_session_id = session_id
        return True

    def get_active_session_id(self) -> str | None:
        return self._active_session_id

    def bind_page_session(self, page_id: str, session_id: str) -> bool:
        if not page_id or not session_id:
            return False
        if session_id not in self._sessions:
            return False
        self._page_session_bindings[page_id] = session_id
        return True

    def unbind_page_session(self, page_id: str) -> bool:
        if not page_id:
            return False
        return self._page_session_bindings.pop(page_id, None) is not None

    def get_page_session_id(self, page_id: str) -> str | None:
        if not page_id:
            return None
        return self._page_session_bindings.get(page_id)

    def get_page_session_bindings(self) -> dict[str, str]:
        return dict(self._page_session_bindings)

    def clear_page_session_bindings(self) -> tuple[str, ...]:
        page_ids = tuple(self._page_session_bindings.keys())
        self._page_session_bindings.clear()
        return page_ids

    def snapshot(self) -> MatrixSessionManagerSnapshot:
        session_ids = tuple(self._sessions.keys())
        session_modes = {sid: managed.mode for sid, managed in self._sessions.items()}
        session_entries = {
            sid: (managed.entry_name or "")
            for sid, managed in self._sessions.items()
            if managed.entry_name
        }
        entry_counts: dict[str, int] = {}
        for managed in self._sessions.values():
            if not managed.entry_name:
                continue
            entry_counts[managed.entry_name] = entry_counts.get(managed.entry_name, 0) + 1
        active_isolated_session_ids = tuple(
            sid for sid, managed in self._sessions.items() if managed.mode == "isolated"
        )
        return MatrixSessionManagerSnapshot(
            session_ids=session_ids,
            session_modes=session_modes,
            session_entries=session_entries,
            entry_counts=entry_counts,
            active_isolated_session_ids=active_isolated_session_ids,
            active_session_id=self._active_session_id,
            page_session_bindings=dict(self._page_session_bindings),
            total_sessions=len(session_ids),
        )

    def stats(self) -> dict:
        snap = self.snapshot()
        return {
            "total_sessions": snap.total_sessions,
            "session_ids": tuple(snap.session_ids),
            "session_modes": dict(snap.session_modes),
            "session_entries": dict(snap.session_entries),
            "entry_counts": dict(snap.entry_counts),
            "active_isolated_session_ids": tuple(snap.active_isolated_session_ids),
            "active_session_id": snap.active_session_id,
            "page_session_bindings": dict(snap.page_session_bindings),
        }

    def close_by_mode(self, mode: str) -> tuple[str, ...]:
        if mode not in ("shared", "isolated"):
            raise ValueError(f"Unsupported matrix session mode: {mode}")
        target_ids = [
            sid for sid, managed in self._sessions.items() if managed.mode == mode
        ]
        closed_ids = []
        for session_id in target_ids:
            if self.close(session_id):
                closed_ids.append(session_id)
        return tuple(closed_ids)

    def close_all(self) -> tuple[str, ...]:
        target_ids = list(self._sessions.keys())
        closed_ids = []
        for session_id in target_ids:
            if self.close(session_id):
                closed_ids.append(session_id)
        return tuple(closed_ids)

    def _unbind_session_from_pages(self, session_id: str) -> None:
        bound_pages = [
            page_id
            for page_id, bound_session_id in self._page_session_bindings.items()
            if bound_session_id == session_id
        ]
        for page_id in bound_pages:
            self._page_session_bindings.pop(page_id, None)
