from __future__ import annotations

from PyQt5.QtWidgets import QWidget

from src.shell.main_window.view.main_window_ui import MainWindow
from src.features.matrix.workspace.matrix_workspace_facade import MatrixWorkspaceFacade
from src.shell.main_window.coordinator.project_session_coordinator import ProjectSessionCoordinator


def assemble_main_window(splash_screen=None) -> MainWindow:
    """
    Composition root for MainWindow.

    通过 MatrixWorkspaceFacade 统一注入所有 Matrix session 依赖，
    通过 ProjectSessionCoordinator 在组装点统一注入项目会话协调依赖，
    消除 MainWindow / Controller 的参数爆炸。
    """
    facade = MatrixWorkspaceFacade(parent_view=None)

    # =========================================================================
    # Phase 4: 在组装点创建 ProjectSessionCoordinator
    # =========================================================================
    # 注意：这里传递 facade.assemble_shared_session() 返回的 controller，
    # 但由于 MainWindow 尚未初始化完成，实际的 matrix_project_controller
    # 需要在 MainWindowController 初始化后通过引用更新。
    #
    # 为保持简单，我们在这里创建协调器，但让 matrix_project_controller=None，
    # 然后在 MainWindowController 中更新引用。
    #
    # 更好的方案是使用依赖注入容器或工厂模式，但为了最小化改动，
    # 采用向后兼容的引用更新方案。
    # =========================================================================
    project_session_coordinator = ProjectSessionCoordinator(
        view=None,  # 将在 MainWindowController 中更新
        matrix_project_controller=None,  # 将在 MainWindowController 中更新
        status_updater=None,  # 将在 MainWindowController 中设置
    )

    main_window = MainWindow(
        splash_screen,
        matrix_workspace_facade=facade,
        project_session_coordinator=project_session_coordinator,
    )

    # Phase 4: 更新协调器引用（view 和 matrix_project_controller）
    # 由于 MainWindow 已创建，可以安全设置 view 引用
    project_session_coordinator.view = main_window

    return main_window
