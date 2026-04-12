import ast
from pathlib import Path


def _load_main_window_ui_ast():
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "view"
        / "main_window_ui.py"
    )
    source = source_path.read_text(encoding="utf-8")
    return ast.parse(source)


def _find_class_method(module_ast, class_name: str, method_name: str):
    for node in module_ast.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    return None


def test_main_window_init_accepts_session_stack_injection():
    module_ast = _load_main_window_ui_ast()
    init_node = _find_class_method(module_ast, "MainWindow", "__init__")
    assert init_node is not None

    kwonly = {arg.arg for arg in init_node.args.kwonlyargs}
    expected = {
        "matrix_session_registry",
        "matrix_session_entry_policies",
        "matrix_session_manager",
        "matrix_session_orchestrator",
        "matrix_session_debug_facade",
        "matrix_session_entry_facade",
    }
    missing = expected - kwonly
    assert not missing, f"MainWindow.__init__ must accept injection args: missing={sorted(missing)}"


def test_main_window_initialize_controllers_injects_policy_table():
    module_ast = _load_main_window_ui_ast()
    initialize_node = _find_class_method(module_ast, "MainWindow", "_initialize_controllers")
    assert initialize_node is not None

    found_injected_arg = False
    for statement in ast.walk(initialize_node):
        if not isinstance(statement, ast.Call):
            continue
        if not isinstance(statement.func, ast.Name) or statement.func.id != "MainWindowController":
            continue
        for kw in statement.keywords:
            if kw.arg != "matrix_session_entry_policies":
                continue
            if (
                isinstance(kw.value, ast.Attribute)
                and isinstance(kw.value.value, ast.Name)
                and kw.value.value.id == "self"
                and kw.value.attr == "matrix_session_entry_policies"
            ):
                found_injected_arg = True
                break

    assert found_injected_arg, "_initialize_controllers must pass UI policy table into MainWindowController"


def test_main_window_initialize_controllers_injects_session_manager():
    module_ast = _load_main_window_ui_ast()
    initialize_node = _find_class_method(module_ast, "MainWindow", "_initialize_controllers")
    assert initialize_node is not None

    found_injected_arg = False
    for statement in ast.walk(initialize_node):
        if not isinstance(statement, ast.Call):
            continue
        if not isinstance(statement.func, ast.Name) or statement.func.id != "MainWindowController":
            continue
        for kw in statement.keywords:
            if kw.arg != "matrix_session_manager":
                continue
            if (
                isinstance(kw.value, ast.Attribute)
                and isinstance(kw.value.value, ast.Name)
                and kw.value.value.id == "self"
                and kw.value.attr == "matrix_session_manager"
            ):
                found_injected_arg = True
                break

    assert found_injected_arg, "_initialize_controllers must pass UI session manager into MainWindowController"


def test_main_window_initialize_controllers_injects_session_orchestrator():
    module_ast = _load_main_window_ui_ast()
    initialize_node = _find_class_method(module_ast, "MainWindow", "_initialize_controllers")
    assert initialize_node is not None

    found_injected_arg = False
    for statement in ast.walk(initialize_node):
        if not isinstance(statement, ast.Call):
            continue
        if not isinstance(statement.func, ast.Name) or statement.func.id != "MainWindowController":
            continue
        for kw in statement.keywords:
            if kw.arg != "matrix_session_orchestrator":
                continue
            if (
                isinstance(kw.value, ast.Attribute)
                and isinstance(kw.value.value, ast.Name)
                and kw.value.value.id == "self"
                and kw.value.attr == "matrix_session_orchestrator"
            ):
                found_injected_arg = True
                break

    assert found_injected_arg, "_initialize_controllers must pass UI orchestrator into MainWindowController"


def test_main_window_initialize_controllers_injects_session_debug_facade():
    module_ast = _load_main_window_ui_ast()
    initialize_node = _find_class_method(module_ast, "MainWindow", "_initialize_controllers")
    assert initialize_node is not None

    found_injected_arg = False
    for statement in ast.walk(initialize_node):
        if not isinstance(statement, ast.Call):
            continue
        if not isinstance(statement.func, ast.Name) or statement.func.id != "MainWindowController":
            continue
        for kw in statement.keywords:
            if kw.arg != "matrix_session_debug_facade":
                continue
            if (
                isinstance(kw.value, ast.Attribute)
                and isinstance(kw.value.value, ast.Name)
                and kw.value.value.id == "self"
                and kw.value.attr == "matrix_session_debug_facade"
            ):
                found_injected_arg = True
                break

    assert found_injected_arg, "_initialize_controllers must pass UI debug facade into MainWindowController"


def test_main_window_initialize_controllers_injects_session_entry_facade():
    module_ast = _load_main_window_ui_ast()
    initialize_node = _find_class_method(module_ast, "MainWindow", "_initialize_controllers")
    assert initialize_node is not None

    found_injected_arg = False
    for statement in ast.walk(initialize_node):
        if not isinstance(statement, ast.Call):
            continue
        if not isinstance(statement.func, ast.Name) or statement.func.id != "MainWindowController":
            continue
        for kw in statement.keywords:
            if kw.arg != "matrix_session_entry_facade":
                continue
            if (
                isinstance(kw.value, ast.Attribute)
                and isinstance(kw.value.value, ast.Name)
                and kw.value.value.id == "self"
                and kw.value.attr == "matrix_session_entry_facade"
            ):
                found_injected_arg = True
                break

    assert found_injected_arg, "_initialize_controllers must pass UI entry facade into MainWindowController"


def test_main_window_page_change_triggers_workspace_session_consistency():
    module_ast = _load_main_window_ui_ast()
    handler_node = _find_class_method(module_ast, "MainWindow", "_on_page_changed_for_matrix")
    assert handler_node is not None

    found_consistency_call = False
    for statement in ast.walk(handler_node):
        if not isinstance(statement, ast.Call):
            continue
        if not isinstance(statement.func, ast.Attribute):
            continue
        if (
            isinstance(statement.func.value, ast.Attribute)
            and isinstance(statement.func.value.value, ast.Name)
            and statement.func.value.value.id == "self"
            and statement.func.value.attr == "controller"
            and statement.func.attr == "ensure_matrix_workspace_session_consistency"
        ):
            found_consistency_call = True
            break

    assert found_consistency_call, (
        "Matrix page-change handler must call controller workspace session consistency check"
    )


def test_main_window_page_change_clears_workspace_binding_when_hidden():
    module_ast = _load_main_window_ui_ast()
    handler_node = _find_class_method(module_ast, "MainWindow", "_on_page_changed_for_matrix")
    assert handler_node is not None

    found_hidden_cleanup_call = False
    for statement in ast.walk(handler_node):
        if not isinstance(statement, ast.Call):
            continue
        if not isinstance(statement.func, ast.Attribute):
            continue
        if (
            isinstance(statement.func.value, ast.Attribute)
            and isinstance(statement.func.value.value, ast.Name)
            and statement.func.value.value.id == "self"
            and statement.func.value.attr == "controller"
            and statement.func.attr == "handle_matrix_workspace_hidden"
        ):
            found_hidden_cleanup_call = True
            break

    assert found_hidden_cleanup_call, (
        "Matrix page-change handler must clear workspace binding when matrix page is hidden"
    )


def test_main_window_debug_ui_handlers_are_removed():
    module_ast = _load_main_window_ui_ast()
    assert _find_class_method(module_ast, "MainWindow", "_on_debug_open_isolated_preview") is None
    assert _find_class_method(module_ast, "MainWindow", "_on_debug_close_isolated_preview") is None
    assert _find_class_method(module_ast, "MainWindow", "_on_debug_switch_isolated_preview") is None
    assert _find_class_method(module_ast, "MainWindow", "_on_debug_query_matrix_session_state") is None


def test_main_window_debug_ui_shortcut_wiring_is_removed():
    ui_source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "view"
        / "main_window_ui.py"
    )
    ui_source = ui_source_path.read_text(encoding="utf-8")
    assert "MatrixSessionDebugCommands.DEBUG_OPEN_SHORTCUT" not in ui_source
    assert "MatrixSessionDebugCommands.DEBUG_CLOSE_SHORTCUT" not in ui_source
    assert "MatrixSessionDebugCommands.DEBUG_SWITCH_SHORTCUT" not in ui_source
    assert "MatrixSessionDebugCommands.DEBUG_QUERY_SHORTCUT" not in ui_source
    assert "_is_legacy_debug_ui_enabled" not in ui_source

    commands_source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "matrix"
        / "service"
        / "matrix_session_debug_commands.py"
    )
    commands_source = commands_source_path.read_text(encoding="utf-8")
    assert "format_state_status" in commands_source
    assert "format_switch_failed" in commands_source
    assert "format_switch_success" in commands_source
    assert "DEBUG_QUERY_SHORTCUT" not in commands_source
    assert "SWITCH_DIALOG_TITLE" not in commands_source
