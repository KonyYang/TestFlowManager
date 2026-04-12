import importlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

def _ensure_stub_module(module_name: str, attrs: dict, originals: dict | None = None):
    if originals is not None and module_name not in originals:
        originals[module_name] = sys.modules.get(module_name, None)
    module = types.ModuleType(module_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module_name] = module


def _load_matrix_service_module():
    module_name = "test_matrix_service_module"
    if module_name in sys.modules:
        return sys.modules[module_name]

    originals = {}

    _ensure_stub_module("src.features.matrix.model.matrix_data", {"MatrixData": type("MatrixData", (), {})}, originals)
    _ensure_stub_module("src.features.matrix.service.matrix_cell_service", {"MatrixCellService": type("MatrixCellService", (), {})}, originals)
    _ensure_stub_module("src.features.matrix.service.matrix_initializer", {"MatrixInitializer": type("MatrixInitializer", (), {"__init__": lambda self, data_model: None})}, originals)
    _ensure_stub_module("src.features.matrix.service.base.matrix_base_operation_service", {"MatrixBaseOperationService": type("MatrixBaseOperationService", (), {"__init__": lambda self, data_model: None})}, originals)
    _ensure_stub_module("src.features.matrix.service.base.matrix_formatting_service", {"MatrixFormattingService": type("MatrixFormattingService", (), {"__init__": lambda self, cell_service: None})}, originals)
    _ensure_stub_module("src.features.matrix.service.export.controller.export_controller", {"ExportController": type("ExportController", (), {"__init__": lambda self, data_model, parent=None: None})}, originals)
    _ensure_stub_module("src.features.matrix.service.export.model.export_data_model", {"ExportDataModel": type("ExportDataModel", (), {"__init__": lambda self, data_model: None})}, originals)
    _ensure_stub_module("src.features.matrix.service.spec.matrix_spec_processing_service", {"MatrixSpecProcessingService": type("MatrixSpecProcessingService", (), {"__init__": lambda self, data_model, template_filler: None, "last_imported_spec_path": None})}, originals)
    _ensure_stub_module("src.features.matrix.service.processing.matrix_data_structure_service", {"MatrixDataStructureService": type("MatrixDataStructureService", (), {"__init__": lambda self, data_model, data_structure: None})}, originals)
    _ensure_stub_module("src.features.matrix.service.matrix_import_service", {"MatrixImportService": type("MatrixImportService", (), {"__init__": lambda self, data_model=None, parser=None, spec_processing_service=None: None, "import_from_excel": lambda self, file_path: True, "import_from_spec": lambda self, file_path, page_number=None, keyword=None: {"success": True}})}, originals)
    _ensure_stub_module("src.features.matrix.model.matrix_data_structure", {"MatrixDataStructure": type("MatrixDataStructure", (), {})}, originals)
    _ensure_stub_module("src.features.matrix.service.template.template_filler", {"TemplateFiller": type("TemplateFiller", (), {})}, originals)
    _ensure_stub_module(
        "src.core.logger",
        {"logger": types.SimpleNamespace(debug=lambda *a, **k: None, info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)},
        originals,
    )

    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "matrix"
        / "service"
        / "matrix_service.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    return module


def _load_matrix_controller_module(matrix_service_class):
    module_name = "test_matrix_controller_module"
    if module_name in sys.modules:
        del sys.modules[module_name]

    originals = {}

    qtwidgets_module = types.ModuleType("PyQt5.QtWidgets")
    qtwidgets_module.QFileDialog = type("QFileDialog", (), {})
    qtwidgets_module.QMessageBox = type("QMessageBox", (), {})
    sys.modules.setdefault("PyQt5", types.ModuleType("PyQt5"))
    originals["PyQt5.QtWidgets"] = sys.modules.get("PyQt5.QtWidgets", None)
    sys.modules["PyQt5.QtWidgets"] = qtwidgets_module

    _ensure_stub_module(
        "src.features.matrix.service.matrix_application_service",
        {
            "MatrixApplicationService": type(
                "MatrixApplicationService",
                (),
                {"__init__": lambda self, matrix_service: None},
            )
        },
        originals,
    )
    _ensure_stub_module(
        "src.features.matrix.service.export.controller.export_controller",
        {"ExportController": type("ExportController", (), {"__init__": lambda self, data_model, parent=None: None})},
        originals,
    )
    _ensure_stub_module(
        "src.core.logger",
        {"logger": types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None, debug=lambda *a, **k: None)},
        originals,
    )
    _ensure_stub_module(
        "src.core.project_context",
        {
            "ProjectContext": object,
            "get_current_project_context": lambda: None,
        },
        originals,
    )

    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "matrix"
        / "controller"
        / "matrix_controller.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    return module


def test_matrix_service_shared_returns_singleton_instance():
    matrix_service_module = _load_matrix_service_module()
    MatrixService = matrix_service_module.MatrixService

    assert MatrixService.shared() is MatrixService.shared()
    assert MatrixService.shared() is not MatrixService()


def test_matrix_service_create_isolated_returns_distinct_instance():
    matrix_service_module = _load_matrix_service_module()
    MatrixService = matrix_service_module.MatrixService

    shared_instance = MatrixService.shared()
    isolated_instance = MatrixService.create_isolated()

    assert isolated_instance is not shared_instance
    assert isinstance(isolated_instance, MatrixService)


def test_matrix_service_constructor_returns_distinct_instance():
    matrix_service_module = _load_matrix_service_module()
    MatrixService = matrix_service_module.MatrixService

    first = MatrixService()
    second = MatrixService()

    assert first is not second


def test_matrix_service_uses_class_level_shared_instance():
    matrix_service_module = _load_matrix_service_module()
    MatrixService = matrix_service_module.MatrixService

    shared_instance = MatrixService.shared()

    assert MatrixService._shared_instance is shared_instance


def test_matrix_controller_uses_shared_matrix_service():
    matrix_controller_module = _load_matrix_controller_module(
        type("StubMatrixService", (), {"shared": classmethod(lambda cls: object())})
    )
    try:
        matrix_controller_module.MatrixController()
        raise AssertionError("MatrixController should require explicit matrix_service injection")
    except ValueError as exc:
        assert "matrix_service is required" in str(exc)


def test_matrix_service_provider_module_is_removed():
    module_name = "src.features.matrix.service.matrix_service_provider"
    sys.modules.pop(module_name, None)
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)


def test_matrix_controller_prefers_injected_service_and_application_service():
    matrix_controller_module = _load_matrix_controller_module(type("UnusedMatrixService", (), {"shared": classmethod(lambda cls: (_ for _ in ()).throw(AssertionError("shared should not be called")))}))
    injected_service = types.SimpleNamespace(data_model=object())
    injected_application_service = object()

    controller = matrix_controller_module.MatrixController(
        matrix_service=injected_service,
        application_service=injected_application_service,
    )

    assert controller.service is injected_service
    assert controller.application_service is injected_application_service


def test_matrix_controller_defaults_to_no_project_context():
    matrix_service_module = _load_matrix_service_module()
    matrix_controller_module = _load_matrix_controller_module(matrix_service_module.MatrixService)

    controller = matrix_controller_module.MatrixController(
        matrix_service=types.SimpleNamespace(data_model=object()),
        application_service=object(),
    )

    assert controller.get_project_context() is None


def test_matrix_controller_has_no_legacy_get_matrix_service_api():
    matrix_service_module = _load_matrix_service_module()
    matrix_controller_module = _load_matrix_controller_module(matrix_service_module.MatrixService)

    controller = matrix_controller_module.MatrixController(
        matrix_service=types.SimpleNamespace(data_model=object()),
        application_service=object(),
    )

    assert not hasattr(controller, "get_matrix_service")
