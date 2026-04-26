# src/shell/main_window/components/layout_builder.py
"""
主窗口布局构建器模块
负责组装 Lims 风格的 UI 布局结构，实现布局逻辑与主窗口的解耦
"""
from typing import Dict, Any

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFrame,
    QLabel,
    QSizePolicy,
)


class MainWindowLayoutBuilder:
    """
    主窗口布局构建器 - 负责组装 Lims 风格的 UI 结构
    
    职责：
    - 统一管理主窗口的布局组装逻辑
    - 隔离布局结构与主窗口实现细节
    - 提供可复用的布局构建方法
    - 返回所有需要引用的组件字典
    """

    @staticmethod
    def build_main_layout(
        header_widget: QWidget,
        sidebar_widget: QWidget,
        page_stack: QStackedWidget,
    ) -> tuple[QWidget, Dict[str, Any]]:
        """
        构建主窗口完整布局
        
        Args:
            header_widget: 顶栏组件（由 HeaderComponents 创建）
            sidebar_widget: 侧栏组件（由 SidebarComponents 创建）
            page_stack: 页面堆叠容器
            
        Returns:
            (central_widget, component_refs)
            - central_widget: 中央部件，可直接设置为 QMainWindow 的 CentralWidget
            - component_refs: 组件引用字典，包含所有需要在主窗口中访问的组件
        """
        # === 创建根容器 ===
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # 添加顶栏
        root_layout.addWidget(header_widget)
        
        # === 创建主体区域 ===
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        
        # 添加侧栏
        body_layout.addWidget(sidebar_widget)
        
        # 创建主内容列
        main_column = MainWindowLayoutBuilder._build_main_column(page_stack)
        body_layout.addWidget(main_column, 1)
        
        root_layout.addWidget(body, 1)
        
        # === 返回组件引用 ===
        component_refs = {
            'main_column': main_column,
        }
        
        return root, component_refs

    @staticmethod
    def _build_main_column(page_stack: QStackedWidget) -> QWidget:
        """
        构建主内容列（包含标题区和页面区）
        
        Args:
            page_stack: 页面堆叠容器
            
        Returns:
            main_column: 主内容列组件
        """
        main_column = QWidget()
        main_column.setObjectName("LimsMainColumn")
        main_column.setAccessibleName("主内容区")
        main_column.setAccessibleDescription("TestFlow Manager 主内容显示区域")
        main_layout = QVBoxLayout(main_column)
        main_layout.setContentsMargins(24, 24, 24, 16)
        main_layout.setSpacing(0)
        
        # 标题区域
        title_widget, page_title_label, page_subtitle_label = \
            MainWindowLayoutBuilder._build_title_area()
        main_layout.addWidget(title_widget)
        
        # 页面纸张容器
        paper = MainWindowLayoutBuilder._build_paper_container(page_stack)
        main_layout.addWidget(paper, 1)
        
        # 将标签也加入引用字典（通过闭包返回）
        main_column._page_title_label = page_title_label
        main_column._page_subtitle_label = page_subtitle_label
        
        return main_column

    @staticmethod
    def _build_title_area() -> tuple[QWidget, QLabel, QLabel]:
        """
        构建标题区域
        
        Returns:
            (title_widget, page_title_label, page_subtitle_label)
        """
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 16)
        title_layout.setSpacing(4)
        
        page_title_label = QLabel("")
        page_title_label.setObjectName("LimsPageTitle")
        
        page_subtitle_label = QLabel("")
        page_subtitle_label.setObjectName("LimsPageSubtitle")
        page_subtitle_label.setStyleSheet("""
            color: #718096;
            font-size: 18px;
            padding-left: 6px;
        """)
        
        title_layout.addWidget(page_title_label)
        title_layout.addWidget(page_subtitle_label)
        
        return title_widget, page_title_label, page_subtitle_label

    @staticmethod
    def _build_paper_container(page_stack: QStackedWidget) -> QFrame:
        """
        构建页面纸张容器
        
        Args:
            page_stack: 页面堆叠容器
            
        Returns:
            paper: 纸张容器组件
        """
        paper = QFrame()
        paper.setObjectName("LimsPagePaper")
        # 样式已在 LIMS_APP_STYLESHEET 中定义，无需内联
        
        paper_layout = QVBoxLayout(paper)
        paper_layout.setContentsMargins(16, 16, 16, 16)
        paper_layout.addWidget(page_stack, 1)
        
        return paper
