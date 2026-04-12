import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path


def _ensure_stub_module(module_name: str, attrs: dict, originals: dict | None = None):
    if originals is not None and module_name not in originals:
        originals[module_name] = sys.modules.get(module_name, None)
    module = types.ModuleType(module_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module_name] = module


def _load_matrix_session_manager_module():
    module_name = "test_matrix_session_manager_module"
    if module_name in sys.modules:
        del sys.modules[module_name]

    originals = {}

    @dataclass(frozen=True)
    class StubMatrixSessionComponents:
        matrix_controller: object
        matrix_project_controller: object

    class StubMatrixSessionFactory:
        calls = []

        @staticmethod
        def create(parent_view=None, mode="shared", **kwargs):
            StubMatrixSessionFactory.calls.append(
                (parent_view, mode, kwargs.get("session_id"))
            )
            return StubMatrixSessionComponents(
                matrix_controller=object(),
                matrix_project_controller=object(),
            )

    _ensure_stub_module(
        "src.features.matrix.service.matrix_session_factory",
        {
            "MatrixSessionFactory": StubMatrixSessionFactory,
            "MatrixSessionComponents": StubMatrixSessionComponents,
        },
        originals,
    )
    _ensure_stub_module(
        "src.features.matrix.service.matrix_session_registry",
        {"MatrixSessionRegistry": type("MatrixSessionRegistry", (), {})},
        originals,
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
    try:
        spec.loader.exec_module(module)
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    return module, StubMatrixSessionFactory


def test_matrix_session_manager_create_or_get_reuses_existing_session():
    module, StubFactory = _load_matrix_session_manager_module()
    StubFactory.calls = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: None),
        release_session=lambda session_id: None,
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)

    first = manager.create_or_get("preview:a", mode="isolated")
    second = manager.create_or_get("preview:a", mode="isolated")

    assert first is second
    assert StubFactory.calls == [("view", "isolated", "preview:a")]


def test_matrix_session_manager_close_prefers_scope_close():
    module, _ = _load_matrix_session_manager_module()
    closed = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(
            close=lambda: closed.append(session_id)
        ),
        release_session=lambda session_id: closed.append(f"release:{session_id}"),
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)

    manager.create_or_get("preview:a", mode="isolated")
    result = manager.close("preview:a")

    assert result is True
    assert closed == ["preview:a"]


def test_matrix_session_manager_close_falls_back_to_registry_release():
    module, _ = _load_matrix_session_manager_module()
    released = []
    registry = types.SimpleNamespace(
        release_session=lambda session_id: released.append(session_id),
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)

    manager.create_or_get("preview:a", mode="isolated")
    result = manager.close("preview:a")

    assert result is True
    assert released == ["preview:a"]


def test_matrix_session_manager_list_session_ids_tracks_active_sessions():
    module, _ = _load_matrix_session_manager_module()
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: None),
        release_session=lambda session_id: None,
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)

    manager.create_or_get("preview:a", mode="isolated")
    manager.create_or_get("preview:b", mode="isolated")
    assert manager.list_session_ids() == ("preview:a", "preview:b")

    manager.close("preview:a")
    assert manager.list_session_ids() == ("preview:b",)


def test_matrix_session_manager_snapshot_reports_modes_and_active_isolated():
    module, _ = _load_matrix_session_manager_module()
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: None),
        release_session=lambda session_id: None,
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)

    manager.create_or_get("preview:a", mode="isolated", entry_name="preview")
    manager.create_or_get("shared:x", mode="shared", entry_name="shared_entry")

    snapshot = manager.snapshot()
    assert snapshot.session_ids == ("preview:a", "shared:x")
    assert snapshot.session_modes == {"preview:a": "isolated", "shared:x": "shared"}
    assert snapshot.session_entries == {
        "preview:a": "preview",
        "shared:x": "shared_entry",
    }
    assert snapshot.entry_counts == {"preview": 1, "shared_entry": 1}
    assert snapshot.active_isolated_session_ids == ("preview:a",)
    assert snapshot.active_session_id == "preview:a"
    assert snapshot.page_session_bindings == {}
    assert snapshot.total_sessions == 2


def test_matrix_session_manager_stats_returns_copied_structures():
    module, _ = _load_matrix_session_manager_module()
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: None),
        release_session=lambda session_id: None,
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)
    manager.create_or_get("preview:a", mode="isolated", entry_name="preview")

    stats = manager.stats()
    stats["session_modes"]["preview:a"] = "shared"
    stats["session_entries"]["preview:a"] = "mutated"
    stats["entry_counts"]["preview"] = 99
    stats["page_session_bindings"]["matrix.main"] = "other"

    stats2 = manager.stats()
    assert stats2["session_modes"] == {"preview:a": "isolated"}
    assert stats2["session_entries"] == {"preview:a": "preview"}
    assert stats2["entry_counts"] == {"preview": 1}
    assert stats2["active_isolated_session_ids"] == ("preview:a",)
    assert stats2["active_session_id"] == "preview:a"
    assert stats2["page_session_bindings"] == {}


def test_matrix_session_manager_close_by_mode_closes_only_target_mode():
    module, _ = _load_matrix_session_manager_module()
    closed = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(
            close=lambda: closed.append(session_id)
        ),
        release_session=lambda session_id: None,
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)
    manager.create_or_get("preview:a", mode="isolated")
    manager.create_or_get("shared:x", mode="shared")

    closed_ids = manager.close_by_mode("isolated")

    assert closed_ids == ("preview:a",)
    assert closed == ["preview:a"]
    assert manager.list_session_ids() == ("shared:x",)


def test_matrix_session_manager_close_all_closes_all_sessions():
    module, _ = _load_matrix_session_manager_module()
    closed = []
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(
            close=lambda: closed.append(session_id)
        ),
        release_session=lambda session_id: None,
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)
    manager.create_or_get("preview:a", mode="isolated")
    manager.create_or_get("preview:b", mode="isolated")

    closed_ids = manager.close_all()

    assert closed_ids == ("preview:a", "preview:b")
    assert closed == ["preview:a", "preview:b"]
    assert manager.list_session_ids() == ()


def test_matrix_session_manager_activate_switches_active_session():
    module, _ = _load_matrix_session_manager_module()
    registry = types.SimpleNamespace(
        open_scope=lambda session_id, mode: types.SimpleNamespace(close=lambda: None),
        release_session=lambda session_id: None,
    )
    manager = module.MatrixSessionManager(parent_view="view", registry=registry)
    manager.create_or_get("preview:a", mode="isolated")
    manager.create_or_get("preview:b", mode="isolated")

    assert manager.get_active_session_id() == "preview:a"
    assert manager.activate("preview:b") is True
    assert manager.get_active_session_id() == "preview:b"


def test_matrix_session_manager_activate_returns_false_for_unknown_session():
    module, _ = _load_matrix_session_manager_module()
    manager = module.MatrixSessionManager(parent_view="view", registry=None)

    assert manager.activate("missing") is False
    assert manager.get_active_session_id() is None


def test_matrix_session_manager_page_session_binding_lifecycle():
    module, _ = _load_matrix_session_manager_module()
    manager = module.MatrixSessionManager(parent_view="view", registry=None)
    manager.create_or_get("preview:a", mode="isolated")

    assert manager.bind_page_session("matrix.main", "preview:a") is True
    assert manager.get_page_session_id("matrix.main") == "preview:a"
    assert manager.get_page_session_bindings() == {"matrix.main": "preview:a"}
    assert manager.unbind_page_session("matrix.main") is True
    assert manager.get_page_session_id("matrix.main") is None


def test_matrix_session_manager_close_unbinds_page_session_mapping():
    module, _ = _load_matrix_session_manager_module()
    manager = module.MatrixSessionManager(parent_view="view", registry=None)
    manager.create_or_get("preview:a", mode="isolated")
    manager.bind_page_session("matrix.main", "preview:a")

    assert manager.close("preview:a") is True
    assert manager.get_page_session_bindings() == {}


def test_matrix_session_manager_can_clear_all_page_session_bindings():
    module, _ = _load_matrix_session_manager_module()
    manager = module.MatrixSessionManager(parent_view="view", registry=None)
    manager.create_or_get("preview:a", mode="isolated")
    manager.create_or_get("preview:b", mode="isolated")
    manager.bind_page_session("matrix.main", "preview:a")
    manager.bind_page_session("matrix.preview", "preview:b")

    cleared = manager.clear_page_session_bindings()

    assert cleared == ("matrix.main", "matrix.preview")
    assert manager.get_page_session_bindings() == {}


def test_matrix_session_manager_can_register_existing_components_without_factory_call():
    module, StubFactory = _load_matrix_session_manager_module()
    StubFactory.calls = []
    manager = module.MatrixSessionManager(parent_view="view", registry=None)
    components = types.SimpleNamespace(matrix_controller=object(), matrix_project_controller=object())

    assert manager.register_existing(
        "main:shared",
        mode="shared",
        entry_name="main",
        components=components,
    ) is True
    assert manager.get("main:shared") is components
    assert manager.get_active_session_id() == "main:shared"
    assert StubFactory.calls == []
