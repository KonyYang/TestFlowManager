from inspect import signature

from src.core.project_context import ProjectContext
from src.features.report_wizard.view import test_spec_tables_page as page_module


class _MatrixControllerStub:
    def __init__(self, headers, rows, project_context):
        self._headers = headers
        self._rows = rows
        self._project_context = project_context

    def get_matrix_headers(self):
        return self._headers

    def get_matrix_rows(self):
        return self._rows

    def get_project_context(self):
        return self._project_context


def test_worker_uses_controller_matrix_snapshot():
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2026-04-901A",
        "DL-2026-04-901A",
    )
    controller = _MatrixControllerStub(
        headers=["Test Item", "Method", "Condition"],
        rows=[["Item-1", "M-1", "C-1"], ["Time", "", ""]],
        project_context=project_context,
    )
    worker = page_module.TestSpecTablesWorker(
        document_path=r"D:\tmp\report.docx",
        matrix_controller=controller,
    )

    assert worker.matrix_headers == ["Test Item", "Method", "Condition"]
    assert worker.matrix_rows[0][0] == "Item-1"
    assert worker.matrix_data_structure is not None
    assert worker.matrix_data_structure.dl_number == "DL-2026-04-901A"


def test_test_spec_page_no_legacy_matrix_service_argument():
    params = signature(page_module.TestSpecTablesPage.__init__).parameters
    assert "matrix_service" not in params
