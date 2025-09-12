"""
LTR管理器视图模块
包含LTR编辑器的视图组件
"""

# 导入主要的视图组件
from .ltr_editor_dialog import LTREditorDialog

# 导入子模块
from . import components

__all__ = ['LTREditorDialog', 'components']
