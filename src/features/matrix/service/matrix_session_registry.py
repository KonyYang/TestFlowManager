from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.features.matrix.service.matrix_service import MatrixService
from src.features.matrix.service.matrix_service_provider import MatrixServiceProvider


@dataclass
class MatrixSessionRegistryStatus:
    mode: str
    session_id: Optional[str] = None


@dataclass(frozen=True)
class MatrixSessionRegistrySnapshot:
    default_mode: str
    session_modes: dict[str, str]
    active_isolated_session_ids: tuple[str, ...]
    has_default_isolated_instance: bool


class MatrixSessionScope:
    """Lightweight lifecycle wrapper for session-scoped matrix routing."""

    def __init__(self, registry: "MatrixSessionRegistry", session_id: str, mode: str):
        self._registry = registry
        self.session_id = session_id
        self.mode = mode
        self._closed = False
        self._registry.set_mode(mode, session_id=session_id)

    def close(self) -> None:
        if self._closed:
            return
        self._registry.release_session(self.session_id)
        self._closed = True

    def __enter__(self) -> "MatrixSessionScope":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class MatrixSessionRegistry:
    """
    Tracks the current Matrix service mode (shared/isolated) and wires it into MatrixServiceProvider.

    Scope: a single "current" choice, not a multi-session container.
    """

    def __init__(self, *, initial_mode: str = "shared"):
        self._mode = "shared"
        self._shared_service_factory = MatrixService.shared
        self._isolated_instance: Optional[MatrixService] = None
        self._session_modes: dict[str, str] = {}
        self._session_isolated_instances: dict[str, MatrixService] = {}
        self.set_mode(initial_mode)

    def status(self, *, session_id: Optional[str] = None) -> MatrixSessionRegistryStatus:
        return MatrixSessionRegistryStatus(
            mode=self._resolve_mode(session_id),
            session_id=session_id,
        )

    def install(self) -> None:
        MatrixServiceProvider.set_provider(self)

    def uninstall(self) -> None:
        MatrixServiceProvider.reset_provider()

    def set_mode(self, mode: str, *, session_id: Optional[str] = None) -> None:
        if mode not in ("shared", "isolated"):
            raise ValueError(f"Unsupported Matrix session mode: {mode}")
        if session_id is None:
            if mode != self._mode:
                self._mode = mode
                if mode == "isolated":
                    self._isolated_instance = None
            return

        current_mode = self._session_modes.get(session_id, self._mode)
        self._session_modes[session_id] = mode
        if mode == "isolated" and current_mode != "isolated":
            self._session_isolated_instances.pop(session_id, None)

    def reset(self) -> None:
        self._shared_service_factory = MatrixService.shared
        self._isolated_instance = None
        self._mode = "shared"
        self._session_modes.clear()
        self._session_isolated_instances.clear()

    # Provider protocol expected by MatrixServiceProvider
    def get_service(self, *, session_id: Optional[str] = None) -> MatrixService:
        mode = self._resolve_mode(session_id)
        if mode == "shared":
            return self._shared_service_factory()

        if session_id is None:
            if self._isolated_instance is None:
                self._isolated_instance = MatrixService.create_isolated()
            return self._isolated_instance

        isolated_instance = self._session_isolated_instances.get(session_id)
        if isolated_instance is None:
            isolated_instance = MatrixService.create_isolated()
            self._session_isolated_instances[session_id] = isolated_instance
        return isolated_instance

    def release_session(self, session_id: str) -> None:
        self._session_modes.pop(session_id, None)
        self._session_isolated_instances.pop(session_id, None)

    def open_scope(self, session_id: str, *, mode: str) -> MatrixSessionScope:
        return MatrixSessionScope(self, session_id, mode)

    def list_isolated_session_ids(self) -> tuple[str, ...]:
        return tuple(self._session_isolated_instances.keys())

    def get_session_modes(self) -> dict[str, str]:
        """Returns a copy of session_id -> mode routing map."""
        return dict(self._session_modes)

    def get_active_isolated_session_ids(self) -> tuple[str, ...]:
        """Returns current active isolated session ids."""
        return tuple(self._session_isolated_instances.keys())

    def snapshot(self) -> MatrixSessionRegistrySnapshot:
        """Read-only diagnostic snapshot for debugging and tests."""
        return MatrixSessionRegistrySnapshot(
            default_mode=self._mode,
            session_modes=dict(self._session_modes),
            active_isolated_session_ids=tuple(self._session_isolated_instances.keys()),
            has_default_isolated_instance=self._isolated_instance is not None,
        )

    def set_service_factory(self, service_factory) -> None:
        # This is only meaningful in shared mode; keep it for backward compat.
        self._shared_service_factory = service_factory

    def reset_service_factory(self) -> None:
        self._shared_service_factory = MatrixService.shared

    def _resolve_mode(self, session_id: Optional[str]) -> str:
        if session_id is None:
            return self._mode
        return self._session_modes.get(session_id, self._mode)
