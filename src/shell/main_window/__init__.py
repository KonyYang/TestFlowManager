"""
主窗口模块初始化文件
"""

# 导入主要的类，方便其他模块使用
from .controller.main_window_controller import MainWindowController
from .view.main_window_ui import MainWindow

__all__ = ['MainWindowController', 'MainWindow']
