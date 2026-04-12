import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

from src.core.project_context import ProjectContext
from src.core.project_document_context import ProjectDocumentContext


def _load_module(module_name: str, relative_path: str, stub_modules=None):
    if module_name in sys.modules:
        return sys.modules[module_name]

    original_modules = {}
    if stub_modules:
        for stub_name, attrs in stub_modules.items():
            original_modules[stub_name] = sys.modules.get(stub_name)
            stub_module = types.ModuleType(stub_name)
            for attr_name, attr_value in attrs.items():
                setattr(stub_module, attr_name, attr_value)
            sys.modules[stub_name] = stub_module

    try:
        module_path = Path(__file__).resolve().parents[2] / relative_path
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, original in original_modules.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


record_data_table_export_controller_module = _load_module(
    "test_record_data_table_export_controller_module",
    "src/features/matrix/service/export/controller/record_data_table_export_controller.py",
    stub_modules={
        "PyQt5.QtWidgets": {
            "QFileDialog": type("QFileDialog", (), {}),
            "QMessageBox": type("QMessageBox", (), {}),
            "QDialog": type("QDialog", (), {"Accepted": 1}),
        },
        "src.features.matrix.service.export.service.llcr_cr_export_service": {
            "LLCRCRExportService": lambda data_model: SimpleNamespace(set_matrix_data=lambda *a, **k: None)
        },
        "src.features.matrix.service.export.view.llcr_cr_record_parameters_dialog": {
            "LLCR_CR_RecordParametersDialog": object
        },
    },
)

step_record_ctrl_module = _load_module(
    "test_step_record_controller_module",
    "src/features/step_record_generator/controller/step_record_controller.py",
    stub_modules={
        "src.features.matrix.model.matrix_data_structure": {
            "MatrixDataStructure": type(
                "MatrixDataStructure",
                (),
                {
                    "__init__": lambda self: setattr(self, "group_steps", {"G1": ["step"]}),
                    "parse_matrix_to_structure": lambda self, rows: [],
                },
            )
        },
        "src.features.step_record_generator.service.step_record_service": {
            "StepRecordService": lambda: SimpleNamespace()
        },
    },
)

report_generation_service_module = _load_module(
    "test_report_generation_service_module",
    "src/features/report_wizard/service/report_generation_service.py",
    stub_modules={
        "pythoncom": {"CoInitialize": lambda: None, "CoUninitialize": lambda: None, "com_error": Exception},
        "src.features.report_wizard.service.header_modifier": {"HeaderModifier": object},
        "src.utils.word_utils": {
            "open_docx_document": lambda *a, **k: None,
            "save_docx_document": lambda *a, **k: None,
            "get_shared_word_app": lambda: None,
        },
        "src.features.report_wizard.model.header_data": {"HeaderData": object},
        "src.features.report_wizard.service.test_spec_tables_service": {
            "TestSpecTablesService": object
        },
    },
)

fee_sheet_export_service_module = _load_module(
    "test_fee_sheet_export_service_module",
    "src/features/matrix/service/export/service/fee_sheet_export_service.py",
    stub_modules={
        "pythoncom": {"CoInitialize": lambda: None, "CoUninitialize": lambda: None},
        "win32com": {},
        "win32com.client": {"Dispatch": lambda *a, **k: None},
        "src.features.matrix.model.matrix_data_structure": {"MatrixDataStructure": object},
    },
)


RecordDataTableExportController = record_data_table_export_controller_module.RecordDataTableExportController
StepRecordControllerClass = step_record_ctrl_module.StepRecordController
StepRecordControllerClass.__test__ = False
ReportGenerationService = report_generation_service_module.ReportGenerationService
FeeSheetExportService = fee_sheet_export_service_module.FeeSheetExportService


def test_llcr_cr_default_dir_prefers_project_test_results(tmp_path):
    project_dir = tmp_path / "DL-2025-04-501A"
    workspace_dir = project_dir / "DL-2025-04-501A Demo"
    workspace_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-501A")

    controller = object.__new__(RecordDataTableExportController)
    controller.project_context = project_context
    controller.get_project_context = lambda: project_context

    export_dir = controller._resolve_default_export_dir()

    assert Path(export_dir) == workspace_dir / "Test results"
    assert Path(export_dir).exists()


def test_llcr_cr_export_controller_without_project_context_returns_none():
    controller = object.__new__(RecordDataTableExportController)
    controller.project_context = None

    assert controller.get_project_context() is None


def test_step_record_default_output_path_uses_submitted_material(tmp_path):
    project_dir = tmp_path / "DL-2025-04-502A"
    submitted_material_dir = project_dir / "DL-2025-04-502A Demo" / "Submitted Material"
    submitted_material_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-502A")
    document_context = ProjectDocumentContext.from_project_context(project_context)

    controller = StepRecordControllerClass(project_context=project_context)

    output_path = controller._get_default_output_path(document_context)

    assert Path(output_path) == submitted_material_dir / "DL-2025-04-502A Step Record.docx"


def test_step_record_controller_prefers_matrix_controller_path_and_output_dir(tmp_path):
    project_dir = tmp_path / "DL-2025-04-502B"
    submitted_material_dir = project_dir / "DL-2025-04-502B Demo" / "Submitted Material"
    submitted_material_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-502B")

    captured = {}

    controller = StepRecordControllerClass(
        matrix_controller=SimpleNamespace(
            get_project_context=lambda: project_context,
            get_matrix_rows=lambda: [["group"]],
            create_matrix_data_structure=lambda context: (
                SimpleNamespace(group_steps={"G1": ["step"]}),
                [],
            ),
        ),
        project_context=project_context,
    )
    controller.service = SimpleNamespace(
        generate_step_record_with_structure=lambda matrix_structure, output_path: (
            captured.update(
                {
                    "matrix_structure": matrix_structure,
                    "output_path": output_path,
                }
            )
            or True
        )
    )

    success = controller.generate_step_record()

    assert success is True
    assert Path(captured["output_path"]) == submitted_material_dir / "DL-2025-04-502B Step Record.docx"
    assert captured["matrix_structure"].group_steps == {"G1": ["step"]}


def test_step_record_controller_has_no_legacy_matrix_service_argument():
    params = StepRecordControllerClass.__init__.__code__.co_varnames
    assert "matrix_service" not in params


def test_step_record_controller_without_any_project_context_returns_none():
    controller = StepRecordControllerClass(matrix_controller=None, project_context=None)

    assert controller._get_project_context() is None


def test_report_generation_service_resolves_submitted_material_output_dir(tmp_path):
    project_dir = tmp_path / "DL-2025-04-503A"
    submitted_material_dir = project_dir / "DL-2025-04-503A Demo" / "Submitted Material"
    submitted_material_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-503A")

    service = ReportGenerationService()

    output_dir = service._resolve_output_dir(project_context=project_context)

    assert Path(output_dir) == submitted_material_dir


def test_report_generation_service_builds_report_path_in_submitted_material(tmp_path):
    project_dir = tmp_path / "DL-2025-04-504A"
    submitted_material_dir = project_dir / "DL-2025-04-504A Demo" / "Submitted Material"
    submitted_material_dir.mkdir(parents=True)
    project_context = ProjectContext.from_project_path(str(project_dir), "DL-2025-04-504A")
    header_data = SimpleNamespace(
        report_no="E-3707",
        report_title="Connector Test",
        version="Rev. B",
    )

    service = ReportGenerationService()

    output_path = service.get_generated_report_path(
        header_data,
        project_context=project_context,
    )

    assert Path(output_path) == submitted_material_dir / "E-3707 Connector Test Report_Rev_B.docx"


def test_fee_sheet_service_finds_project_workspace_fee_sheet_file(tmp_path):
    project_dir = tmp_path / "DL-2025-04-505A"
    workspace_dir = project_dir / "DL-2025-04-505A Demo Project"
    workspace_dir.mkdir(parents=True)
    fee_sheet_file = workspace_dir / "DL-2025-04-505A Form for Testing Fee Evaluation.xls"
    fee_sheet_file.write_text("", encoding="utf-8")

    service = FeeSheetExportService()

    result = service._find_fee_sheet_folder_and_file(
        str(project_dir),
        "DL-2025-04-505A",
    )

    assert result == (str(workspace_dir), str(fee_sheet_file))


def test_fee_sheet_service_without_project_context_returns_none():
    service = FeeSheetExportService()

    assert service.get_project_context() is None
