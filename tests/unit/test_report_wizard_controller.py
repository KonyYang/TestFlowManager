import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace


def _load_module(module_name: str, relative_path: str, stub_modules=None):
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


class _DialogStub:
    Accepted = 1

    def __init__(self, *args, **kwargs):
        self.matrix_controller = None
        self.pages = [SimpleNamespace(set_header_data=lambda data: None)]
        self.finished = SimpleNamespace(connect=lambda callback: None)

    def set_matrix_controller(self, matrix_controller):
        self.matrix_controller = matrix_controller

    def exec_(self):
        return None


def test_report_wizard_controller_uses_matrix_controller_only():
    controller_module = _load_module(
        "test_report_wizard_controller_module",
        "src/features/report_wizard/controller/report_wizard_controller.py",
        stub_modules={
            "src.features.report_wizard.view.report_wizard_dialog": {
                "ReportWizardDialog": _DialogStub,
            },
            "src.features.report_wizard.service.report_generation_service": {
                "ReportGenerationService": lambda: SimpleNamespace(load_project_data=lambda path: None),
            },
        },
    )

    controller = controller_module.ReportWizardController()
    matrix_controller = object()
    controller.set_matrix_controller(matrix_controller)
    controller.show_wizard()

    assert controller.matrix_controller is matrix_controller
    assert controller.view.matrix_controller is matrix_controller


def test_report_wizard_controller_has_no_matrix_service_setter():
    controller_module = _load_module(
        "test_report_wizard_controller_module_no_service",
        "src/features/report_wizard/controller/report_wizard_controller.py",
        stub_modules={
            "src.features.report_wizard.view.report_wizard_dialog": {
                "ReportWizardDialog": _DialogStub,
            },
            "src.features.report_wizard.service.report_generation_service": {
                "ReportGenerationService": lambda: SimpleNamespace(load_project_data=lambda path: None),
            },
        },
    )

    controller = controller_module.ReportWizardController()
    assert not hasattr(controller, "set_matrix_service")
