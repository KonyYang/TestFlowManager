import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


ALLOWED_DIRECT_MATRIX_SERVICE_IMPORTS = {
    "src/features/matrix/service/matrix_session_registry.py",
}



def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_direct_matrix_service_imports_are_scoped():
    violations = []
    for file_path in _iter_python_files():
        rel = _rel_path(file_path)
        source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "src.features.matrix.service.matrix_service":
                continue
            imported_names = {alias.name for alias in node.names}
            if "MatrixService" not in imported_names:
                continue
            if rel not in ALLOWED_DIRECT_MATRIX_SERVICE_IMPORTS:
                violations.append(rel)

    assert violations == [], (
        "Direct MatrixService imports should be scoped to registry only. "
        f"Violations: {sorted(set(violations))}"
    )


def test_matrix_service_provider_get_service_calls_are_not_allowed():
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
            if func.attr != "get_service":
                continue
            owner = func.value
            if not isinstance(owner, ast.Name):
                continue
            if owner.id != "MatrixServiceProvider":
                continue
            violations.append(rel)

    assert violations == [], (
        "MatrixServiceProvider.get_service() should not be called from src. "
        f"Violations: {sorted(set(violations))}"
    )


def test_matrix_service_provider_switch_calls_are_scoped_to_registry():
    violations = []
    switch_methods = {
        "set_provider",
        "reset_provider",
        "set_service_factory",
        "reset_service_factory",
    }
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
            if func.attr not in switch_methods:
                continue
            owner = func.value
            if not isinstance(owner, ast.Name):
                continue
            if owner.id != "MatrixServiceProvider":
                continue
            violations.append(rel)

    assert violations == [], (
        "MatrixServiceProvider switch calls should not exist under src. "
        f"Violations: {sorted(set(violations))}"
    )


def test_matrix_session_registry_install_uninstall_are_not_used_in_src():
    violations = []
    for file_path in _iter_python_files():
        rel = _rel_path(file_path)
        source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(source, filename=rel)

        imports_registry = False
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "src.features.matrix.service.matrix_session_registry":
                continue
            imported_names = {alias.name for alias in node.names}
            if "MatrixSessionRegistry" in imported_names:
                imports_registry = True
                break

        if not imports_registry:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in {"install", "uninstall"}:
                continue
            violations.append(rel)

    assert violations == [], (
        "MatrixSessionRegistry.install()/uninstall() should not be called from src. "
        "Provider switching must remain a registry-internal capability. "
        f"Violations: {sorted(set(violations))}"
    )


def test_matrix_service_provider_module_is_not_imported_in_src():
    violations = []
    for file_path in _iter_python_files():
        rel = _rel_path(file_path)
        source = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(source, filename=rel)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "src.features.matrix.service.matrix_service_provider":
                    violations.append(rel)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "src.features.matrix.service.matrix_service_provider":
                        violations.append(rel)

    assert violations == [], (
        "matrix_service_provider has been removed and must not be (re)introduced or imported from src. "
        f"Violations: {sorted(set(violations))}"
    )
