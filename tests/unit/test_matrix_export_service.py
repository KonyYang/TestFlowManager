from pathlib import Path
from types import SimpleNamespace

from src.core.project_context import ProjectContext
from src.features.matrix.service.matrix_export_service import MatrixExportService


def test_matrix_export_service_delegates_export_with_pre_sync_and_parse(tmp_path):
    calls = []
    matrix_service = SimpleNamespace(
        _sync_table_to_model=lambda: calls.append("sync"),
        _parse_and_structure_matrix_data=lambda: calls.append("parse"),
        export_to_excel=lambda file_path, export_type="matrix_excel": calls.append(
            ("export", file_path, export_type)
        )
        or True,
    )
    service = MatrixExportService(matrix_service)
    output_file = tmp_path / "matrix.xlsx"

    result = service.export_matrix_excel(str(output_file))

    assert result is True
    assert calls == [
        "sync",
        "parse",
        ("export", str(output_file), "matrix_excel"),
    ]


def test_matrix_export_service_resolves_project_matrix_path(tmp_path):
    project_dir = tmp_path / "DL-2025-04-901A"
    project_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-901A")

    result = MatrixExportService.resolve_project_matrix_file_path(project_context)

    assert Path(result) == project_dir / "matrix.xlsx"


def test_matrix_export_service_auto_export_uses_resolved_project_path(tmp_path):
    project_dir = tmp_path / "DL-2025-04-902A"
    project_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-902A")
    calls = []
    matrix_service = SimpleNamespace(
        export_controller=SimpleNamespace(
            export_by_type=lambda file_path, export_type: calls.append(
                (file_path, export_type)
            )
            or True
        )
    )
    service = MatrixExportService(matrix_service)

    result = service.auto_export_to_project(project_context, sync_callback=lambda: calls.append("sync"))

    assert result is True
    assert calls == [
        "sync",
        (str(project_dir / "matrix.xlsx"), "matrix_excel"),
    ]


def test_matrix_export_service_builds_default_filename_from_project_context(tmp_path):
    project_dir = tmp_path / "DL-2025-04-903A"
    project_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-903A")
    service = MatrixExportService(SimpleNamespace())

    result = service.build_default_export_filename(project_context)

    assert Path(result) == project_dir / "matrix.xlsx"


def test_matrix_export_service_returns_structured_failure_kind():
    matrix_service = SimpleNamespace(
        _sync_table_to_model=lambda: None,
        _parse_and_structure_matrix_data=lambda: None,
        export_to_excel=lambda file_path, export_type="matrix_excel": False,
    )
    service = MatrixExportService(matrix_service)

    result = service.export_matrix_excel_with_result(r"D:\not-exist\matrix.xlsx")

    assert result == {
        "success": False,
        "error_kind": "missing_path",
    }


def test_matrix_export_service_exports_llcr_with_sync_callback():
    calls = []
    matrix_service = SimpleNamespace(
        data_model=object(),
        export_controller=SimpleNamespace(
            update_data_model=lambda data_model: calls.append(("update", data_model)),
            export_by_type=lambda file_path, export_type: calls.append(
                ("export", file_path, export_type)
            )
            or True,
        ),
    )
    service = MatrixExportService(matrix_service)

    result = service.export_record_data("llcr", sync_callback=lambda: calls.append("sync"))

    assert result is True
    assert calls == [
        "sync",
        ("update", matrix_service.data_model),
        ("export", None, "llcr"),
    ]
