import json
from pathlib import Path

from src.core.output_paths import DEFAULT_OUTPUT_DIR, OutputPathResolver
from src.core.project_context import ProjectContext, resolve_project_data_file_path
from src.core.project_document_context import ProjectDocumentContext


def test_resolve_project_data_file_path_prefers_existing_json(tmp_path):
    project_dir = tmp_path / "DL-2025-04-001A"
    project_dir.mkdir()
    project_data_file = project_dir / "application_data.json"
    project_data_file.write_text('{"DL": "DL-2025-04-001A"}', encoding="utf-8")

    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-001A")

    assert resolve_project_data_file_path(project_context) == str(project_data_file)


def test_project_document_context_loads_project_data_and_resolves_workspace_dirs(tmp_path):
    project_dir = tmp_path / "DL-2025-04-002A"
    project_dir.mkdir()
    workspace_dir = project_dir / "DL-2025-04-002A Demo Project"
    submitted_material_dir = workspace_dir / "Submitted Material"
    submitted_material_dir.mkdir(parents=True)

    project_data_file = project_dir / "application_data.json"
    project_data = {"DL": "DL-2025-04-002A", "Requested by": "Alice"}
    project_data_file.write_text(
        json.dumps(project_data, ensure_ascii=False),
        encoding="utf-8",
    )

    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-002A")
    document_context = ProjectDocumentContext.from_project_context(project_context)

    assert document_context.dl_number == "DL-2025-04-002A"
    assert document_context.project_data == project_data
    assert document_context.get_field("Requested by") == "Alice"
    assert document_context.get_submitted_material_dir() == str(submitted_material_dir)
    assert document_context.get_project_workspace_dir() == str(workspace_dir)
    assert document_context.get_test_results_dir(create=True) == str(workspace_dir / "Test results")
    assert (workspace_dir / "Test results").exists()


def test_project_document_context_falls_back_to_project_root_when_workspace_missing(tmp_path):
    project_dir = tmp_path / "DL-2025-04-003A"
    project_dir.mkdir()

    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-003A")
    document_context = ProjectDocumentContext.from_project_context(project_context)

    assert document_context.get_submitted_material_dir() == str(project_dir)
    assert document_context.get_project_workspace_dir() == str(project_dir)
    assert document_context.build_submitted_material_output_path("demo.docx") == str(project_dir / "demo.docx")


def test_output_path_resolver_prefers_project_dirs_and_falls_back_to_default(tmp_path):
    project_dir = tmp_path / "DL-2025-04-004A"
    project_dir.mkdir()
    workspace_dir = project_dir / "DL-2025-04-004A Sample"
    submitted_material_dir = workspace_dir / "Submitted Material"
    submitted_material_dir.mkdir(parents=True)

    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-004A")

    assert OutputPathResolver.resolve_submitted_material_dir(project_context) == str(submitted_material_dir)
    assert OutputPathResolver.resolve_test_results_dir(project_context, create=True) == str(workspace_dir / "Test results")
    assert OutputPathResolver.resolve_project_workspace_dir(project_context) == str(workspace_dir)
    assert OutputPathResolver.build_submitted_material_output_path(project_context, "report.docx") == str(
        submitted_material_dir / "report.docx"
    )

    assert OutputPathResolver.resolve_submitted_material_dir(None) == DEFAULT_OUTPUT_DIR
    assert OutputPathResolver.resolve_test_results_dir(None) == DEFAULT_OUTPUT_DIR
    assert OutputPathResolver.resolve_project_workspace_dir(None) == DEFAULT_OUTPUT_DIR
    assert OutputPathResolver.build_submitted_material_output_path(None, "report.docx") == str(
        Path(DEFAULT_OUTPUT_DIR) / "report.docx"
    )
