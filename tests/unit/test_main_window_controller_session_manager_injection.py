import ast
from pathlib import Path


def _load_controller_ast():
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "features"
        / "main_window"
        / "controller"
        / "main_window_controller.py"
    )
    source = source_path.read_text(encoding="utf-8-sig")
    return ast.parse(source)


def _find_class_method(module_ast, class_name: str, method_name: str):
    for node in module_ast.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    return None


def test_main_window_controller_init_accepts_session_manager_injection():
    module_ast = _load_controller_ast()
    init_node = _find_class_method(module_ast, "MainWindowController", "__init__")
    assert init_node is not None

    arg_names = [arg.arg for arg in init_node.args.args]
    assert "matrix_session_manager" in arg_names
    assert "matrix_session_orchestrator" in arg_names
    assert "matrix_session_debug_facade" in arg_names
    assert "matrix_session_entry_facade" in arg_names


def test_main_window_controller_uses_injected_session_manager_with_fallback():
    module_ast = _load_controller_ast()
    init_node = _find_class_method(module_ast, "MainWindowController", "__init__")
    assert init_node is not None

    found_assignment = False
    for statement in ast.walk(init_node):
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue

        target = statement.targets[0]
        value = statement.value
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "_matrix_preview_session_manager"
        ):
            continue
        if not isinstance(value, ast.BoolOp) or not isinstance(value.op, ast.Or):
            continue
        if len(value.values) != 2:
            continue
        if not (isinstance(value.values[0], ast.Name) and value.values[0].id == "matrix_session_manager"):
            continue
        right = value.values[1]
        if (
            isinstance(right, ast.Call)
            and isinstance(right.func, ast.Name)
            and right.func.id == "MatrixSessionManager"
        ):
            found_assignment = True
            break

    assert found_assignment


def test_main_window_controller_uses_injected_orchestrator_with_fallback():
    module_ast = _load_controller_ast()
    init_node = _find_class_method(module_ast, "MainWindowController", "__init__")
    assert init_node is not None

    found_assignment = False
    for statement in ast.walk(init_node):
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue

        target = statement.targets[0]
        value = statement.value
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "_matrix_session_orchestrator"
        ):
            continue
        if not isinstance(value, ast.BoolOp) or not isinstance(value.op, ast.Or):
            continue
        if len(value.values) != 2:
            continue
        if not (
            isinstance(value.values[0], ast.Name)
            and value.values[0].id == "matrix_session_orchestrator"
        ):
            continue
        right = value.values[1]
        if not (
            isinstance(right, ast.Call)
            and isinstance(right.func, ast.Name)
            and right.func.id == "MatrixSessionOrchestrator"
        ):
            continue
        if not right.args:
            continue
        if (
            isinstance(right.args[0], ast.Attribute)
            and isinstance(right.args[0].value, ast.Name)
            and right.args[0].value.id == "self"
            and right.args[0].attr == "_matrix_preview_session_manager"
        ):
            found_assignment = True
            break

    assert found_assignment


def test_main_window_controller_uses_injected_debug_facade_with_fallback():
    module_ast = _load_controller_ast()
    init_node = _find_class_method(module_ast, "MainWindowController", "__init__")
    assert init_node is not None

    found_assignment = False
    for statement in ast.walk(init_node):
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue

        target = statement.targets[0]
        value = statement.value
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "_matrix_session_debug_facade"
        ):
            continue
        if not isinstance(value, ast.BoolOp) or not isinstance(value.op, ast.Or):
            continue
        if len(value.values) != 2:
            continue
        if not (
            isinstance(value.values[0], ast.Name)
            and value.values[0].id == "matrix_session_debug_facade"
        ):
            continue
        right = value.values[1]
        if not (
            isinstance(right, ast.Call)
            and isinstance(right.func, ast.Name)
            and right.func.id == "MatrixSessionDebugFacade"
        ):
            continue
        found_assignment = True
        break

    assert found_assignment


def test_main_window_controller_uses_injected_entry_facade_with_fallback():
    module_ast = _load_controller_ast()
    init_node = _find_class_method(module_ast, "MainWindowController", "__init__")
    assert init_node is not None

    found_assignment = False
    for statement in ast.walk(init_node):
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue

        target = statement.targets[0]
        value = statement.value
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "_matrix_session_entry_facade"
        ):
            continue
        if not isinstance(value, ast.BoolOp) or not isinstance(value.op, ast.Or):
            continue
        if len(value.values) != 2:
            continue
        if not (
            isinstance(value.values[0], ast.Name)
            and value.values[0].id == "matrix_session_entry_facade"
        ):
            continue
        right = value.values[1]
        if not (
            isinstance(right, ast.Call)
            and isinstance(right.func, ast.Name)
            and right.func.id == "MatrixSessionEntryFacade"
        ):
            continue
        found_assignment = True
        break

    assert found_assignment
