"""
主窗口侧边栏组件
包含侧边栏（Sidebar）的创建和导航列表管理

注意：组件通过 duck typing 使用 main_window 的属性，不需要导入 MainWindow 类型。
"""

import os
from typing import Any
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QFrame
from PyQt5.QtCore import Qt


class SidebarComponents:
    """主窗口侧边栏组件管理器"""

    def __init__(self, main_window: Any):
        self.main_window = main_window
        
    def create_sidebar(self) -> QWidget:
        """创建现代化侧边栏：分组导航"""
        side = QWidget()
        side.setObjectName("LimsSidebar")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(0)

        # 导航列表
        self.main_window._nav_list = QListWidget()
        self.main_window._nav_list.setObjectName("LimsNavList")
        self.main_window._nav_list.setFrameShape(QFrame.NoFrame)
        self.main_window._nav_list.setSpacing(4)
        # 注意：导航事件由 NavigationManager 处理，无需在此连接信号
        
        # 导航分组容器
        nav_container = QWidget()
        nav_container_layout = QVBoxLayout(nav_container)
        nav_container_layout.setContentsMargins(0, 8, 0, 0)
        nav_container_layout.setSpacing(0)

        # 分组1: 项目管理
        sec1 = QLabel("📁 项目管理")
        sec1.setObjectName("LimsSidebarSection")
        nav_container_layout.addWidget(sec1)
        nav_container_layout.addWidget(self.main_window._nav_list, 1)
        
        # 占位分组标签（将在 _setup_navigation_pages 中填充）
        self.main_window._sidebar_sections = {}
        
        # 分隔线和更多分组（预留位置给动态导航项）
        separator = self._create_separator()
        nav_container_layout.addWidget(separator)

        # 底部版本信息
        version_label = self._create_version_label()
        nav_container_layout.addWidget(version_label)
        
        layout.addWidget(nav_container, 1)
        return side
        

    def _create_separator(self) -> QWidget:
        """创建分隔线"""
        separator = QWidget()
        separator.setStyleSheet("""
            background: rgba(255, 255, 255, 0.1);
            min-height: 1px;
            margin: 12px 16px;
        """)
        return separator
        
    def _create_version_label(self) -> QLabel:
        """创建版本标签"""
        try:
            import src
            version_text = f"v{src.__version__}"
        except Exception:
            version_text = "v1.0.0"
        
        version_label = QLabel(version_text)
        version_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.5);
            font-size: 15px;
            padding: 10px 24px;
        """)
        return version_label
