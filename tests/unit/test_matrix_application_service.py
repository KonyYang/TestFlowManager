from types import SimpleNamespace

from src.core.project_context import ProjectContext
from src.features.matrix.service.matrix_application_service import MatrixApplicationService


def test_matrix_application_service_delegates_excel_and_spec_import():
    matrix_service = SimpleNamespace(
        import_from_excel=lambda file_path: ("excel", file_path),
        import_from_spec=lambda file_path, page_number=None, keyword=None: {
            "success": True,
            "mode": "spec",
            "file_path": file_path,
            "page_number": page_number,
            "keyword": keyword,
        },
        import_service=SimpleNamespace(import_from_project=lambda project_context=None: True),
    )
    service = MatrixApplicationService(matrix_service)

    assert service.import_from_excel("matrix.xlsx") == ("excel", "matrix.xlsx")
    assert service.import_from_spec("spec.docx", 5, "temp") == {
        "success": True,
        "error": None,
        "post_action": "refresh_only",
        "should_refresh": True,
        "should_initialize": False,
        "should_parse": False,
        "mode": "spec",
        "file_path": "spec.docx",
        "page_number": 5,
        "keyword": "temp",
    }


def test_matrix_application_service_builds_failed_spec_import_post_action():
    matrix_service = SimpleNamespace(
        import_from_excel=lambda file_path: True,
        import_from_spec=lambda file_path, page_number=None, keyword=None: {
            "success": False,
            "error": "extract failed",
        },
        import_service=SimpleNamespace(import_from_project=lambda project_context=None: True),
    )
    service = MatrixApplicationService(matrix_service)

    result = service.import_from_spec("spec.docx")

    assert result == {
        "success": False,
        "error": "extract failed",
        "post_action": "none",
        "should_refresh": False,
        "should_initialize": False,
        "should_parse": False,
    }


def test_matrix_application_service_auto_import_uses_matrix_import_service():
    captured = {}

    def _import_from_project(project_context=None):
        captured["project_context"] = project_context
        return True

    matrix_service = SimpleNamespace(
        import_service=SimpleNamespace(
            import_from_project=_import_from_project
        )
    )
    service = MatrixApplicationService(matrix_service)
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-801A",
        "DL-2025-04-801A",
    )

    result = service.auto_import_from_project(project_context)

    assert result is True
    assert captured["project_context"] == project_context


def test_matrix_application_service_standardize_and_fill_runs_full_flow():
    matrix_service = SimpleNamespace(
        initialize_matrix=lambda: True,
        extract_test_methods_from_spec=lambda: True,
        update_standard_versions=lambda: {"success": True, "updated": 3},
    )
    service = MatrixApplicationService(matrix_service)

    result = service.standardize_and_fill()

    assert result == {
        "success": True,
        "initialized": True,
        "extract_result": True,
        "update_result": {"success": True, "updated": 3},
    }


def test_matrix_application_service_standardize_and_fill_stops_when_initialize_fails():
    matrix_service = SimpleNamespace(
        initialize_matrix=lambda: False,
        extract_test_methods_from_spec=lambda: True,
        update_standard_versions=lambda: {"success": True},
    )
    service = MatrixApplicationService(matrix_service)

    result = service.standardize_and_fill()

    assert result == {
        "success": False,
        "initialized": False,
        "extract_result": False,
        "update_result": {"success": False},
    }


def test_matrix_application_service_delegates_llcr_and_cr_exports():
    calls = []
    matrix_service = SimpleNamespace(
        export_controller=SimpleNamespace(
            update_data_model=lambda data_model: calls.append(("update", data_model)),
            export_by_type=lambda file_path, export_type: calls.append(
                ("export", file_path, export_type)
            )
            or True,
        ),
        data_model=object(),
    )
    service = MatrixApplicationService(matrix_service)

    llcr_result = service.export_llcr(sync_callback=lambda: calls.append("sync_llcr"))
    cr_result = service.export_cr(sync_callback=lambda: calls.append("sync_cr"))

    assert llcr_result is True
    assert cr_result is True
    assert calls == [
        "sync_llcr",
        ("update", matrix_service.data_model),
        ("export", None, "llcr"),
        "sync_cr",
        ("update", matrix_service.data_model),
        ("export", None, "cr"),
    ]


def test_matrix_application_service_initializes_with_ltr_data():
    calls = []
    matrix_service = SimpleNamespace(
        initialize_matrix=lambda: calls.append("initialize"),
    )
    ltr_integration_service = SimpleNamespace(
        is_project_loaded=lambda: True,
        get_ltr_data=lambda: {"DL": "DL-2025-04-999A"},
        get_test_info=lambda: calls.append("test_info"),
    )
    service = MatrixApplicationService(matrix_service)

    result = service.initialize_with_ltr_data(ltr_integration_service)

    assert result is True
    assert calls == ["initialize", "test_info"]


def test_matrix_application_service_skips_ltr_initialization_when_not_loaded():
    matrix_service = SimpleNamespace(
        initialize_matrix=lambda: None,
    )
    ltr_integration_service = SimpleNamespace(
        is_project_loaded=lambda: False,
        get_ltr_data=lambda: {"DL": "DL-2025-04-999A"},
        get_test_info=lambda: None,
    )
    service = MatrixApplicationService(matrix_service)

    result = service.initialize_with_ltr_data(ltr_integration_service)

    assert result is False


def test_matrix_application_service_sets_project_context_on_export_controller():
    calls = []
    matrix_service = SimpleNamespace(
        export_controller=SimpleNamespace(
            set_project_context=lambda project_context: calls.append(project_context)
        )
    )
    service = MatrixApplicationService(matrix_service)
    project_context = ProjectContext.from_project_path(
        r"D:\Projects\DL-2025-04-910A",
        "DL-2025-04-910A",
    )

    service.set_project_context(project_context)

    assert calls == [project_context]


def test_matrix_application_service_sets_ltr_data_via_matrix_service():
    calls = []
    matrix_service = SimpleNamespace(
        set_ltr_data=lambda ltr_data: calls.append(ltr_data)
    )
    service = MatrixApplicationService(matrix_service)

    service.set_ltr_data({"DL": "DL-2025-04-911A"})

    assert calls == [{"DL": "DL-2025-04-911A"}]
