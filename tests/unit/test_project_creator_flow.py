import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from src.core.project_context import ProjectContext


def _load_module(module_name: str, relative_path: str, stub_modules=None):
    if module_name in sys.modules:
        return sys.modules[module_name]

    # IMPORTANT: keep sys.modules stubbing strictly scoped to importing the target module.
    _original_modules = {}

    def _install_stub(stub_name: str, stub_module: types.ModuleType) -> None:
        if stub_name not in _original_modules:
            _original_modules[stub_name] = sys.modules.get(stub_name, None)
        sys.modules[stub_name] = stub_module

    def _restore_stubs() -> None:
        for stub_name, original in _original_modules.items():
            if original is None:
                sys.modules.pop(stub_name, None)
            else:
                sys.modules[stub_name] = original

    if stub_modules:
        for stub_name, attrs in stub_modules.items():
            stub_module = types.ModuleType(stub_name)
            for attr_name, attr_value in attrs.items():
                setattr(stub_module, attr_name, attr_value)
            _install_stub(stub_name, stub_module)

    module_path = Path(__file__).resolve().parents[2] / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        _restore_stubs()
    return module


def _build_qmessage_box_stub():
    return type(
        "QMessageBox",
        (),
        {
            "critical": staticmethod(lambda *args, **kwargs: None),
            "warning": staticmethod(lambda *args, **kwargs: None),
        },
    )


project_creator_controller_module = _load_module(
    "test_project_creator_controller_module",
    "src/features/project_creator/controller/project_creator_controller.py",
    stub_modules={
        "PyQt5.QtWidgets": {
            "QDialog": type("QDialog", (), {"Accepted": 1}),
            "QMessageBox": _build_qmessage_box_stub(),
        },
        "src.features.project_creator.service.project_creator_service": {
            "ProjectCreatorService": object
        },
        "src.features.project_creator.service.project_creation_application_service": {
            "ProjectCreationApplicationService": object
        },
        "src.features.project_creator.model.project_creator_data": {
            "EmailData": object,
            "EmailAttachment": object,
            "ProjectCreationContext": object,
        },
        "src.features.email_extractor.view.email_selector_dialog": {
            "EmailSelectorDialog": object
        },
        "src.features.email_extractor.controller.email_extractor_controller": {
            "EmailExtractorController": object
        },
        "src.features.project_creator.service.ltr_project_integration_service": {
            "LTRProjectIntegrationService": object
        },
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
        # Use real event_dispatcher / ProjectSessionCoordinator to avoid polluting global sys.modules
        # for other tests (session flow / coordinator tests).
    },
)

ProjectCreatorController = project_creator_controller_module.ProjectCreatorController
ProjectCreatorController.__test__ = False


def _load_main_window_controller_for_new_file_test():
    module_name = "test_main_window_controller_new_file_module"
    if module_name in sys.modules:
        return sys.modules[module_name]

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
    qtwidgets_module.QFileDialog = type("QFileDialog", (), {})
    qtwidgets_module.QMessageBox = _build_qmessage_box_stub()
    sys.modules.setdefault("PyQt5", types.ModuleType("PyQt5"))
    _install_stub("PyQt5.QtWidgets", qtwidgets_module)

    dependency_specs = {
        "src.core.logger": {
            "logger": SimpleNamespace(
                debug=lambda *a, **k: None,
                info=lambda *a, **k: None,
                warning=lambda *a, **k: None,
                error=lambda *a, **k: None,
            )
        },
        # Use real event_dispatcher / ProjectSessionCoordinator (PyQt5.QtCore is stubbed above).
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


main_window_controller_module = _load_main_window_controller_for_new_file_test()
MainWindowController = main_window_controller_module.MainWindowController
MainWindowController.__test__ = False


def test_project_creator_handle_create_new_project_continues_when_email_selected():
    controller = object.__new__(ProjectCreatorController)
    controller.parent_view = object()
    controller._show_email_selector_dialog = Mock(return_value=True)
    controller._continue_project_creation = Mock()

    assert controller.handle_create_new_project() is True
    controller._show_email_selector_dialog.assert_called_once_with()
    controller._continue_project_creation.assert_called_once_with()


def test_project_creator_handle_create_new_project_stops_when_email_selection_cancelled():
    controller = object.__new__(ProjectCreatorController)
    controller.parent_view = object()
    controller._show_email_selector_dialog = Mock(return_value=False)
    controller._continue_project_creation = Mock()

    assert controller.handle_create_new_project() is False
    controller._show_email_selector_dialog.assert_called_once_with()
    controller._continue_project_creation.assert_not_called()


def test_project_creator_handle_create_new_project_shows_error_when_exception_raised(monkeypatch):
    controller = object.__new__(ProjectCreatorController)
    controller.parent_view = object()
    controller._show_email_selector_dialog = Mock(side_effect=RuntimeError("boom"))
    controller._continue_project_creation = Mock()

    critical_messages = []
    monkeypatch.setattr(
        project_creator_controller_module.QMessageBox,
        "critical",
        staticmethod(lambda *args: critical_messages.append(args)),
    )

    assert controller.handle_create_new_project() is False
    controller._continue_project_creation.assert_not_called()
    assert len(critical_messages) == 1


def test_main_window_handle_new_file_calls_creator_and_cleanup(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.view = object()
    controller.matrix_session_registry = object()
    controller.service = SimpleNamespace(update_status=Mock())

    creator_instance = Mock()
    creator_instance.handle_create_new_project.return_value = True
    creator_class = Mock(return_value=creator_instance)
    monkeypatch.setattr(
        main_window_controller_module,
        "ProjectCreatorController",
        creator_class,
    )

    assert controller.handle_new_file() is True
    creator_class.assert_called_once_with(
        controller.view,
        matrix_session_registry=controller.matrix_session_registry,
        matrix_session_mode="shared",
        matrix_session_id=None,
    )
    creator_instance.handle_create_new_project.assert_called_once_with()
    creator_instance.cleanup.assert_called_once_with()


def test_main_window_handle_new_file_updates_status_when_creator_raises(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.view = object()
    controller.matrix_session_registry = object()
    controller.service = SimpleNamespace(update_status=Mock())

    creator_instance = Mock()
    creator_instance.handle_create_new_project.side_effect = RuntimeError("boom")
    creator_class = Mock(return_value=creator_instance)
    monkeypatch.setattr(
        main_window_controller_module,
        "ProjectCreatorController",
        creator_class,
    )

    assert controller.handle_new_file() is False
    controller.service.update_status.assert_called_once_with("新建项目失败")
    creator_instance.cleanup.assert_not_called()


def test_main_window_handle_new_file_uses_isolated_mode_when_pilot_enabled(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.view = object()
    controller.matrix_session_registry = object()
    controller.service = SimpleNamespace(update_status=Mock())

    creator_instance = Mock()
    creator_instance.handle_create_new_project.return_value = True
    creator_class = Mock(return_value=creator_instance)
    monkeypatch.setattr(
        main_window_controller_module,
        "ProjectCreatorController",
        creator_class,
    )
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_isolated_matrix_session_pilot_enabled",
        staticmethod(lambda: True),
    )

    assert controller.handle_new_file() is True
    creator_class.assert_called_once_with(
        controller.view,
        matrix_session_registry=controller.matrix_session_registry,
        matrix_session_mode="isolated",
        matrix_session_id="pilot:new-file",
    )
    creator_instance.cleanup.assert_called_once_with()


def test_main_window_handle_new_file_uses_injected_pilot_policy(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.view = object()
    controller.matrix_session_registry = object()
    controller.service = SimpleNamespace(update_status=Mock())
    controller._matrix_session_entry_policies = SimpleNamespace(
        get=lambda name: SimpleNamespace(mode="isolated", fixed_session_id="custom:new-file")
    )

    creator_instance = Mock()
    creator_instance.handle_create_new_project.return_value = True
    creator_class = Mock(return_value=creator_instance)
    monkeypatch.setattr(
        main_window_controller_module,
        "ProjectCreatorController",
        creator_class,
    )
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_isolated_matrix_session_pilot_enabled",
        staticmethod(lambda: True),
    )

    assert controller.handle_new_file() is True
    creator_class.assert_called_once_with(
        controller.view,
        matrix_session_registry=controller.matrix_session_registry,
        matrix_session_mode="isolated",
        matrix_session_id="custom:new-file",
    )
    creator_instance.cleanup.assert_called_once_with()


def test_main_window_handle_new_file_uses_injected_entry_facade(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.view = object()
    controller.matrix_session_registry = object()
    controller.service = SimpleNamespace(update_status=Mock())
    controller._matrix_session_entry_facade = SimpleNamespace(
        resolve_new_file_session_config=lambda pilot_enabled: SimpleNamespace(
            mode="isolated",
            session_id="facade:new-file",
        )
    )

    creator_instance = Mock()
    creator_instance.handle_create_new_project.return_value = True
    creator_class = Mock(return_value=creator_instance)
    monkeypatch.setattr(
        main_window_controller_module,
        "ProjectCreatorController",
        creator_class,
    )
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_isolated_matrix_session_pilot_enabled",
        staticmethod(lambda: False),
    )

    assert controller.handle_new_file() is True
    creator_class.assert_called_once_with(
        controller.view,
        matrix_session_registry=controller.matrix_session_registry,
        matrix_session_mode="isolated",
        matrix_session_id="facade:new-file",
    )
    creator_instance.cleanup.assert_called_once_with()


def test_main_window_isolated_pilot_switch_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("TFM_MATRIX_SESSION_ISOLATED_PILOT", raising=False)
    assert main_window_controller_module.MainWindowController._is_isolated_matrix_session_pilot_enabled() is False


def test_main_window_isolated_pilot_switch_accepts_truthy_values(monkeypatch):
    monkeypatch.setenv("TFM_MATRIX_SESSION_ISOLATED_PILOT", "true")
    assert main_window_controller_module.MainWindowController._is_isolated_matrix_session_pilot_enabled() is True


def test_main_window_debug_switch_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("TFM_ENABLE_DEBUG_COMMANDS", raising=False)
    assert main_window_controller_module.MainWindowController._is_debug_matrix_command_enabled() is False


def test_main_window_debug_switch_accepts_truthy_values(monkeypatch):
    monkeypatch.setenv("TFM_ENABLE_DEBUG_COMMANDS", "on")
    assert main_window_controller_module.MainWindowController._is_debug_matrix_command_enabled() is True


def test_main_window_preview_entry_opens_isolated_session_with_scope(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.view = object()
    calls = []
    closed = []

    controller.matrix_session_registry = SimpleNamespace(
        open_scope=lambda session_id, mode: (
            calls.append(("open_scope", session_id, mode))
            or SimpleNamespace(close=lambda: closed.append(session_id))
        ),
        release_session=lambda session_id: calls.append(("release_session", session_id)),
    )

    def _create(parent_view=None, **kwargs):
        calls.append(("create", kwargs.get("mode"), kwargs.get("session_id")))
        return SimpleNamespace(matrix_project_controller=object())

    # Ensure the manager uses our injected session factory, independent of import order.
    from src.features.matrix.service.matrix_session_manager import MatrixSessionManager

    class _SessionFactory:
        create = staticmethod(_create)

    controller._matrix_preview_session_manager = MatrixSessionManager(
        parent_view=controller.view,
        registry=controller.matrix_session_registry,
        session_factory=_SessionFactory,
    )

    session = controller.open_isolated_matrix_preview_session("preview:a")
    reused = controller.open_isolated_matrix_preview_session("preview:a")

    assert session is reused
    assert calls == [
        ("open_scope", "preview:a", "isolated"),
        ("create", "isolated", "preview:a"),
    ]
    assert closed == []


def test_main_window_preview_entry_supports_multi_scope_independent_release(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.view = object()
    closed = []

    controller.matrix_session_registry = SimpleNamespace(
        open_scope=lambda session_id, mode: SimpleNamespace(close=lambda: closed.append(session_id)),
        release_session=lambda session_id: closed.append(f"release:{session_id}"),
    )

    from src.features.matrix.service.matrix_session_manager import MatrixSessionManager

    class _SessionFactory:
        create = staticmethod(
            lambda parent_view=None, **kwargs: SimpleNamespace(matrix_project_controller=object())
        )

    controller._matrix_preview_session_manager = MatrixSessionManager(
        parent_view=controller.view,
        registry=controller.matrix_session_registry,
        session_factory=_SessionFactory,
    )

    controller.open_isolated_matrix_preview_session("preview:a")
    controller.open_isolated_matrix_preview_session("preview:b")

    controller.close_isolated_matrix_preview_session("preview:a")

    assert closed == ["preview:a"]
    assert "preview:b" in controller._matrix_preview_session_manager.list_session_ids()

    controller.close_isolated_matrix_preview_session("preview:b")
    assert closed == ["preview:a", "preview:b"]


def test_main_window_debug_open_preview_requires_debug_mode(monkeypatch):
    controller = object.__new__(MainWindowController)
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: False),
    )

    assert controller.debug_open_isolated_matrix_preview_session() is None


def test_main_window_debug_open_preview_generates_session_id_and_opens_workspace(monkeypatch):
    controller = object.__new__(MainWindowController)
    workspace_opened = []

    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )
    controller._matrix_session_entry_policies = SimpleNamespace(
        get=lambda name: SimpleNamespace(mode="isolated", session_id_prefix="debug:preview:")
    )
    controller._matrix_session_orchestrator = SimpleNamespace(
        open_debug_preview=lambda **kwargs: (
            "debug:preview:1",
            SimpleNamespace(
                matrix_project_controller=SimpleNamespace(
                    open_matrix_workspace=lambda: workspace_opened.append("debug:preview:1")
                )
            ),
        ),
        get_debug_state=lambda registry_snapshot=None: {
            "preview_session_ids": ("debug:preview:1",),
            "registry_default_mode": "shared",
            "registry_active_isolated_session_ids": ("debug:preview:1",),
        },
    )

    session_id = controller.debug_open_isolated_matrix_preview_session()

    assert session_id == "debug:preview:1"
    assert workspace_opened == ["debug:preview:1"]


def test_main_window_debug_open_preview_uses_injected_policy_prefix(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller._matrix_session_entry_policies = SimpleNamespace(
        get=lambda name: SimpleNamespace(mode="isolated", session_id_prefix="custom:preview:")
    )
    calls = []

    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )
    controller._matrix_session_orchestrator = SimpleNamespace(
        open_debug_preview=lambda **kwargs: (
            calls.append(
                (
                    kwargs.get("session_id"),
                    kwargs.get("mode"),
                    kwargs.get("session_id_prefix"),
                    kwargs.get("entry_name"),
                )
            )
            or ("custom:preview:1", SimpleNamespace(matrix_project_controller=None))
        )
    )
    controller._debug_publish_matrix_session_state = lambda action: None

    session_id = controller.debug_open_isolated_matrix_preview_session()

    assert session_id == "custom:preview:1"
    assert calls == [(None, "isolated", "custom:preview:", "debug_preview")]


def test_main_window_debug_open_preview_publishes_session_status(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.service = SimpleNamespace(update_status=Mock())
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )
    controller._matrix_session_entry_policies = SimpleNamespace(
        get=lambda name: SimpleNamespace(mode="isolated", session_id_prefix="debug:preview:")
    )
    controller._matrix_session_orchestrator = SimpleNamespace(
        open_debug_preview=lambda **kwargs: (
            "debug:preview:1", SimpleNamespace(matrix_project_controller=None)
        )
    )
    controller._build_matrix_session_debug_state = lambda: {
        "preview_session_ids": ("debug:preview:1",),
        "registry_default_mode": "shared",
        "registry_session_modes": {},
        "registry_active_isolated_session_ids": ("debug:preview:1",),
        "registry_has_default_isolated_instance": False,
    }

    controller.debug_open_isolated_matrix_preview_session("debug:preview:1")

    controller.service.update_status.assert_called_once_with(
        "[debug:open] preview=1 active_isolated=1 default_mode=shared"
    )


def test_main_window_debug_close_preview_uses_last_session_id(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller._matrix_session_orchestrator = SimpleNamespace(
        close_debug_preview=lambda session_id=None: (True, "debug:preview:7"),
        get_debug_state=lambda registry_snapshot=None: {
            "preview_session_ids": (),
            "registry_default_mode": "shared",
            "registry_active_isolated_session_ids": (),
        },
    )

    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )

    assert controller.debug_close_isolated_matrix_preview_session() is True


def test_main_window_debug_switch_preview_requires_debug_mode(monkeypatch):
    controller = object.__new__(MainWindowController)
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: False),
    )

    assert controller.debug_switch_isolated_matrix_preview_session("preview:a") is False


def test_main_window_debug_switch_preview_returns_false_when_session_not_found(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.service = SimpleNamespace(update_status=Mock())
    controller._matrix_session_orchestrator = SimpleNamespace(
        switch_to_session=lambda session_id, **kwargs: SimpleNamespace(
            success=False,
            session_id=session_id,
            reason="session_not_found",
            session=None,
        )
    )
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )

    assert controller.debug_switch_isolated_matrix_preview_session("preview:missing") is False
    controller.service.update_status.assert_called_once_with(
        "[debug:switch:failed] reason=session_not_found session_id=preview:missing"
    )


def test_main_window_debug_switch_preview_returns_false_with_missing_session_id_reason(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller.service = SimpleNamespace(update_status=Mock())
    controller._matrix_session_orchestrator = SimpleNamespace(
        switch_to_session=lambda session_id, **kwargs: SimpleNamespace(
            success=False,
            session_id=session_id,
            reason="missing_session_id",
            session=None,
        )
    )
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )

    assert controller.debug_switch_isolated_matrix_preview_session("") is False
    controller.service.update_status.assert_called_once_with(
        "[debug:switch:failed] reason=missing_session_id session_id="
    )


def test_main_window_debug_switch_preview_publishes_state_when_success(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller._matrix_session_orchestrator = SimpleNamespace(
        switch_to_session=lambda session_id, **kwargs: SimpleNamespace(
            success=True,
            session_id=session_id,
            reason=None,
            session=SimpleNamespace(matrix_project_controller=None),
            entry_name="preview",
        )
    )
    controller.service = SimpleNamespace(update_status=Mock())
    controller._build_matrix_session_debug_state = lambda: {
        "preview_session_ids": ("preview:a",),
        "registry_default_mode": "shared",
        "registry_active_isolated_session_ids": ("preview:a",),
    }
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )

    assert controller.debug_switch_isolated_matrix_preview_session("preview:a") is True
    controller.service.update_status.assert_called_once_with(
        "[debug:switch] switched_to=preview:a entry=preview preview=1 active_isolated=1 default_mode=shared"
    )


def test_main_window_debug_get_session_state_requires_debug_mode(monkeypatch):
    controller = object.__new__(MainWindowController)
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: False),
    )

    assert controller.debug_get_matrix_session_state() is None


def test_main_window_debug_get_session_state_uses_registry_snapshot(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            session_ids=("preview:a", "preview:b"),
            session_modes={"preview:a": "isolated", "preview:b": "isolated"},
            session_entries={
                "preview:a": "preview",
                "preview:b": "debug_preview",
            },
            entry_counts={"preview": 1, "debug_preview": 1},
            active_isolated_session_ids=("preview:a", "preview:b"),
            total_sessions=2,
        )
    )
    controller.matrix_session_registry = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            default_mode="shared",
            session_modes={"preview:a": "isolated"},
            active_isolated_session_ids=("preview:a",),
            has_default_isolated_instance=False,
        )
    )
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )

    state = controller.debug_get_matrix_session_state()

    assert state == {
        "preview_session_ids": ("preview:a", "preview:b"),
        "registry_default_mode": "shared",
        "registry_session_modes": {"preview:a": "isolated"},
        "registry_active_isolated_session_ids": ("preview:a",),
        "registry_has_default_isolated_instance": False,
        "manager_total_sessions": 2,
        "manager_session_modes": {
            "preview:a": "isolated",
            "preview:b": "isolated",
        },
        "manager_session_entries": {
            "preview:a": "preview",
            "preview:b": "debug_preview",
        },
        "manager_entry_counts": {"preview": 1, "debug_preview": 1},
        "manager_active_isolated_session_ids": ("preview:a", "preview:b"),
        "last_debug_preview_session_id": None,
    }


def test_main_window_debug_get_session_state_prefers_manager_snapshot_over_list(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            session_ids=("snapshot:id",),
            session_modes={"snapshot:id": "isolated"},
            session_entries={"snapshot:id": "debug_preview"},
            entry_counts={"debug_preview": 1},
            active_isolated_session_ids=("snapshot:id",),
            total_sessions=1,
        ),
        list_session_ids=lambda: ("list:id",),
    )
    controller.matrix_session_registry = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            default_mode="shared",
            session_modes={},
            active_isolated_session_ids=(),
            has_default_isolated_instance=False,
        )
    )
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )

    state = controller.debug_get_matrix_session_state()

    assert state["preview_session_ids"] == ("snapshot:id",)
    assert state["manager_total_sessions"] == 1
    assert state["manager_session_entries"] == {"snapshot:id": "debug_preview"}
    assert state["manager_entry_counts"] == {"debug_preview": 1}
    assert state["last_debug_preview_session_id"] is None


def test_main_window_open_preview_passes_preview_entry_name_to_manager():
    controller = object.__new__(MainWindowController)
    controller._matrix_session_entry_policies = SimpleNamespace(
        get=lambda name: SimpleNamespace(mode="isolated")
    )
    calls = []
    controller._matrix_preview_session_manager = SimpleNamespace(
        create_or_get=lambda session_id, **kwargs: (
            calls.append((session_id, kwargs.get("mode"), kwargs.get("entry_name")))
            or SimpleNamespace(matrix_project_controller=None)
        )
    )

    controller.open_isolated_matrix_preview_session("preview:a")

    assert calls == [("preview:a", "isolated", "preview")]


def test_main_window_debug_open_preview_passes_debug_entry_name_to_manager(monkeypatch):
    controller = object.__new__(MainWindowController)
    controller._matrix_session_entry_policies = SimpleNamespace(
        get=lambda name: SimpleNamespace(mode="isolated", session_id_prefix="debug:preview:")
    )
    calls = []
    controller._matrix_session_orchestrator = SimpleNamespace(
        open_debug_preview=lambda **kwargs: (
            calls.append(
                (
                    kwargs.get("session_id"),
                    kwargs.get("mode"),
                    kwargs.get("session_id_prefix"),
                    kwargs.get("entry_name"),
                )
            )
            or ("debug:preview:9", SimpleNamespace(matrix_project_controller=None))
        )
    )
    controller._debug_publish_matrix_session_state = lambda action: None
    monkeypatch.setattr(
        main_window_controller_module.MainWindowController,
        "_is_debug_matrix_command_enabled",
        staticmethod(lambda: True),
    )

    controller.debug_open_isolated_matrix_preview_session("debug:preview:9")

    assert calls == [("debug:preview:9", "isolated", "debug:preview:", "debug_preview")]


def test_project_creator_applies_local_session_side_effects_after_creation():
    controller = object.__new__(ProjectCreatorController)
    controller.matrix_session_mode = "shared"
    controller.parent_view = SimpleNamespace(refresh_table=Mock())
    controller.project_creation_service = Mock()
    controller.project_session_coordinator = Mock()
    controller._apply_matrix_project_context = Mock()
    controller._should_apply_session_side_effects_locally = Mock(return_value=True)

    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-601A",
        "DL-2025-04-601A",
    )
    session_result = SimpleNamespace(
        project_context=project_context,
        dl_number="DL-2025-04-601A",
        ltr_project_loaded=True,
    )
    controller.project_creation_service.open_created_project.return_value = session_result

    controller._open_matrix_editor_with_ltr_number(
        "DL-2025-04-601A",
        r"D:\Projects\DL-2025-04-601A",
    )

    controller.project_creation_service.open_created_project.assert_called_once_with(
        r"D:\Projects\DL-2025-04-601A",
        "DL-2025-04-601A",
    )
    controller.project_session_coordinator.apply_project_context.assert_called_once_with(
        project_context,
        status_message="当前项目: DL-2025-04-601A",
        trigger_matrix_auto_import=True,
    )
    controller._apply_matrix_project_context.assert_called_once_with(project_context)
    controller.parent_view.refresh_table.assert_called_once_with()


def test_project_creator_skips_local_side_effects_when_main_window_controller_exists():
    controller = object.__new__(ProjectCreatorController)
    controller.matrix_session_mode = "shared"
    controller.parent_view = SimpleNamespace(refresh_table=Mock())
    controller.project_creation_service = Mock()
    controller.project_session_coordinator = Mock()
    controller._apply_matrix_project_context = Mock()
    controller._should_apply_session_side_effects_locally = Mock(return_value=False)

    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-602A",
        "DL-2025-04-602A",
    )
    session_result = SimpleNamespace(
        project_context=project_context,
        dl_number="DL-2025-04-602A",
        ltr_project_loaded=False,
    )
    controller.project_creation_service.open_created_project.return_value = session_result

    controller._open_matrix_editor_with_ltr_number(
        "DL-2025-04-602A",
        r"D:\Projects\DL-2025-04-602A",
    )

    controller.project_session_coordinator.apply_project_context.assert_not_called()
    controller._apply_matrix_project_context.assert_not_called()
    controller.parent_view.refresh_table.assert_not_called()


def test_project_creator_isolated_mode_applies_matrix_context_even_when_main_window_controller_exists():
    controller = object.__new__(ProjectCreatorController)
    controller.matrix_session_mode = "isolated"
    controller.parent_view = SimpleNamespace(refresh_table=Mock())
    controller.project_creation_service = Mock()
    controller.project_session_coordinator = Mock()
    controller._apply_matrix_project_context = Mock()
    controller._should_apply_session_side_effects_locally = Mock(return_value=False)

    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-603A",
        "DL-2025-04-603A",
    )
    session_result = SimpleNamespace(
        project_context=project_context,
        dl_number="DL-2025-04-603A",
        ltr_project_loaded=True,
    )
    controller.project_creation_service.open_created_project.return_value = session_result

    controller._open_matrix_editor_with_ltr_number(
        "DL-2025-04-603A",
        r"D:\Projects\DL-2025-04-603A",
    )

    controller.project_session_coordinator.apply_project_context.assert_not_called()
    controller._apply_matrix_project_context.assert_called_once_with(project_context)
    controller.parent_view.refresh_table.assert_called_once_with()


def test_project_creator_cleanup_releases_isolated_session_id():
    released = []
    controller = object.__new__(ProjectCreatorController)
    controller._event_subscribed = False
    controller.matrix_session_mode = "isolated"
    controller.matrix_session_id = "pilot:new-file"
    controller.matrix_session_registry = SimpleNamespace(
        release_session=lambda session_id: released.append(session_id)
    )

    controller.cleanup()

    assert released == ["pilot:new-file"]


def test_project_creator_cleanup_does_not_release_for_shared_mode():
    released = []
    controller = object.__new__(ProjectCreatorController)
    controller._event_subscribed = False
    controller.matrix_session_mode = "shared"
    controller.matrix_session_id = "pilot:new-file"
    controller.matrix_session_registry = SimpleNamespace(
        release_session=lambda session_id: released.append(session_id)
    )

    controller.cleanup()

    assert released == []


def test_project_creator_cleanup_prefers_scope_close_over_registry_release():
    released = []
    scope_closed = []
    controller = object.__new__(ProjectCreatorController)
    controller._event_subscribed = False
    controller.matrix_session_mode = "isolated"
    controller.matrix_session_id = "pilot:new-file"
    controller._matrix_session_scope = SimpleNamespace(close=lambda: scope_closed.append(True))
    controller.matrix_session_registry = SimpleNamespace(
        release_session=lambda session_id: released.append(session_id)
    )

    controller.cleanup()

    assert scope_closed == [True]
    assert released == []


def test_main_window_shutdown_cleans_isolated_preview_sessions_before_export():
    controller = object.__new__(MainWindowController)
    close_calls = []
    controller._matrix_preview_session_manager = SimpleNamespace(
        close_by_mode=lambda mode: close_calls.append(mode) or ("preview:a",)
    )
    auto_export = Mock()
    save_state = Mock()
    controller.view = SimpleNamespace(matrix_controller=SimpleNamespace(
        auto_export_matrix_data_on_shutdown=auto_export
    ))
    controller.service = SimpleNamespace(save_application_state=save_state)

    controller.shutdown()

    assert close_calls == ["isolated"]
    auto_export.assert_called_once_with()
    save_state.assert_called_once_with()


def test_main_window_shutdown_falls_back_to_close_all_when_mode_close_unavailable():
    controller = object.__new__(MainWindowController)
    close_all_calls = []
    controller._matrix_preview_session_manager = SimpleNamespace(
        close_all=lambda: close_all_calls.append(True) or ("preview:a", "preview:b")
    )
    auto_export = Mock()
    save_state = Mock()
    controller.view = SimpleNamespace(matrix_controller=SimpleNamespace(
        auto_export_matrix_data_on_shutdown=auto_export
    ))
    controller.service = SimpleNamespace(save_application_state=save_state)

    controller.shutdown()

    assert close_all_calls == [True]
    auto_export.assert_called_once_with()
    save_state.assert_called_once_with()


def test_main_window_workspace_binding_defaults_to_shared_metadata():
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            active_session_id=None,
            session_modes={},
            session_entries={},
        )
    )

    binding = controller.get_matrix_workspace_session_binding()

    assert binding == {
        "session_id": "main:shared",
        "entry_name": "main",
        "mode": "shared",
    }


def test_main_window_workspace_binding_reads_active_session_metadata():
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            active_session_id="preview:a",
            session_modes={"preview:a": "isolated"},
            session_entries={"preview:a": "preview"},
        )
    )

    binding = controller.get_matrix_workspace_session_binding()

    assert binding == {
        "session_id": "preview:a",
        "entry_name": "preview",
        "mode": "isolated",
    }


def test_main_window_workspace_consistency_uses_default_shared_when_no_binding_and_no_active():
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            active_session_id=None,
            page_session_bindings={},
        )
    )

    result = controller.ensure_matrix_workspace_session_consistency()

    assert result == {
        "success": True,
        "reason": "default_shared_binding",
        "page_id": "matrix.main",
        "active_session_id": None,
        "bound_session_id": None,
        "rollback_performed": False,
    }


def test_main_window_workspace_consistency_binds_page_to_active_when_unbound():
    calls = []
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            active_session_id="preview:a",
            page_session_bindings={},
        ),
        bind_page_session=lambda page_id, session_id: calls.append((page_id, session_id)) or True,
    )

    result = controller.ensure_matrix_workspace_session_consistency()

    assert result["success"] is True
    assert result["bound_session_id"] == "preview:a"
    assert calls == [("matrix.main", "preview:a")]


def test_main_window_workspace_consistency_switches_when_binding_differs_from_active():
    calls = []
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            active_session_id="preview:active",
            page_session_bindings={"matrix.main": "preview:target"},
        ),
    )
    controller._matrix_session_orchestrator = SimpleNamespace(
        bind_page_session=lambda page_id, session_id, **kwargs: (
            calls.append(
                (
                    page_id,
                    session_id,
                    kwargs.get("expected_entry_names"),
                    kwargs.get("requested_by"),
                )
            )
            or SimpleNamespace(
                success=True,
                reason=None,
                active_session_id="preview:target",
                rollback_performed=False,
            )
        )
    )

    result = controller.ensure_matrix_workspace_session_consistency()

    assert result == {
        "success": True,
        "reason": None,
        "page_id": "matrix.main",
        "active_session_id": "preview:target",
        "bound_session_id": "preview:target",
        "rollback_performed": False,
    }
    assert calls == [
        (
            "matrix.main",
            "preview:target",
            ("main", "new_file_pilot", "preview", "debug_preview"),
            "main_window.matrix_workspace.page_visible",
        )
    ]


def test_main_window_workspace_consistency_reports_rollback_when_switch_fails():
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            active_session_id="preview:active",
            page_session_bindings={"matrix.main": "preview:target"},
        ),
    )
    controller._matrix_session_orchestrator = SimpleNamespace(
        bind_page_session=lambda page_id, session_id, **kwargs: SimpleNamespace(
            success=False,
            reason="activation_failed",
            active_session_id="preview:active",
            rollback_performed=True,
        )
    )

    result = controller.ensure_matrix_workspace_session_consistency()

    assert result == {
        "success": False,
        "reason": "activation_failed",
        "page_id": "matrix.main",
        "active_session_id": "preview:active",
        "bound_session_id": "preview:target",
        "rollback_performed": True,
    }


def test_main_window_workspace_hidden_unbinds_page_session():
    calls = []
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        unbind_page_session=lambda page_id: calls.append(page_id) or True
    )

    result = controller.handle_matrix_workspace_hidden()

    assert result is True
    assert calls == ["matrix.main"]


def test_main_window_shutdown_clears_page_bindings_before_isolated_close():
    calls = []
    controller = object.__new__(MainWindowController)
    controller._matrix_preview_session_manager = SimpleNamespace(
        clear_page_session_bindings=lambda: calls.append("clear_page_bindings") or ("matrix.main",),
        close_by_mode=lambda mode: calls.append(("close_by_mode", mode)) or ("preview:a",),
    )
    auto_export = Mock()
    save_state = Mock()
    controller.view = SimpleNamespace(matrix_controller=SimpleNamespace(
        auto_export_matrix_data_on_shutdown=auto_export
    ))
    controller.service = SimpleNamespace(save_application_state=save_state)

    controller.shutdown()

    assert calls == ["clear_page_bindings", ("close_by_mode", "isolated")]
    auto_export.assert_called_once_with()
    save_state.assert_called_once_with()
