import os
import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from src.features.matrix.service.matrix_session_orchestrator import MatrixSessionOrchestrator


def _ensure_stub_module(module_name: str, attrs: dict):
    module = types.ModuleType(module_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module_name] = module


def _build_qmessage_box_stub():
    return type(
        "QMessageBox",
        (),
        {
            "critical": staticmethod(lambda *args, **kwargs: None),
            "warning": staticmethod(lambda *args, **kwargs: None),
            "about": staticmethod(lambda *args, **kwargs: None),
        },
    )


def _load_main_window_controller_module():
    module_name = "test_integration_main_window_controller_module"
    if module_name in sys.modules:
        del sys.modules[module_name]

    qtwidgets_module = types.ModuleType("PyQt5.QtWidgets")
    qtwidgets_module.QWidget = object
    qtwidgets_module.QDialog = type("QDialog", (), {"Accepted": 1})
    qtwidgets_module.QFileDialog = type("QFileDialog", (), {})
    qtwidgets_module.QMessageBox = _build_qmessage_box_stub()
    sys.modules.setdefault("PyQt5", types.ModuleType("PyQt5"))
    sys.modules["PyQt5.QtWidgets"] = qtwidgets_module

    dependency_specs = {
        "src.core.logger": {
            "logger": SimpleNamespace(
                debug=lambda *a, **k: None,
                info=lambda *a, **k: None,
                error=lambda *a, **k: None,
                warning=lambda *a, **k: None,
            )
        },
        "src.core.event_dispatcher": {
            "event_dispatcher": SimpleNamespace(subscribe=lambda *a, **k: None)
        },
        "src.core.project_session_coordinator": {"ProjectSessionCoordinator": object},
        "src.core.project_session_service": {
            "project_session_service": SimpleNamespace(apply_project_context=lambda *a, **k: None)
        },
        "src.features.ltr_manager.controller.ltr_editor_controller": {"LTREditorController": object},
        "src.features.main_window.model.main_window_data": {"MainWindowData": object},
        "src.features.main_window.service.project_open_service": {"ProjectOpenService": object},
        "src.features.main_window.service.main_window_service": {"MainWindowService": object},
        "src.features.ltr_manager.controller.ltr_viewer_controller": {"LTRViewerController": object},
        "src.features.main_window.view.dialogs.dl_input_dialog": {"DLInputDialog": object},
        "src.features.project_creator.controller.project_creator_controller": {"ProjectCreatorController": object},
    }
    for module_path, attrs in dependency_specs.items():
        _ensure_stub_module(module_path, attrs)

    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "controller"
        / "main_window_controller.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_matrix_session_manager_module():
    module_name = "test_integration_matrix_session_manager_module_v2"
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


def test_workspace_consistency_switches_active_to_bound_session():
    manager_module = _load_matrix_session_manager_module()
    main_window_module = _load_main_window_controller_module()
    MainWindowController = main_window_module.MainWindowController

    manager = manager_module.MatrixSessionManager(parent_view="view", registry=None)
    manager.create_or_get("main:shared", mode="shared", entry_name="main")
    manager.create_or_get("preview:a", mode="isolated", entry_name="preview")
    manager.activate("main:shared")
    manager.bind_page_session("matrix.main", "preview:a")

    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = manager
    controller._matrix_session_orchestrator = MatrixSessionOrchestrator(manager)

    result = controller.ensure_matrix_workspace_session_consistency()

    assert result["success"] is True
    assert result["bound_session_id"] == "preview:a"
    assert result["active_session_id"] == "preview:a"
    assert result["rollback_performed"] is False
    assert manager.get_active_session_id() == "preview:a"


def test_workspace_consistency_rolls_back_when_bound_entry_is_not_allowed():
    manager_module = _load_matrix_session_manager_module()
    main_window_module = _load_main_window_controller_module()
    MainWindowController = main_window_module.MainWindowController

    manager = manager_module.MatrixSessionManager(parent_view="view", registry=None)
    manager.create_or_get("main:shared", mode="shared", entry_name="main")
    manager.create_or_get("custom:session", mode="isolated", entry_name="custom_entry")
    manager.activate("main:shared")
    manager.bind_page_session("matrix.main", "custom:session")

    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = manager
    controller._matrix_session_orchestrator = MatrixSessionOrchestrator(manager)

    result = controller.ensure_matrix_workspace_session_consistency()

    assert result["success"] is False
    assert result["reason"] == "entry_not_allowed"
    assert result["rollback_performed"] is True
    assert result["active_session_id"] == "main:shared"
    assert manager.get_active_session_id() == "main:shared"


def test_shutdown_clears_page_bindings_and_closes_only_isolated_sessions():
    manager_module = _load_matrix_session_manager_module()
    main_window_module = _load_main_window_controller_module()
    MainWindowController = main_window_module.MainWindowController

    manager = manager_module.MatrixSessionManager(parent_view="view", registry=None)
    manager.create_or_get("main:shared", mode="shared", entry_name="main")
    manager.create_or_get("preview:a", mode="isolated", entry_name="preview")
    manager.bind_page_session("matrix.main", "preview:a")
    manager.bind_page_session("matrix.secondary", "main:shared")

    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = manager
    controller.view = SimpleNamespace(
        matrix_controller=SimpleNamespace(auto_export_matrix_data_on_shutdown=lambda: None)
    )
    controller.service = SimpleNamespace(save_application_state=lambda: None)

    controller.shutdown()

    assert manager.get_page_session_bindings() == {}
    assert manager.list_session_ids() == ("main:shared",)


def test_preview_pilot_close_clears_binding_and_restores_active_shared(monkeypatch):
    manager_module = _load_matrix_session_manager_module()
    main_window_module = _load_main_window_controller_module()
    MainWindowController = main_window_module.MainWindowController

    monkeypatch.setenv("TFM_MATRIX_SESSION_ISOLATED_PREVIEW_PILOT", "1")

    manager = manager_module.MatrixSessionManager(parent_view="view", registry=None)
    manager.create_or_get("main:shared", mode="shared", entry_name="main")
    manager.create_or_get("pilot:preview", mode="isolated", entry_name="preview")
    manager.activate("pilot:preview")
    manager.bind_page_session("matrix.main", "pilot:preview")

    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = manager
    controller._matrix_session_orchestrator = MatrixSessionOrchestrator(manager)

    assert controller.handle_close_isolated_matrix_preview_pilot() is True

    assert manager.get_active_session_id() == "main:shared"
    assert manager.get_page_session_id("matrix.main") == "main:shared"
    assert "pilot:preview" not in manager.list_session_ids()
