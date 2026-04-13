from __future__ import annotations

from src.features.main_window.view.main_window_ui import MainWindow
from src.features.main_window.facade.matrix_workspace_facade import MatrixWorkspaceFacade


def assemble_main_window(splash_screen=None) -> MainWindow:
    """
    Composition root for MainWindow.

    通过 MatrixWorkspaceFacade 统一注入所有 Matrix session 依赖，
    消除 MainWindow / Controller 的 7 参数爆炸。
    """
    facade = MatrixWorkspaceFacade(parent_view=None)

    return MainWindow(
        splash_screen,
        matrix_workspace_facade=facade,
    )
