import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from src.core.project_context import ProjectContext


def _load_project_creation_application_service_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "project_creator"
        / "service"
        / "project_creation_application_service.py"
    )
    spec = importlib.util.spec_from_file_location(
        "test_project_creation_application_service_module",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


project_creation_application_service_module = _load_project_creation_application_service_module()
ProjectCreationApplicationService = project_creation_application_service_module.ProjectCreationApplicationService


class DummyMatrixProjectController:
    def __init__(self, matrix_controller, ltr_integration_service=None):
        self.matrix_controller = matrix_controller
        self.ltr_integration_service = ltr_integration_service
        self.set_ltr_integration_service = Mock(side_effect=self._set_ltr_integration_service)

    def _set_ltr_integration_service(self, ltr_integration_service):
        self.ltr_integration_service = ltr_integration_service


def test_open_created_project_returns_none_when_project_path_missing():
    service = ProjectCreationApplicationService(Mock(), Mock())

    assert service.open_created_project("") is None


def test_open_created_project_resolves_dl_number_and_initializes_matrix(monkeypatch):
    ltr_integration_service = Mock()
    ltr_integration_service.load_ltr_project.return_value = {"DL": "DL-2025-04-301A"}
    ltr_integration_service.is_project_loaded.return_value = True
    ltr_integration_service.get_project_json_path.return_value = (
        r"D:\Projects\DL-2025-04-301A\application_data.json"
    )

    matrix_controller = Mock()
    matrix_project_controller = DummyMatrixProjectController(matrix_controller)

    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-301A",
        "DL-2025-04-301A",
    )
    apply_calls = []
    monkeypatch.setattr(
        project_creation_application_service_module.project_session_service,
        "apply_project_context",
        lambda context: apply_calls.append(context) or context,
    )
    monkeypatch.setattr(
        project_creation_application_service_module.ProjectDocumentContext,
        "from_project_context",
        lambda context: SimpleNamespace(dl_number="DL-2025-04-301A"),
    )

    service = ProjectCreationApplicationService(
        ltr_integration_service,
        matrix_project_controller,
    )
    result = service.open_created_project(r"D:\Projects\DL-2025-04-301A")

    assert result is not None
    assert result.project_context == project_context
    assert result.dl_number == "DL-2025-04-301A"
    assert result.ltr_project_loaded is True
    assert apply_calls == [project_context]
    ltr_integration_service.load_ltr_project.assert_called_once_with(r"D:\Projects\DL-2025-04-301A")
    matrix_project_controller.set_ltr_integration_service.assert_called_once_with(ltr_integration_service)
    matrix_controller.set_project_context.assert_not_called()
    matrix_controller.initialize_with_ltr_data.assert_not_called()


def test_open_created_project_skips_matrix_init_when_ltr_project_not_loaded(monkeypatch):
    ltr_integration_service = Mock()
    ltr_integration_service.load_ltr_project.return_value = None
    ltr_integration_service.is_project_loaded.return_value = False
    ltr_integration_service.get_project_json_path.return_value = None

    matrix_controller = Mock()
    matrix_project_controller = DummyMatrixProjectController(
        matrix_controller,
        ltr_integration_service=ltr_integration_service,
    )

    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-302A",
        "DL-2025-04-302A",
    )
    apply_calls = []
    monkeypatch.setattr(
        project_creation_application_service_module.project_session_service,
        "apply_project_context",
        lambda context: apply_calls.append(context) or context,
    )

    service = ProjectCreationApplicationService(
        ltr_integration_service,
        matrix_project_controller,
    )
    result = service.open_created_project(
        r"D:\Projects\DL-2025-04-302A",
        "DL-2025-04-302A",
    )

    assert result is not None
    assert result.ltr_project_loaded is False
    assert apply_calls == [project_context]
    matrix_project_controller.set_ltr_integration_service.assert_not_called()
    matrix_controller.set_project_context.assert_not_called()
    matrix_controller.initialize_with_ltr_data.assert_not_called()
