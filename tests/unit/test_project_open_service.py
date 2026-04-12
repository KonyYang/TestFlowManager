import json

from src.features.main_window.service.project_open_service import ProjectOpenService


def test_prepare_project_uses_existing_application_data_json(tmp_path):
    project_dir = tmp_path / "DL-2025-04-101A"
    project_dir.mkdir()
    project_data_file = project_dir / "application_data.json"
    project_data = {"DL": "DL-2025-04-101A", "Requested by": "Bob"}
    project_data_file.write_text(
        json.dumps(project_data, ensure_ascii=False),
        encoding="utf-8",
    )

    service = ProjectOpenService()
    result = service.prepare_project(str(project_dir))

    assert result.created_application_data is False
    assert result.json_file_path == str(project_data_file)
    assert result.project_data == project_data
    assert result.project_context.project_path == str(project_dir)
    assert result.project_context.dl_number == "DL-2025-04-101A"


def test_prepare_project_creates_application_data_when_missing(monkeypatch, tmp_path):
    project_dir = tmp_path / "DL-2025-04-102A"
    project_dir.mkdir()

    service = ProjectOpenService()
    monkeypatch.setattr(
        service,
        "_extract_test_request_data",
        lambda project_path, dl_number: {"Requested by": "Carol", "selected_filename": "request.docx"},
    )
    monkeypatch.setattr(
        service,
        "_build_application_data",
        lambda dl_number, test_request_data: {
            "DL": dl_number,
            "Requested by": test_request_data["Requested by"],
            "selected_filename": test_request_data["selected_filename"],
            "status": "new",
            "error": "",
            "file_path": "",
        },
    )

    result = service.prepare_project(str(project_dir))

    assert result.created_application_data is True
    assert result.project_context.project_path == str(project_dir)
    assert result.project_context.dl_number == "DL-2025-04-102A"
    assert result.project_data["DL"] == "DL-2025-04-102A"
    assert result.project_data["Requested by"] == "Carol"
    assert (project_dir / "application_data.json").exists()


def test_resolve_default_project_path_returns_empty_when_config_path_missing(monkeypatch):
    service = ProjectOpenService()
    monkeypatch.setattr(
        "src.features.main_window.service.project_open_service.config_manager.get_path",
        lambda key, default="": r"D:\Path\That\Does\Not\Exist",
    )

    assert service.resolve_default_project_path() == ""
