from __future__ import annotations

from PyQt5.QtWidgets import QWidget

from src.shell.main_window.view.main_window_ui import MainWindow
from src.features.matrix.workspace.matrix_workspace_facade import MatrixWorkspaceFacade
from src.shell.main_window.coordinator.project_session_coordinator import ProjectSessionCoordinator
from src.app.composition.project_session_application_service import ProjectSessionApplicationService


def assemble_main_window(splash_screen=None) -> MainWindow:
    """
    Composition root for MainWindow.

    通过 MatrixWorkspaceFacade 统一注入所有 Matrix session 依赖，
    通过 ProjectSessionCoordinator 在组装点统一注入项目会话协调依赖，
    通过 ProjectSessionApplicationService 编排会话主入口 (S1-2)。
    """
    facade = MatrixWorkspaceFacade(parent_view=None)

    # =========================================================================
    # Phase 4 + S1-2: 在组装点创建项目会话组件并编排
    # =========================================================================
    project_session_coordinator = ProjectSessionCoordinator(
        view=None,  # 将在 MainWindowController 中更新
        matrix_project_controller=None,  # 将在 MainWindowController 中更新
        status_updater=None,  # 将在 MainWindowController 中设置
    )

    # S1-2: 创建应用层编排器，绑定 coordinator（coordinator 引用后续由 Controller 更新）
    project_session_app_service = ProjectSessionApplicationService(
        coordinator=project_session_coordinator,
    )

    main_window = MainWindow(
        splash_screen,
        matrix_workspace_facade=facade,
        project_session_coordinator=project_session_coordinator,
        project_session_app_service=project_session_app_service,
    )

    # Phase 4: 更新协调器引用（view 和 matrix_project_controller）
    # 由于 MainWindow 已创建，可以安全设置 view 引用
    project_session_coordinator.view = main_window

    return main_window
