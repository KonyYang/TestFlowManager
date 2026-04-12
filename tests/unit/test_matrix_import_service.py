from types import SimpleNamespace

from src.core.project_context import ProjectContext
from src.features.matrix.service.matrix_import_service import MatrixImportService


class DummyParser:
    def __init__(self, result):
        self.result = result
        self.parsed_paths = []

    def parse(self, file_path):
        self.parsed_paths.append(file_path)
        return self.result


def test_import_from_project_loads_matrix_file_into_data_model(tmp_path):
    project_dir = tmp_path / "DL-2025-04-701A"
    matrix_file = project_dir / "matrix.xlsx"
    project_dir.mkdir(parents=True)
    matrix_file.write_text("", encoding="utf-8")

    data_model = SimpleNamespace(
        rows=[],
        headers=[],
        merged_cells_info=[],
        _column_index_to_letter=lambda index: chr(65 + index),
    )
    parser = DummyParser(
        {
            "data": [["A1", "B1"]],
            "headers": ["Item", "Group1"],
            "merged_cells": [{"row": 1, "col": 1}],
        }
    )
    service = MatrixImportService(parser=parser)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-701A")

    result = service.import_from_project(data_model, project_context)

    assert result is True
    assert parser.parsed_paths == [str(matrix_file)]
    assert data_model.rows == [["A1", "B1"]]
    assert data_model.headers == ["Item", "Group1"]
    assert data_model.merged_cells_info == [{"row": 1, "col": 1}]


def test_import_from_excel_generates_default_headers_when_missing():
    data_model = SimpleNamespace(
        rows=[],
        headers=[],
        merged_cells_info=[],
        _column_index_to_letter=lambda index: chr(65 + index),
    )
    parser = DummyParser({"data": [["A1", "B1", "C1"]]})
    service = MatrixImportService(parser=parser)

    result = service.import_from_excel("dummy.xlsx", data_model=data_model)

    assert result is True
    assert data_model.headers == ["A", "B", "C"]


def test_import_from_project_returns_false_when_matrix_file_missing(tmp_path):
    project_dir = tmp_path / "DL-2025-04-702A"
    project_dir.mkdir(parents=True)
    data_model = SimpleNamespace(
        rows=[],
        headers=[],
        merged_cells_info=[],
        _column_index_to_letter=lambda index: chr(65 + index),
    )
    parser = DummyParser({"data": [["A1"]]})
    service = MatrixImportService(parser=parser)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-702A")

    result = service.import_from_project(data_model, project_context)

    assert result is False
    assert parser.parsed_paths == []


def test_import_from_spec_delegates_to_spec_processing_service():
    spec_processing_service = SimpleNamespace(
        import_from_spec=lambda file_path, page_number, keyword: {
            "success": True,
            "file_path": file_path,
            "page_number": page_number,
            "keyword": keyword,
        }
    )
    service = MatrixImportService(spec_processing_service=spec_processing_service)

    result = service.import_from_spec("demo.docx", page_number=3, keyword="shock")

    assert result == {
        "success": True,
        "file_path": "demo.docx",
        "page_number": 3,
        "keyword": "shock",
    }
