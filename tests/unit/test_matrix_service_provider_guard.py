from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def _rel_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_no_matrix_service_provider_references():
    violations = []
    for path in _iter_python_files():
        rel = _rel_path(path)
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        if "MatrixServiceProvider" in text:
            violations.append(rel)
    assert violations == [], (
        "MatrixServiceProvider is retired. Stop reintroducing it."
        f" Violations: {sorted(set(violations))}"
    )
