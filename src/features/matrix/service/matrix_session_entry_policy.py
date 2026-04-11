from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MatrixSessionEntryPolicy:
    mode: str
    fixed_session_id: Optional[str] = None
    session_id_prefix: Optional[str] = None


class MatrixSessionEntryPolicyTable:
    """
    Lightweight entry-policy table for non-default matrix sessionized entries.
    """

    NEW_FILE_PILOT = "new_file_pilot"
    PREVIEW = "preview"
    DEBUG_PREVIEW = "debug_preview"

    def __init__(self):
        self._policies = {
            self.NEW_FILE_PILOT: MatrixSessionEntryPolicy(
                mode="isolated",
                fixed_session_id="pilot:new-file",
            ),
            self.PREVIEW: MatrixSessionEntryPolicy(
                mode="isolated",
            ),
            self.DEBUG_PREVIEW: MatrixSessionEntryPolicy(
                mode="isolated",
                session_id_prefix="debug:preview:",
            ),
        }

    def get(self, entry_name: str) -> MatrixSessionEntryPolicy:
        policy = self._policies.get(entry_name)
        if policy is None:
            raise KeyError(f"Unknown matrix session entry policy: {entry_name}")
        return policy

