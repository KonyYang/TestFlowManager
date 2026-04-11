from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from src.features.matrix.service.matrix_session_entry_policy import MatrixSessionEntryPolicyTable


@dataclass(frozen=True)
class MatrixSessionEntryConfig:
    mode: str
    session_id: str | None = None


class MatrixSessionEntryFacade:
    """Facade for session-entry strategy resolution."""

    NEW_FILE_ISOLATED_PILOT_GATE = "TFM_MATRIX_SESSION_ISOLATED_PILOT"
    _TRUTHY_SWITCH_VALUES = frozenset({"1", "true", "yes", "on"})

    def __init__(self, *, entry_policies=None):
        self._entry_policies = entry_policies or MatrixSessionEntryPolicyTable()

    @classmethod
    def is_new_file_pilot_enabled(cls, env: Mapping[str, str] | None = None) -> bool:
        env_map = env or {}
        value = env_map.get(cls.NEW_FILE_ISOLATED_PILOT_GATE, "")
        return value.strip().lower() in cls._TRUTHY_SWITCH_VALUES

    def resolve_new_file_session_config(self, *, pilot_enabled: bool) -> MatrixSessionEntryConfig:
        if not pilot_enabled:
            return MatrixSessionEntryConfig(mode="shared", session_id=None)

        policy = self._entry_policies.get(MatrixSessionEntryPolicyTable.NEW_FILE_PILOT)
        return MatrixSessionEntryConfig(
            mode=policy.mode,
            session_id=policy.fixed_session_id,
        )
