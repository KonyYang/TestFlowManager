import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


def _load_module(module_name: str, relative_path: str):
    module_path = Path(__file__).resolve().parents[2] / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_import_export_manager_defaults_to_no_project_context():
    module = _load_module(
        "test_import_export_manager_module",
        "src/features/matrix/view/managers/import_export_manager.py",
    )
    manager = module.ImportExportManager(view=SimpleNamespace(), matrix_controller=None)

    assert manager._get_active_project_context() is None
