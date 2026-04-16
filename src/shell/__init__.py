"""
Shell 模块 - 应用外壳层

提供主窗口 UI、导航路由、事件绑定等 Shell 级功能。
与 features/ 下的业务功能模块平级。
"""

from src.shell.main_window.controller.main_window_controller import MainWindowController

__all__ = ["MainWindowController"]
