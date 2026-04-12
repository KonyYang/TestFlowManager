import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


ALLOWED_MATRIX_CONTROLLER_CALL_SITES = {
    "src/features/matrix/service/matrix_session_factory.py",
}

ALLOWED_MATRIX_PROJECT_CONTROLLER_CALL_SITES = {
    "src/features/matrix/service/matrix_session_factory.py",
}


def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _is_name_call(node: ast.Call, name: str) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == name
    if isinstance(func, ast.Attribute):
        return func.attr == name
    return False


def _has_keyword(node: ast.Call, keyword: str) -> bool:
    for kw in node.keywords:
        if kw.arg == keyword:
            return True
    return False


def test_matrix_controller_construction_is_scoped_to_session_factory():
    violations = []
    for file_path in _iter_python_files():
        rel = _rel_path(file_path)
        source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_name_call(node, "MatrixController"):
                continue
            if rel not in ALLOWED_MATRIX_CONTROLLER_CALL_SITES:
                violations.append(rel)
                continue
            if not _has_keyword(node, "matrix_service"):
                violations.append(rel)

    assert violations == [], (
        "MatrixController construction should be scoped to MatrixSessionFactory and "
        "must pass explicit matrix_service injection. "
        f"Violations: {sorted(set(violations))}"
    )


def test_matrix_project_controller_construction_is_scoped_to_session_factory():
    violations = []
    for file_path in _iter_python_files():
        rel = _rel_path(file_path)
        source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_name_call(node, "MatrixProjectController"):
                continue
            if rel not in ALLOWED_MATRIX_PROJECT_CONTROLLER_CALL_SITES:
                violations.append(rel)
                continue
            if not _has_keyword(node, "matrix_controller"):
                violations.append(rel)

    assert violations == [], (
        "MatrixProjectController construction should be scoped to MatrixSessionFactory and "
        "must pass explicit matrix_controller injection. "
        f"Violations: {sorted(set(violations))}"
    )

