from types import SimpleNamespace

from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator


def test_matrix_session_orchestrator_open_switch_close_routes_to_manager():
    calls = []
    manager = SimpleNamespace(
        create_or_get=lambda session_id, **kwargs: (
            calls.append(("open", session_id, kwargs.get("mode"), kwargs.get("entry_name")))
            or "session-components"
        ),
        get=lambda session_id: calls.append(("switch", session_id)) or "target-components",
        activate=lambda session_id: calls.append(("activate", session_id)) or True,
        get_active_session_id=lambda: "preview:a",
        close=lambda session_id: calls.append(("close", session_id)) or True,
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    opened = orchestrator.open_session("preview:a", mode="isolated", entry_name="preview")
    switched = orchestrator.switch_to_session("preview:a")
    closed = orchestrator.close_session("preview:a")

    assert opened == "session-components"
    assert switched.success is True
    assert switched.session_id == "preview:a"
    assert switched.reason is None
    assert switched.session == "target-components"
    assert switched.entry_name is None
    assert switched.active_session_id == "preview:a"
    assert switched.rollback_performed is False
    assert closed is True
    assert calls == [
        ("open", "preview:a", "isolated", "preview"),
        ("switch", "preview:a"),
        ("activate", "preview:a"),
        ("close", "preview:a"),
    ]


def test_matrix_session_orchestrator_switch_to_session_returns_not_found():
    manager = SimpleNamespace(get=lambda session_id: None)
    orchestrator = MatrixSessionOrchestrator(manager)

    result = orchestrator.switch_to_session("preview:missing")

    assert result.success is False
    assert result.session_id == "preview:missing"
    assert result.reason == MatrixSessionOrchestrator.SWITCH_REASON_SESSION_NOT_FOUND
    assert result.session is None
    assert result.entry_name is None


def test_matrix_session_orchestrator_switch_to_session_returns_missing_id():
    manager = SimpleNamespace(get=lambda session_id: object())
    orchestrator = MatrixSessionOrchestrator(manager)

    result = orchestrator.switch_to_session("")

    assert result.success is False
    assert result.reason == MatrixSessionOrchestrator.SWITCH_REASON_MISSING_SESSION_ID
    assert result.entry_name is None


def test_matrix_session_orchestrator_switch_to_session_returns_entry_name_from_snapshot():
    manager = SimpleNamespace(
        get=lambda session_id: "session",
        snapshot=lambda: SimpleNamespace(
            session_entries={"preview:a": "preview"},
        ),
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    result = orchestrator.switch_to_session("preview:a")

    assert result.success is True
    assert result.entry_name == "preview"


def test_matrix_session_orchestrator_switch_to_session_rejects_disallowed_entry():
    manager = SimpleNamespace(
        get=lambda session_id: "session",
        snapshot=lambda: SimpleNamespace(
            session_entries={"preview:a": "new_file_pilot"},
        ),
        get_active_session_id=lambda: "preview:active",
        activate=lambda session_id: True,
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    result = orchestrator.switch_to_session(
        "preview:a",
        expected_entry_names=("preview", "debug_preview"),
        requested_by="test.switch",
    )

    assert result.success is False
    assert result.reason == MatrixSessionOrchestrator.SWITCH_REASON_ENTRY_NOT_ALLOWED
    assert result.entry_name == "new_file_pilot"
    assert result.requested_by == "test.switch"
    assert result.previous_active_session_id == "preview:active"
    assert result.active_session_id == "preview:active"
    assert result.rollback_performed is True


def test_matrix_session_orchestrator_switch_to_session_reports_activation_failure():
    manager = SimpleNamespace(
        get=lambda session_id: "session",
        snapshot=lambda: SimpleNamespace(
            session_entries={"preview:a": "preview"},
        ),
        get_active_session_id=lambda: "preview:active",
        activate=lambda session_id: False,
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    result = orchestrator.switch_to_session(
        "preview:a",
        expected_entry_names=("preview",),
        requested_by="test.switch",
    )

    assert result.success is False
    assert result.reason == MatrixSessionOrchestrator.SWITCH_REASON_ACTIVATION_FAILED
    assert result.entry_name == "preview"
    assert result.requested_by == "test.switch"
    assert result.previous_active_session_id == "preview:active"
    assert result.active_session_id == "preview:active"
    assert result.rollback_performed is True


def test_matrix_session_orchestrator_debug_open_generates_incremental_session_id():
    calls = []
    manager = SimpleNamespace(
        create_or_get=lambda session_id, **kwargs: (
            calls.append((session_id, kwargs.get("mode"), kwargs.get("entry_name")))
            or "session"
        ),
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    first_id, _ = orchestrator.open_debug_preview(
        session_id_prefix="debug:preview:",
        mode="isolated",
        entry_name="debug_preview",
    )
    second_id, _ = orchestrator.open_debug_preview(
        session_id_prefix="debug:preview:",
        mode="isolated",
        entry_name="debug_preview",
    )

    assert first_id == "debug:preview:1"
    assert second_id == "debug:preview:2"
    assert calls == [
        ("debug:preview:1", "isolated", "debug_preview"),
        ("debug:preview:2", "isolated", "debug_preview"),
    ]


def test_matrix_session_orchestrator_debug_close_uses_last_opened_when_no_input():
    closed = []
    manager = SimpleNamespace(
        create_or_get=lambda session_id, **kwargs: "session",
        close=lambda session_id: closed.append(session_id) or True,
    )
    orchestrator = MatrixSessionOrchestrator(manager)
    orchestrator.open_debug_preview(session_id="debug:preview:9")

    ok, session_id = orchestrator.close_debug_preview()

    assert ok is True
    assert session_id == "debug:preview:9"
    assert closed == ["debug:preview:9"]


def test_matrix_session_orchestrator_debug_close_returns_false_without_target():
    manager = SimpleNamespace(close=lambda session_id: True)
    orchestrator = MatrixSessionOrchestrator(manager)

    ok, session_id = orchestrator.close_debug_preview()

    assert ok is False
    assert session_id is None


def test_matrix_session_orchestrator_get_debug_state_uses_manager_and_registry_snapshots():
    manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            session_ids=("preview:a",),
            session_modes={"preview:a": "isolated"},
            session_entries={"preview:a": "preview"},
            entry_counts={"preview": 1},
            active_isolated_session_ids=("preview:a",),
            total_sessions=1,
        )
    )
    orchestrator = MatrixSessionOrchestrator(manager)
    registry_snapshot = SimpleNamespace(
        default_mode="shared",
        session_modes={"preview:a": "isolated"},
        active_isolated_session_ids=("preview:a",),
        has_default_isolated_instance=False,
    )

    state = orchestrator.get_debug_state(registry_snapshot=registry_snapshot)

    assert state == {
        "preview_session_ids": ("preview:a",),
        "registry_default_mode": "shared",
        "registry_session_modes": {"preview:a": "isolated"},
        "registry_active_isolated_session_ids": ("preview:a",),
        "registry_has_default_isolated_instance": False,
        "manager_total_sessions": 1,
        "manager_session_modes": {"preview:a": "isolated"},
        "manager_session_entries": {"preview:a": "preview"},
        "manager_entry_counts": {"preview": 1},
        "manager_active_isolated_session_ids": ("preview:a",),
        "last_debug_preview_session_id": None,
    }


def test_matrix_session_orchestrator_get_debug_state_defaults_without_registry_snapshot():
    manager = SimpleNamespace(
        list_session_ids=lambda: ("preview:a", "preview:b")
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    state = orchestrator.get_debug_state(registry_snapshot=None)

    assert state["preview_session_ids"] == ("preview:a", "preview:b")
    assert state["registry_default_mode"] is None
    assert state["manager_total_sessions"] == 2
    assert state["last_debug_preview_session_id"] is None


def test_matrix_session_orchestrator_bind_page_session_uses_switch_contract_then_binds():
    calls = []
    manager = SimpleNamespace(
        get=lambda session_id: "session",
        activate=lambda session_id: True,
        get_active_session_id=lambda: "preview:a",
        bind_page_session=lambda page_id, session_id: (
            calls.append((page_id, session_id)) or True
        ),
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    result = orchestrator.bind_page_session(
        "matrix.main",
        "preview:a",
        requested_by="test.page_bind",
    )

    assert result.success is True
    assert result.session_id == "preview:a"
    assert result.requested_by == "test.page_bind"
    assert calls == [("matrix.main", "preview:a")]


def test_matrix_session_orchestrator_bind_page_session_fails_when_manager_rejects_binding():
    manager = SimpleNamespace(
        get=lambda session_id: "session",
        activate=lambda session_id: True,
        get_active_session_id=lambda: "preview:a",
        bind_page_session=lambda page_id, session_id: False,
    )
    orchestrator = MatrixSessionOrchestrator(manager)

    result = orchestrator.bind_page_session("matrix.main", "preview:a")

    assert result.success is False
    assert result.reason == MatrixSessionOrchestrator.SWITCH_REASON_ACTIVATION_FAILED
    assert result.rollback_performed is True
