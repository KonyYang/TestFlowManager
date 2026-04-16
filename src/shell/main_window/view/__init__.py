"""
MainWindow View 子模块
提供主窗口相关的 UI 组件

注意: 业务对话框已迁移至各自功能模块:
- LTR相关对话框: src.features.ltr_manager.view
- 项目信息对话框: src.features.project_creator.view
"""
from src.shell.main_window.view.window_chrome_manager import WindowChromeManager

__all__ = [
    'WindowChromeManager',
]
