import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from src.core.project_context import ProjectContext


def _load_main_window_controller_module():
    module_name = "test_main_window_controller_module"
    if module_name in sys.modules:
        return sys.modules[module_name]

    # IMPORTANT: keep sys.modules stubbing strictly scoped to importing the target module.
    # Do not leak stubbed core modules to other test modules, otherwise collection/import order
    # will cause cross-test pollution.
    _original_modules = {}
    def _install_stub(module_path: str, stub_module: types.ModuleType) -> None:
        if module_path not in _original_modules:
            _original_modules[module_path] = sys.modules.get(module_path, None)
        sys.modules[module_path] = stub_module

    def _restore_stubs() -> None:
        for module_path, original in _original_modules.items():
            if original is None:
                sys.modules.pop(module_path, None)
            else:
                sys.modules[module_path] = original

    qtwidgets_module = types.ModuleType("PyQt5.QtWidgets")
    qtwidgets_module.QWidget = object
    qtwidgets_module.QDialog = type("QDialog", (), {"Accepted": 1})
    qtwidgets_module.QFileDialog = type(
        "QFileDialog",
        (),
        {
            "ShowDirsOnly": 1,
            "DontResolveSymlinks": 2,
            "getExistingDirectory": staticmethod(lambda *args, **kwargs: ""),
        },
    )
    qtwidgets_module.QMessageBox = type(
        "QMessageBox",
        (),
        {"critical": staticmethod(lambda *args, **kwargs: None)},
    )
    sys.modules.setdefault("PyQt5", types.ModuleType("PyQt5"))
    _install_stub("PyQt5.QtWidgets", qtwidgets_module)

    dependency_specs = {
        "src.core.logger": {"logger": SimpleNamespace(debug=lambda *a, **k: None, info=lambda *a, **k: None, error=lambda *a, **k: None)},
        "src.core.event_dispatcher": {"event_dispatcher": SimpleNamespace(subscribe=lambda *a, **k: None)},
        "src.core.project_session_coordinator": {"ProjectSessionCoordinator": object},
        "src.core.project_session_service": {"project_session_service": SimpleNamespace(apply_project_context=lambda *a, **k: None)},
        "src.features.ltr_manager.controller.ltr_editor_controller": {"LTREditorController": object},
        "src.features.main_window.model.main_window_data": {"MainWindowData": object},
        "src.features.main_window.service.project_open_service": {"ProjectOpenService": object},
        "src.features.main_window.service.main_window_service": {"MainWindowService": object},
        "src.features.ltr_manager.controller.ltr_viewer_controller": {"LTRViewerController": object},
        "src.features.main_window.view.dialogs.dl_input_dialog": {"DLInputDialog": object},
        "src.features.project_creator.controller.project_creator_controller": {"ProjectCreatorController": object},
        "src.features.matrix.service.matrix_session_factory": {
            "MatrixSessionFactory": type(
                "MatrixSessionFactory",
                (),
                {
                    "create": staticmethod(
                        lambda parent_view=None, **kwargs: SimpleNamespace(
                            matrix_project_controller=object()
                        )
                    )
                },
            )
        },
        "src.features.matrix.service.matrix_session_registry": {
            "MatrixSessionRegistry": type("MatrixSessionRegistry", (), {})
        },
    }

    for module_path, attrs in dependency_specs.items():
        stub_module = types.ModuleType(module_path)
        for attr_name, attr_value in attrs.items():
            setattr(stub_module, attr_name, attr_value)
        _install_stub(module_path, stub_module)

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
    try:
        spec.loader.exec_module(module)
    finally:
        _restore_stubs()
    return module


main_window_controller_module = _load_main_window_controller_module()
MainWindowController = main_window_controller_module.MainWindowController


def _build_controller():
    controller = object.__new__(MainWindowController)
    controller.view = object()
    controller.service = SimpleNamespace(update_status=Mock())
    controller.project_open_service = SimpleNamespace(
        resolve_default_project_path=Mock(return_value=r"D:\Projects"),
        prepare_project=Mock(),
    )
    controller.project_session_coordinator = Mock()
    controller._project_context = None
    controller._show_basic_info_dialog = Mock()
    return controller


def test_handle_open_project_returns_false_when_user_cancels(monkeypatch):
    controller = _build_controller()
    apply_project_context = Mock()
    monkeypatch.setattr(
        main_window_controller_module,
        "project_session_service",
        SimpleNamespace(apply_project_context=apply_project_context),
    )
    monkeypatch.setattr(
        main_window_controller_module.QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *args, **kwargs: ""),
    )

    assert controller.handle_open_project() is False
    controller.project_open_service.prepare_project.assert_not_called()
    apply_project_context.assert_not_called()


def test_handle_open_project_applies_existing_project_context(monkeypatch):
    controller = _build_controller()
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-401A",
        "DL-2025-04-401A",
    )
    project_result = SimpleNamespace(
        created_application_data=False,
        project_data={"DL": "DL-2025-04-401A"},
        json_file_path=r"D:\Projects\DL-2025-04-401A\application_data.json",
        project_context=project_context,
    )
    controller.project_open_service.prepare_project.return_value = project_result

    apply_project_context = Mock()
    monkeypatch.setattr(
        main_window_controller_module,
        "project_session_service",
        SimpleNamespace(apply_project_context=apply_project_context),
    )
    monkeypatch.setattr(
        main_window_controller_module.QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *args, **kwargs: r"D:\Projects\DL-2025-04-401A"),
    )

    assert controller.handle_open_project() is True
    controller.project_open_service.prepare_project.assert_called_once_with(r"D:\Projects\DL-2025-04-401A")
    controller._show_basic_info_dialog.assert_not_called()
    apply_project_context.assert_called_once_with(project_context)


def test_handle_open_project_reloads_after_basic_info_dialog(monkeypatch):
    controller = _build_controller()
    initial_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-402A",
        "DL-2025-04-402A",
    )
    final_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-402A",
        "DL-2025-04-402A",
    )
    initial_result = SimpleNamespace(
        created_application_data=True,
        project_data={"DL": "DL-2025-04-402A"},
        json_file_path=r"D:\Projects\DL-2025-04-402A\application_data.json",
        project_context=initial_context,
    )
    final_result = SimpleNamespace(
        created_application_data=False,
        project_data={"DL": "DL-2025-04-402A"},
        json_file_path=r"D:\Projects\DL-2025-04-402A\application_data.json",
        project_context=final_context,
    )
    controller.project_open_service.prepare_project.side_effect = [initial_result, final_result]

    apply_project_context = Mock()
    monkeypatch.setattr(
        main_window_controller_module,
        "project_session_service",
        SimpleNamespace(apply_project_context=apply_project_context),
    )
    monkeypatch.setattr(
        main_window_controller_module.QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *args, **kwargs: r"D:\Projects\DL-2025-04-402A"),
    )

    assert controller.handle_open_project() is True
    assert controller.project_open_service.prepare_project.call_count == 2
    controller._show_basic_info_dialog.assert_called_once_with(
        initial_result.project_data,
        initial_result.json_file_path,
    )
    apply_project_context.assert_called_once_with(final_context)


def test_handle_open_project_updates_status_and_shows_error_when_prepare_fails(monkeypatch):
    controller = _build_controller()
    controller.project_open_service.prepare_project.side_effect = RuntimeError("boom")

    critical_messages = []
    monkeypatch.setattr(
        main_window_controller_module,
        "project_session_service",
        SimpleNamespace(apply_project_context=Mock()),
    )
    monkeypatch.setattr(
        main_window_controller_module.QFileDialog,
        "getExistingDirectory",
        staticmethod(lambda *args, **kwargs: r"D:\Projects\DL-2025-04-403A"),
    )
    monkeypatch.setattr(
        main_window_controller_module.QMessageBox,
        "critical",
        staticmethod(lambda *args: critical_messages.append(args)),
    )

    assert controller.handle_open_project() is False
    controller.service.update_status.assert_called_once_with("打开项目失败")
    assert len(critical_messages) == 1


def test_on_project_opened_ignores_event_without_project_path():
    controller = _build_controller()
    controller._apply_project_context = Mock()

    controller._on_project_opened({})

    controller._apply_project_context.assert_not_called()


def test_on_project_opened_short_circuits_when_same_project_already_applied():
    controller = _build_controller()
    controller._project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-404A",
        "DL-2025-04-404A",
    )
    controller._apply_project_context = Mock()

    controller._on_project_opened(
        {
            "project_path": r"D:\Projects\DL-2025-04-404A",
            "dl_number": "DL-2025-04-404A",
        }
    )

    controller._apply_project_context.assert_not_called()


def test_on_project_opened_applies_project_context_from_event_payload():
    controller = _build_controller()
    controller._apply_project_context = Mock()
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-405A",
        "DL-2025-04-405A",
    )

    controller._on_project_opened(
        {
            "project_context": project_context,
            "project_path": project_context.project_path,
            "dl_number": project_context.dl_number,
        }
    )

    controller._apply_project_context.assert_called_once_with(
        project_context,
        trigger_matrix_auto_import=True,
        status_message="当前项目: DL-2025-04-405A",
        log_message=(
            "Project opened successfully: "
            rf"{project_context.project_path} with DL number: {project_context.dl_number}"
        ),
    )


def test_on_project_opened_uses_event_context_builder_and_not_local_fallback():
    controller = _build_controller()
    controller._apply_project_context = Mock()
    controller._build_project_context = Mock()

    controller._on_project_opened(
        {
            "project_path": r"D:\Projects\DL-2025-04-406A",
            "dl_number": "DL-2025-04-406A",
        }
    )

    controller._build_project_context.assert_not_called()
    controller._apply_project_context.assert_called_once()
