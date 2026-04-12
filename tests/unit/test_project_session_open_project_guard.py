import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


ALLOWED_PROJECT_SESSION_SERVICE_OPEN_PROJECT_CALLERS = {
    # The legacy helper lives here; call sites must prefer `apply_project_context(...)`.
    "src/core/project_session_service.py",
}


def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_project_session_service_open_project_is_not_used_in_src():
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
            if func.attr != "open_project":
                continue
            owner = func.value
            if not isinstance(owner, ast.Name):
                continue
            if owner.id != "project_session_service":
                continue

            if rel not in ALLOWED_PROJECT_SESSION_SERVICE_OPEN_PROJECT_CALLERS:
                violations.append(rel)

    assert violations == [], (
        "Do not call project_session_service.open_project(...) from src; use "
        "ProjectContext.from_project_path(...) + project_session_service.apply_project_context(...) instead. "
        f"Violations: {sorted(set(violations))}"
    )

