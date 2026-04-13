"""
架构守护测试：验证 MainWindow 通过 MatrixWorkspaceFacade 统一注入依赖
"""
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


def test_main_window_init_accepts_facade_injection():
    """验证 MainWindow.__init__ 接受单一 matrix_workspace_facade 参数"""
    module_ast = _load_main_window_ui_ast()
    init_node = _find_class_method(module_ast, "MainWindow", "__init__")
    assert init_node is not None

    kwonly = {arg.arg for arg in init_node.args.kwonlyargs}
    # 新架构：只接受 matrix_workspace_facade
    assert "matrix_workspace_facade" in kwonly, (
        "MainWindow.__init__ must accept 'matrix_workspace_facade' kwarg for unified session injection"
    )


def test_main_window_init_no_individual_session_args():
    """验证 MainWindow.__init__ 不再接受 7 个独立的 session 参数"""
    module_ast = _load_main_window_ui_ast()
    init_node = _find_class_method(module_ast, "MainWindow", "__init__")
    assert init_node is not None

    kwonly = {arg.arg for arg in init_node.args.kwonlyargs}
    individual_args = {
        "matrix_session_registry",
        "matrix_session_entry_policies",
        "matrix_session_manager",
        "matrix_session_orchestrator",
        "matrix_session_debug_facade",
        "matrix_session_entry_facade",
        "matrix_workspace_coordinator",
    }
    leaked = individual_args & kwonly
    assert not leaked, (
        f"MainWindow.__init__ must NOT accept individual session args (architecture change): "
        f"found={sorted(leaked)}"
    )


def test_main_window_init_creates_workspace_facade():
    """验证 MainWindow.__init__ 创建或使用 _workspace_facade"""
    module_ast = _load_main_window_ui_ast()
    init_node = _find_class_method(module_ast, "MainWindow", "__init__")
    assert init_node is not None

    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "view"
        / "main_window_ui.py"
    )
    source = source_path.read_text(encoding="utf-8")

    # 检查是否使用了 _workspace_facade
    assert "_workspace_facade" in source, (
        "MainWindow must use '_workspace_facade' to encapsulate Matrix session objects"
    )


def test_main_window_initialize_controllers_uses_facade():
    """验证 _initialize_controllers 通过 facade 注入依赖"""
    module_ast = _load_main_window_ui_ast()
    initialize_node = _find_class_method(module_ast, "MainWindow", "_initialize_controllers")
    assert initialize_node is not None

    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "view"
        / "main_window_ui.py"
    )
    source = source_path.read_text(encoding="utf-8")

    # 新架构：只传递 matrix_workspace_facade
    assert "matrix_workspace_facade=" in source, (
        "_initialize_controllers must pass 'matrix_workspace_facade' to MainWindowController"
    )


def test_main_window_controller_accepts_facade():
    """验证 MainWindowController.__init__ 接受 matrix_workspace_facade 参数"""
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "controller"
        / "main_window_controller.py"
    )
    source = source_path.read_text(encoding="utf-8")

    assert "matrix_workspace_facade" in source, (
        "MainWindowController must accept 'matrix_workspace_facade' parameter"
    )


def test_main_window_controller_uses_facade_delegation():
    """验证 MainWindowController 通过 facade 委托获取 session 对象"""
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "controller"
        / "main_window_controller.py"
    )
    source = source_path.read_text(encoding="utf-8")

    # Controller 应该使用 _facade 来获取 session 对象
    assert "self._facade" in source, (
        "MainWindowController must use 'self._facade' to access Matrix session objects"
    )


def test_assembler_creates_facade():
    """验证 assembler 创建 MatrixWorkspaceFacade"""
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "app"
        / "composition"
        / "main_window_assembler.py"
    )
    source = source_path.read_text(encoding="utf-8")

    assert "MatrixWorkspaceFacade" in source, (
        "main_window_assembler must create MatrixWorkspaceFacade"
    )
    assert "matrix_workspace_facade=" in source, (
        "main_window_assembler must pass 'matrix_workspace_facade' to MainWindow"
    )


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
