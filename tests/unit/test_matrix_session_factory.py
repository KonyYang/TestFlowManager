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


def _load_matrix_session_factory_module():
    module_name = "test_matrix_session_factory_module"
    if module_name in sys.modules:
        module = sys.modules[module_name]
        return module, module._shared_service, module._stub_matrix_service

    originals = {}
    shared_service = None

    class StubMatrixService:
        def __init__(self):
            self.data_model = object()

        @classmethod
        def shared(cls):
            return shared_service

        @classmethod
        def create_isolated(cls):
            return cls()

    class StubMatrixController:
        def __init__(self, parent=None, matrix_service=None, application_service=None):
            self.parent = parent
            self.service = matrix_service
            self.application_service = application_service

    class StubMatrixProjectController:
        def __init__(self, parent_view=None, matrix_controller=None):
            self.parent_view = parent_view
            self.matrix_controller = matrix_controller

    class StubMatrixApplicationService:
        def __init__(self, matrix_service):
            self.matrix_service = matrix_service

    class StubMatrixSessionRegistry:
        def __init__(self, initial_mode="shared"):
            self.mode = initial_mode
            if initial_mode == "isolated":
                self.service = StubMatrixService.create_isolated()
            else:
                self.service = StubMatrixService.shared()

        def set_mode(self, mode, **kwargs):
            self.mode = mode

        def get_service(self, **kwargs):
            return self.service

    shared_service = StubMatrixService()

    _ensure_stub_module(
        "src.features.matrix.service.matrix_service",
        {"MatrixService": StubMatrixService},
        originals,
    )
    _ensure_stub_module(
        "src.features.matrix.controller.matrix_controller",
        {"MatrixController": StubMatrixController},
        originals,
    )
    _ensure_stub_module(
        "src.features.matrix.controller.matrix_project_controller",
        {"MatrixProjectController": StubMatrixProjectController},
        originals,
    )
    _ensure_stub_module(
        "src.features.matrix.service.matrix_application_service",
        {"MatrixApplicationService": StubMatrixApplicationService},
        originals,
    )
    _ensure_stub_module(
        "src.features.matrix.service.matrix_session_registry",
        {"MatrixSessionRegistry": StubMatrixSessionRegistry},
        originals,
    )

    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "matrix"
        / "service"
        / "matrix_session_factory.py"
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
    module._shared_service = shared_service
    module._stub_matrix_service = StubMatrixService
    return module, shared_service, StubMatrixService


def test_matrix_session_factory_uses_shared_mode_by_default():
    module, shared_service, _ = _load_matrix_session_factory_module()

    session = module.MatrixSessionFactory.create(parent_view="view")

    assert session.matrix_controller.service is shared_service
    assert session.matrix_project_controller.matrix_controller is session.matrix_controller


def test_matrix_session_factory_can_build_isolated_service():
    module, shared_service, StubMatrixService = _load_matrix_session_factory_module()

    session = module.MatrixSessionFactory.create(parent_view="view", mode="isolated")

    assert isinstance(session.matrix_controller.service, StubMatrixService)
    assert session.matrix_controller.service is not shared_service


def test_matrix_session_factory_rejects_unknown_mode():
    module, _, _ = _load_matrix_session_factory_module()

    try:
        module.MatrixSessionFactory.create(mode="unknown")
    except ValueError as exc:
        assert "Unsupported Matrix session mode" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported mode")


def test_matrix_session_factory_can_use_injected_registry():
    module, _, StubMatrixService = _load_matrix_session_factory_module()
    isolated_service = StubMatrixService()
    registry = types.SimpleNamespace(
        mode_set=None,
        set_mode=lambda mode, **kwargs: setattr(registry, "mode_set", (mode, kwargs.get("session_id"))),
        get_service=lambda **kwargs: isolated_service,
    )

    session = module.MatrixSessionFactory.create(
        parent_view="view",
        mode="isolated",
        registry=registry,
    )

    assert registry.mode_set == ("isolated", None)
    assert session.matrix_controller.service is isolated_service


def test_matrix_session_factory_reuses_service_when_same_registry_is_passed():
    module, _, _ = _load_matrix_session_factory_module()
    shared_service = object()
    registry = types.SimpleNamespace(
        set_mode=lambda mode, **kwargs: None,
        get_service=lambda **kwargs: shared_service,
    )

    first = module.MatrixSessionFactory.create(parent_view="view-a", registry=registry)
    second = module.MatrixSessionFactory.create(parent_view="view-b", registry=registry)

    assert first.matrix_controller.service is shared_service
    assert second.matrix_controller.service is shared_service


def test_matrix_session_factory_isolated_entry_does_not_mutate_shared_registry_entry():
    module, _, StubMatrixService = _load_matrix_session_factory_module()
    shared_service = StubMatrixService()
    registry = types.SimpleNamespace(
        set_mode=lambda mode, **kwargs: None,
        get_service=lambda **kwargs: shared_service,
    )

    shared_session_before = module.MatrixSessionFactory.create(
        parent_view="shared-before",
        mode="shared",
        registry=registry,
    )
    isolated_session = module.MatrixSessionFactory.create(
        parent_view="isolated-entry",
        mode="isolated",
    )
    shared_session_after = module.MatrixSessionFactory.create(
        parent_view="shared-after",
        mode="shared",
        registry=registry,
    )

    assert shared_session_before.matrix_controller.service is shared_service
    assert isolated_session.matrix_controller.service is not shared_service
    assert shared_session_after.matrix_controller.service is shared_service


def test_matrix_session_factory_cross_entry_shared_is_stable_around_isolated_pilot():
    module, _, StubMatrixService = _load_matrix_session_factory_module()

    shared_service = StubMatrixService()
    shared_registry = types.SimpleNamespace(
        set_mode=lambda mode, **kwargs: None,
        get_service=lambda **kwargs: shared_service,
    )

    shared_entry_first = module.MatrixSessionFactory.create(
        parent_view="main-window-entry",
        mode="shared",
        registry=shared_registry,
    )
    isolated_pilot_entry = module.MatrixSessionFactory.create(
        parent_view="new-file-pilot-entry",
        mode="isolated",
    )
    shared_entry_second = module.MatrixSessionFactory.create(
        parent_view="open-project-entry",
        mode="shared",
        registry=shared_registry,
    )

    assert shared_entry_first.matrix_controller.service is shared_service
    assert isolated_pilot_entry.matrix_controller.service is not shared_service
    assert shared_entry_second.matrix_controller.service is shared_service


def test_matrix_session_factory_passes_session_id_to_registry():
    module, _, StubMatrixService = _load_matrix_session_factory_module()
    session_service = StubMatrixService()
    calls = []
    registry = types.SimpleNamespace(
        set_mode=lambda mode, **kwargs: calls.append(("set_mode", mode, kwargs.get("session_id"))),
        get_service=lambda **kwargs: (calls.append(("get_service", kwargs.get("session_id"))) or session_service),
    )

    session = module.MatrixSessionFactory.create(
        parent_view="view",
        mode="isolated",
        session_id="pilot:new-file",
        registry=registry,
    )

    assert session.matrix_controller.service is session_service
    assert calls == [
        ("set_mode", "isolated", "pilot:new-file"),
        ("get_service", "pilot:new-file"),
    ]
