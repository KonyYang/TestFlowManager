import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


ALLOWED_PROJECT_TITLE_SETTERS = {
    "src/core/project_session_coordinator.py",
}


def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_project_title_update_is_scoped_to_project_session_coordinator():
    """Guard: the main-window project title must be set by the coordinator only."""
    violations = []
    for file_path in _iter_python_files():
        rel = _rel_path(file_path)
        source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        if "TestFlow Manager - 项目:" not in source:
            continue
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr != "setWindowTitle":
                continue
            if not node.args:
                continue
            # We keep this guard intentionally narrow: only the canonical project title pattern.
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if "TestFlow Manager - 项目:" in arg.value:
                    if rel not in ALLOWED_PROJECT_TITLE_SETTERS:
                        violations.append(rel)
            elif isinstance(arg, ast.JoinedStr):
                for value in arg.values:
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        if "TestFlow Manager - 项目:" in value.value:
                            if rel not in ALLOWED_PROJECT_TITLE_SETTERS:
                                violations.append(rel)
                                break

    assert violations == [], (
        "Project title updates must be centralized in ProjectSessionCoordinator.apply_project_context(...). "
        f"Violations: {sorted(set(violations))}"
    )

