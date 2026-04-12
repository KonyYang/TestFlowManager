import importlib.util
import sys
import types
from pathlib import Path


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


report_updater_service_module = _load_module(
    "test_report_updater_service_module",
    "src/features/report_updater/service/report_updater_service.py",
    stub_modules={
        "win32com": {},
        "win32com.client": {
            "Dispatch": lambda *a, **k: None,
            "gencache": types.SimpleNamespace(),
        },
        "win32com.client.gencache": {},
    },
)

report_updater_controller_module = _load_module(
    "test_report_updater_controller_module",
    "src/features/report_updater/controller/report_updater_controller.py",
    stub_modules={
        "PyQt5.QtWidgets": {
            "QWidget": object,
            "QMessageBox": type("QMessageBox", (), {}),
            "QFileDialog": type("QFileDialog", (), {}),
            "QDialog": type("QDialog", (), {}),
        },
        "src.features.report_updater.view.report_updater_dialog": {
            "ReportUpdaterDialog": object,
        },
        "src.features.report_updater.service.report_updater_service": {
            "ReportUpdaterService": report_updater_service_module.ReportUpdaterService,
        },
    },
)


ReportUpdaterService = report_updater_service_module.ReportUpdaterService
ReportUpdaterController = report_updater_controller_module.ReportUpdaterController


def test_report_updater_service_defaults_to_no_project_context():
    service = ReportUpdaterService()

    assert service.project_context is None


def test_report_updater_controller_defaults_to_no_project_context():
    controller = ReportUpdaterController()

    assert controller.project_context is None
    assert controller.current_project_path is None
