from types import SimpleNamespace
from unittest.mock import Mock

from src.core.project_context import ProjectContext
from src.core.project_session_coordinator import ProjectSessionCoordinator
from src.core.project_session_service import ProjectSessionService


class DummyView:
    def __init__(self, *, has_workspace=True):
        self.window_title = ""
        self.current_dl_number = None
        self.project_context = None
        self._has_workspace = has_workspace
        self.report_updater_controller = Mock()
        self.auto_import_from_project = Mock()
        self.refresh_table = Mock()
        self.activate_matrix_workspace = Mock(return_value=True)

    def setWindowTitle(self, title):
        self.window_title = title

    def update_dl_number_display(self, dl_number):
        self.current_dl_number = dl_number

    def set_matrix_project_context(self, project_context):
        self.project_context = project_context

    def has_matrix_workspace(self):
        return self._has_workspace


def test_project_session_service_open_project_writes_state_and_dispatches_event(monkeypatch):
    service = ProjectSessionService()
    project_context_events = []
    state_changes = []

    monkeypatch.setattr(
        "src.core.project_session_service.state_manager.set_state",
        lambda key, value: state_changes.append((key, value)),
    )
    monkeypatch.setattr(
        "src.core.project_session_service.event_dispatcher.dispatch",
        lambda event_name, payload: project_context_events.append((event_name, payload)),
    )

    result = service.open_project(r"D:\Projects\DL-2025-04-201A", "DL-2025-04-201A")

    assert result.project_path == r"D:\Projects\DL-2025-04-201A"
    assert state_changes == [("current_project_context", result)]
    assert project_context_events == [("project.opened", result.to_event_data())]


def test_project_session_coordinator_applies_context_and_triggers_matrix_refresh(monkeypatch):
    scheduled_callbacks = []
    monkeypatch.setattr(
        "src.core.project_session_coordinator.QTimer.singleShot",
        lambda delay, callback: scheduled_callbacks.append((delay, callback)),
    )

    view = DummyView()
    matrix_controller = Mock()
    matrix_project_controller = SimpleNamespace(matrix_controller=matrix_controller)
    status_messages = []
    coordinator = ProjectSessionCoordinator(
        view,
        matrix_project_controller=matrix_project_controller,
        status_updater=status_messages.append,
    )
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-202A",
        "DL-2025-04-202A",
    )

    coordinator.apply_project_context(
        project_context,
        status_message="已打开项目: DL-2025-04-202A",
        log_message="Project opened successfully",
        trigger_matrix_auto_import=True,
    )

    assert status_messages == ["已打开项目: DL-2025-04-202A"]
    assert view.window_title == "TestFlow Manager - 项目: DL-2025-04-202A"
    assert view.current_dl_number == "DL-2025-04-202A"
    assert view.project_context == project_context
    view.report_updater_controller.set_project_context.assert_called_once_with(project_context)
    matrix_controller.set_project_context.assert_called_once_with(project_context)
    matrix_controller.set_ltr_number.assert_called_once_with("DL-2025-04-202A")
    assert len(scheduled_callbacks) == 1
    assert scheduled_callbacks[0][0] == 0

    scheduled_callbacks[0][1]()

    view.auto_import_from_project.assert_called_once()
    view.refresh_table.assert_not_called()
    view.activate_matrix_workspace.assert_not_called()
    assert [delay for delay, _ in scheduled_callbacks[1:]] == [50, 100]

    scheduled_callbacks[1][1]()
    scheduled_callbacks[2][1]()

    view.refresh_table.assert_called_once()
    view.activate_matrix_workspace.assert_called_once()


def test_project_session_coordinator_skips_auto_import_when_workspace_missing(monkeypatch):
    scheduled_callbacks = []
    monkeypatch.setattr(
        "src.core.project_session_coordinator.QTimer.singleShot",
        lambda delay, callback: scheduled_callbacks.append((delay, callback)),
    )

    view = DummyView(has_workspace=False)
    coordinator = ProjectSessionCoordinator(view)
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-203A",
        "DL-2025-04-203A",
    )

    coordinator.apply_project_context(
        project_context,
        trigger_matrix_auto_import=True,
    )

    assert len(scheduled_callbacks) == 1
    scheduled_callbacks[0][1]()

    view.auto_import_from_project.assert_not_called()
    assert [delay for delay, _ in scheduled_callbacks[1:]] == [50, 100]

    scheduled_callbacks[1][1]()
    scheduled_callbacks[2][1]()

    view.refresh_table.assert_not_called()
    view.activate_matrix_workspace.assert_called_once()


def test_project_session_coordinator_continues_when_auto_import_raises(monkeypatch):
    scheduled_callbacks = []
    monkeypatch.setattr(
        "src.core.project_session_coordinator.QTimer.singleShot",
        lambda delay, callback: scheduled_callbacks.append((delay, callback)),
    )

    view = DummyView()
    view.auto_import_from_project.side_effect = RuntimeError("import failed")
    coordinator = ProjectSessionCoordinator(view)
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-204A",
        "DL-2025-04-204A",
    )

    coordinator.apply_project_context(
        project_context,
        trigger_matrix_auto_import=True,
    )

    scheduled_callbacks[0][1]()

    view.auto_import_from_project.assert_called_once()
    assert [delay for delay, _ in scheduled_callbacks[1:]] == [50, 100]

    scheduled_callbacks[1][1]()
    scheduled_callbacks[2][1]()

    view.refresh_table.assert_called_once()
    view.activate_matrix_workspace.assert_called_once()
