import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


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


matrix_project_controller_module = _load_module(
    "test_matrix_project_controller_module",
    "src/features/matrix/controller/matrix_project_controller.py",
    stub_modules={
        "src.features.matrix.controller.matrix_controller": {
            "MatrixController": lambda parent=None: SimpleNamespace(
                set_ltr_integration_service=Mock(),
                set_ltr_data=Mock(),
                initialize_with_ltr_data=Mock(return_value=True),
                activate_matrix_workspace=Mock(return_value=True),
            )
        },
    },
)


MatrixProjectController = matrix_project_controller_module.MatrixProjectController


def test_set_ltr_integration_service_routes_ltr_data_through_matrix_controller(monkeypatch):
    # MatrixProjectController imports LTRApplicationData lazily inside the method.
    # Stub it only for the duration of this call to keep the test isolated.
    stub_module = types.ModuleType("src.features.ltr_manager.model.ltr_application_data")
    stub_module.LTRApplicationData = type(
        "LTRApplicationData",
        (),
        {"from_dict": staticmethod(lambda data: {"converted": data})},
    )
    monkeypatch.setitem(
        sys.modules,
        "src.features.ltr_manager.model.ltr_application_data",
        stub_module,
    )

    injected_matrix_controller = SimpleNamespace(
        set_ltr_integration_service=Mock(),
        set_ltr_data=Mock(),
        initialize_with_ltr_data=Mock(return_value=True),
        activate_matrix_workspace=Mock(return_value=True),
    )
    controller = MatrixProjectController(matrix_controller=injected_matrix_controller)
    ltr_integration_service = SimpleNamespace(
        current_ltr_data={"DL": "DL-2025-04-601A"},
    )

    controller.set_ltr_integration_service(ltr_integration_service)

    controller.matrix_controller.set_ltr_integration_service.assert_called_once_with(
        ltr_integration_service
    )
    controller.matrix_controller.set_ltr_data.assert_called_once_with(
        {"converted": {"DL": "DL-2025-04-601A"}}
    )


def test_matrix_project_controller_prefers_injected_matrix_controller():
    injected_matrix_controller = SimpleNamespace()

    controller = MatrixProjectController(matrix_controller=injected_matrix_controller)

    assert controller.matrix_controller is injected_matrix_controller
