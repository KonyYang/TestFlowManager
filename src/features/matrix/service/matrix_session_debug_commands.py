class MatrixSessionDebugCommands:
    # Phase-9 temporary channel:
    # debug shortcuts are kept for transition diagnostics only,
    # and should not be promoted as primary business entry.
    TEMPORARY_DEBUG_CHANNEL = True

    @staticmethod
    def format_state_status(action: str, state: dict) -> str:
        return (
            f"[debug:{action}] preview={len(state['preview_session_ids'])} "
            f"active_isolated={len(state['registry_active_isolated_session_ids'])} "
            f"default_mode={state['registry_default_mode']}"
        )

    @staticmethod
    def format_switch_failed(reason: str, session_id: str) -> str:
        return f"[debug:switch:failed] reason={reason} session_id={session_id}"

    @staticmethod
    def format_switch_success(session_id: str, entry_name: str, state: dict) -> str:
        return (
            f"[debug:switch] switched_to={session_id} entry={entry_name} "
            f"preview={len(state['preview_session_ids'])} "
            f"active_isolated={len(state['registry_active_isolated_session_ids'])} "
            f"default_mode={state['registry_default_mode']}"
        )
