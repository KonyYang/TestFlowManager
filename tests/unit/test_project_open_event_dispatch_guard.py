import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


ALLOWED_PROJECT_OPENED_DISPATCHERS = {
    "src/core/project_session_service.py",
}


def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_project_opened_event_is_dispatched_only_by_project_session_service():
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
            if func.attr != "dispatch":
                continue
            owner = func.value
            if not isinstance(owner, ast.Name):
                continue
            if owner.id != "event_dispatcher":
                continue

            if not node.args:
                continue
            first_arg = node.args[0]
            if not isinstance(first_arg, ast.Constant):
                continue
            if first_arg.value != "project.opened":
                continue

            if rel not in ALLOWED_PROJECT_OPENED_DISPATCHERS:
                violations.append(rel)

    assert violations == [], (
        "Do not dispatch 'project.opened' directly from src; use "
        "project_session_service.apply_project_context(...) as the single trigger. "
        f"Violations: {sorted(set(violations))}"
    )

