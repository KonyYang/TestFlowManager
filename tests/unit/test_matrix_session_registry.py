import importlib.util
import sys
import types
from pathlib import Path


def _ensure_stub_module(module_name: str, attrs: dict, originals: dict | None = None):
    if originals is not None and module_name not in originals:
        originals[module_name] = sys.modules.get(module_name, None)
    module = types.ModuleType(module_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module_name] = module


def _load_registry_module():
    module_name = "test_matrix_session_registry_module"
    if module_name in sys.modules:
        del sys.modules[module_name]

    originals = {}

    class StubMatrixService:
        _shared_instance = None

        def __init__(self):
            self.data_model = object()

        @classmethod
        def shared(cls):
            if cls._shared_instance is None:
                cls._shared_instance = cls()
            return cls._shared_instance

        @classmethod
        def create_isolated(cls):
            return cls()

    _ensure_stub_module(
        "src.features.matrix.service.matrix_service",
        {"MatrixService": StubMatrixService},
        originals,
    )

    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "matrix"
        / "service"
        / "matrix_session_registry.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    return module, StubMatrixService


def test_matrix_session_registry_defaults_to_shared():
    module, StubMatrixService = _load_registry_module()
    registry = module.MatrixSessionRegistry()

    assert registry.status().mode == "shared"
    assert registry.get_service() is StubMatrixService.shared()


def test_matrix_session_registry_isolated_mode_caches_default_isolated_instance():
    module, StubMatrixService = _load_registry_module()
    registry = module.MatrixSessionRegistry()
    shared = StubMatrixService.shared()

    registry.set_mode("isolated")
    first = registry.get_service()
    second = registry.get_service()

    assert first is second
    assert first is not shared

    registry.set_mode("shared")
    assert registry.get_service() is shared

    registry.set_mode("isolated")
    third = registry.get_service()

    assert third is not first
    assert third is not shared


def test_matrix_session_registry_supports_session_scoped_isolated_instances():
    module, StubMatrixService = _load_registry_module()
    registry = module.MatrixSessionRegistry()

    shared = StubMatrixService.shared()

    registry.set_mode("isolated", session_id="session-a")
    registry.set_mode("isolated", session_id="session-b")
    assert registry.status().mode == "shared"

    service_a_1 = registry.get_service(session_id="session-a")
    service_a_2 = registry.get_service(session_id="session-a")
    service_b = registry.get_service(session_id="session-b")
    default_service = registry.get_service()

    assert service_a_1 is service_a_2
    assert service_a_1 is not service_b
    assert service_a_1 is not shared
    assert service_b is not shared
    assert default_service is shared


def test_matrix_session_registry_release_session_clears_session_isolated_instance():
    module, StubMatrixService = _load_registry_module()
    registry = module.MatrixSessionRegistry()

    registry.set_mode("isolated", session_id="session-a")
    first = registry.get_service(session_id="session-a")
    registry.release_session("session-a")
    registry.set_mode("isolated", session_id="session-a")
    second = registry.get_service(session_id="session-a")

    assert first is not second
    assert first is not StubMatrixService.shared()
    assert second is not StubMatrixService.shared()


def test_matrix_session_registry_status_can_report_session_mode():
    module, _ = _load_registry_module()
    registry = module.MatrixSessionRegistry()

    registry.set_mode("isolated", session_id="pilot-entry")
    status = registry.status(session_id="pilot-entry")
    default_status = registry.status()

    assert status.mode == "isolated"
    assert status.session_id == "pilot-entry"
    assert default_status.mode == "shared"


def test_matrix_session_registry_open_scope_releases_session_on_close():
    module, StubMatrixService = _load_registry_module()
    registry = module.MatrixSessionRegistry()

    scope = registry.open_scope("pilot-entry", mode="isolated")
    first = registry.get_service(session_id="pilot-entry")
    scope.close()

    registry.set_mode("isolated", session_id="pilot-entry")
    second = registry.get_service(session_id="pilot-entry")

    assert first is not second
    assert first is not StubMatrixService.shared()
    assert second is not StubMatrixService.shared()


def test_matrix_session_registry_snapshot_reports_mode_map_and_active_sessions():
    module, _ = _load_registry_module()
    registry = module.MatrixSessionRegistry()

    registry.set_mode("isolated")
    registry.set_mode("isolated", session_id="session-a")
    registry.set_mode("shared", session_id="session-b")
    registry.get_service(session_id="session-a")

    snapshot = registry.snapshot()

    assert snapshot.default_mode == "isolated"
    assert snapshot.session_modes == {
        "session-a": "isolated",
        "session-b": "shared",
    }
    assert snapshot.active_isolated_session_ids == ("session-a",)
    assert snapshot.has_default_isolated_instance is False


def test_matrix_session_registry_snapshot_returns_read_only_copies():
    module, _ = _load_registry_module()
    registry = module.MatrixSessionRegistry()
    registry.set_mode("isolated", session_id="session-a")
    registry.get_service(session_id="session-a")

    snapshot = registry.snapshot()
    session_modes = registry.get_session_modes()
    active_ids = registry.get_active_isolated_session_ids()

    # Mutating returned structures must not affect registry internals.
    session_modes["session-a"] = "shared"
    snapshot.session_modes["session-a"] = "shared"

    assert registry.status(session_id="session-a").mode == "isolated"
    assert registry.get_session_modes()["session-a"] == "isolated"
    assert active_ids == ("session-a",)
