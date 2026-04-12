import importlib
import sys


def test_test_spec_tables_service_uses_explicit_matrix_snapshot():
    original_module = sys.modules.pop("src.features.report_wizard.service.test_spec_tables_service", None)
    try:
        module = importlib.import_module(
            "src.features.report_wizard.service.test_spec_tables_service"
        )
        service = module.TestSpecTablesService()

        service.set_matrix_table_data(headers=["Test Item", "Notes"], rows=[["LLCR"], ["Time"]])

        headers, rows = service._get_matrix_table_data()

        assert headers == ["Test Item", "Notes"]
        assert rows == [["LLCR"], ["Time"]]
    finally:
        if original_module is not None:
            sys.modules["src.features.report_wizard.service.test_spec_tables_service"] = original_module
        else:
            sys.modules.pop("src.features.report_wizard.service.test_spec_tables_service", None)
