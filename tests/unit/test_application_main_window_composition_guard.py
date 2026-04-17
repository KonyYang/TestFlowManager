from pathlib import Path


def test_application_create_main_window_uses_composition_assembler():
    """
    Guard: keep MainWindow dependency assembly out of UI layer by routing through
    app composition in create_main_window().
    """
    source_path = (
        Path(__file__).resolve().parents[2] / "src" / "app" / "application.py"
    )
    source = source_path.read_text(encoding="utf-8")

    assert "from src.app.composition.main_window_assembler import assemble_main_window" in source
    assert "from src.shell.main_window.view.main_window_ui import MainWindow" not in source
    assert "MainWindow(" not in source
    assert "assemble_main_window(" in source

