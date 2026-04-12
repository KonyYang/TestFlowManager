import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path

from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator


def _ensure_stub_module(module_name: str, attrs: dict):
    module = types.ModuleType(module_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module_name] = module


def _load_matrix_session_manager_module():
    module_name = "test_integration_matrix_session_manager_module"
    if module_name in sys.modules:
        del sys.modules[module_name]

    @dataclass(frozen=True)
    class StubMatrixSessionComponents:
        matrix_controller: object
        matrix_project_controller: object

    class StubMatrixSessionFactory:
        @staticmethod
        def create(parent_view=None, mode="shared", **kwargs):
            session_id = kwargs.get("session_id")
            return StubMatrixSessionComponents(
                matrix_controller=f"controller:{mode}:{session_id}",
                matrix_project_controller=f"project:{mode}:{session_id}",
            )

    _ensure_stub_module(
        "src.features.matrix.service.matrix_session_factory",
        {
            "MatrixSessionFactory": StubMatrixSessionFactory,
            "MatrixSessionComponents": StubMatrixSessionComponents,
        },
    )
    _ensure_stub_module(
        "src.features.matrix.service.matrix_session_registry",
        {"MatrixSessionRegistry": type("MatrixSessionRegistry", (), {})},
    )

    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "matrix"
        / "service"
        / "matrix_session_manager.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_session_transition_shared_isolated_shared_consistency():
    module = _load_matrix_session_manager_module()
    released = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: released.append(session_id)),
        release_session=lambda session_id: released.append(f"release:{session_id}"),
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)
    orchestrator = MatrixSessionOrchestrator(manager)

    orchestrator.open_session("main:shared", mode="shared", entry_name="main")
    assert manager.get_active_session_id() == "main:shared"

    orchestrator.open_session(
        "pilot:new-file",
        mode="isolated",
        entry_name="new_file_pilot",
    )
    switched_isolated = orchestrator.switch_to_session(
        "pilot:new-file",
        expected_entry_names=("new_file_pilot",),
        requested_by="integration.new_file",
    )
    switched_shared = orchestrator.switch_to_session(
        "main:shared",
        expected_entry_names=("main", "new_file_pilot"),
        requested_by="integration.new_file",
    )

    assert switched_isolated.success is True
    assert switched_isolated.active_session_id == "pilot:new-file"
    assert switched_shared.success is True
    assert switched_shared.active_session_id == "main:shared"
    assert manager.snapshot().session_ids == ("main:shared", "pilot:new-file")
    assert released == []


def test_session_transition_shared_preview_pilot_shared_consistency():
    module = _load_matrix_session_manager_module()
    released = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: released.append(session_id)),
        release_session=lambda session_id: released.append(f"release:{session_id}"),
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)
    orchestrator = MatrixSessionOrchestrator(manager)

    orchestrator.open_session("main:shared", mode="shared", entry_name="main")
    assert manager.get_active_session_id() == "main:shared"

    orchestrator.open_session(
        "pilot:preview",
        mode="isolated",
        entry_name="preview",
    )
    switched_isolated = orchestrator.switch_to_session(
        "pilot:preview",
        expected_entry_names=("preview",),
        requested_by="integration.preview_pilot",
    )
    switched_shared = orchestrator.switch_to_session(
        "main:shared",
        expected_entry_names=("main", "preview"),
        requested_by="integration.preview_pilot",
    )

    assert switched_isolated.success is True
    assert switched_isolated.active_session_id == "pilot:preview"
    assert switched_shared.success is True
    assert switched_shared.active_session_id == "main:shared"
    assert manager.snapshot().session_ids == ("main:shared", "pilot:preview")
    assert released == []


def test_preview_and_debug_preview_sessions_can_coexist_and_close_independently():
    module = _load_matrix_session_manager_module()
    closed = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: closed.append(session_id)),
        release_session=lambda session_id: closed.append(f"release:{session_id}"),
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)
    orchestrator = MatrixSessionOrchestrator(manager)

    orchestrator.open_session("preview:a", mode="isolated", entry_name="preview")
    debug_session_id, _ = orchestrator.open_debug_preview(
        mode="isolated",
        session_id_prefix="debug:preview:",
        entry_name="debug_preview",
    )

    snapshot = manager.snapshot()
    assert snapshot.entry_counts == {"preview": 1, "debug_preview": 1}
    assert len(snapshot.session_ids) == 2

    assert orchestrator.close_session("preview:a") is True
    assert debug_session_id in manager.list_session_ids()
    assert orchestrator.close_session(debug_session_id) is True
    assert manager.list_session_ids() == ()
    assert "preview:a" in closed
    assert debug_session_id in closed


def test_shutdown_cleanup_on_mixed_session_set_closes_only_isolated():
    module = _load_matrix_session_manager_module()
    closed = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: closed.append(session_id)),
        release_session=lambda session_id: closed.append(f"release:{session_id}"),
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)

    manager.create_or_get("main:shared", mode="shared", entry_name="main")
    manager.create_or_get("preview:a", mode="isolated", entry_name="preview")
    manager.create_or_get("debug:preview:1", mode="isolated", entry_name="debug_preview")

    closed_ids = manager.close_by_mode("isolated")
    remaining = manager.snapshot()

    assert set(closed_ids) == {"preview:a", "debug:preview:1"}
    assert remaining.session_ids == ("main:shared",)
    assert remaining.active_isolated_session_ids == ()
    assert "main:shared" not in closed
