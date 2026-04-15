import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


ALLOWED_DIRECT_COORDINATOR_APPLY_CALLERS = {
    # Mainline: side effects are orchestrated via `project.opened` -> MainWindowController._on_project_opened()
    "src/features/main_window/controller/main_window_controller.py",
    # Fallback: project creator may run without a main window controller (tests / isolated contexts)
    "src/features/project_creator/controller/project_creator_controller.py",
}


def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _is_project_session_coordinator_owner(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "project_session_coordinator"
    if isinstance(node, ast.Attribute):
        # e.g. `self.project_session_coordinator` or `ctx.project_session_coordinator`
        return node.attr == "project_session_coordinator"
    return False


def test_project_session_coordinator_apply_calls_are_scoped():
    violations = []
    for file_path in _iter_python_files():
        rel = _rel_path(file_path)
        source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr != "apply_project_context":
                continue
            if not _is_project_session_coordinator_owner(func.value):
                continue

            if rel not in ALLOWED_DIRECT_COORDINATOR_APPLY_CALLERS:
                violations.append(rel)

    assert violations == [], (
        "Project-open side effects must be centralized: trigger-side should call "
        "`project_session_service.apply_project_context(...)`, and coordinator-side effects must run via "
        "`project.opened` consumption (or a controlled local fallback). "
        f"Violations: {sorted(set(violations))}"
    )


def test_handle_open_project_delegates_properly():
    """
    Guard: handle_open_project() 必须委托给 lifecycle_coordinator，而不是直接编排副作用。
    
    架构演进说明：
    - Phase 12: 直接调用 project_session_service.apply_project_context()
    - Phase 16+: 通过 lifecycle_coordinator 委托，coordinator 内部调用 apply_project_context()
    
    这确保了：
    1. MainWindowController.handle_open_project() 不直接处理 UI 对话框
    2. 所有项目打开副作用统一由 coordinator 编排
    3. 最终仍然通过 project_session_service.apply_project_context() 触发副作用
    """
    rel = "src/features/main_window/controller/main_window_controller.py"
    file_path = REPO_ROOT / rel
    source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
    tree = ast.parse(source, filename=rel)

    handle_open_project_nodes: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "handle_open_project":
            handle_open_project_nodes.append(node)

    assert len(handle_open_project_nodes) >= 1, "Could not find handle_open_project() in main_window_controller.py"

    violations = []

    for fn in handle_open_project_nodes:
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            
            # 检查禁止的模式：直接调用 _apply_project_context
            if isinstance(func, ast.Attribute) and func.attr == "_apply_project_context":
                violations.append("_apply_project_context")
                continue

            # 检查禁止的模式：直接调用 project_session_coordinator.apply_project_context
            if isinstance(func, ast.Attribute) and func.attr == "apply_project_context":
                if _is_project_session_coordinator_owner(func.value):
                    violations.append("project_session_coordinator.apply_project_context")

            # 检查禁止的模式：直接调用 project_session_service.apply_project_context
            # （应该通过 lifecycle_coordinator 委托）
            if isinstance(func, ast.Attribute) and func.attr == "apply_project_context":
                if isinstance(func.value, ast.Name) and func.value.id == "project_session_service":
                    violations.append("project_session_service.apply_project_context_directly")
            
            # 检查禁止的模式：直接调用 project_open_service
            if isinstance(func, ast.Attribute) and func.attr == "open_project":
                if isinstance(func.value, ast.Name) and func.value.id == "project_open_service":
                    violations.append("project_open_service.open_project")

    # 允许的模式：委托给 lifecycle_coordinator
    allowed_delegations = []
    for fn in handle_open_project_nodes:
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            # 允许：self.lifecycle_coordinator.handle_open_project()
            if isinstance(func, ast.Attribute) and func.attr == "handle_open_project":
                if isinstance(func.value, ast.Attribute) and func.value.attr == "lifecycle_coordinator":
                    allowed_delegations.append("lifecycle_coordinator.handle_open_project")

    assert violations == [], (
        f"handle_open_project() must delegate to lifecycle_coordinator, not call these directly: {violations}"
    )
    assert len(allowed_delegations) >= 1, (
        "handle_open_project() must delegate to self.lifecycle_coordinator.handle_open_project()"
    )

