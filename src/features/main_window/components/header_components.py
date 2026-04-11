"""
主窗口头部组件
包含顶栏（App Header）的创建和相关事件处理
"""

from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QMouseEvent
from src.core.logger import logger

if TYPE_CHECKING:
    from src.features.main_window.view.main_window_ui import MainWindow


class HeaderComponents:
    """主窗口头部组件管理器"""
    
    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
        
    def create_app_header(self) -> QWidget:
        """创建现代化顶栏：简洁图标 + 面包屑 + 快捷操作（支持拖拽和双击最大化）"""
        header = QWidget()
        header.setObjectName("LimsAppHeader")
        header.setMouseTracking(True)
        # 设置顶栏为可拖拽区域
        header.mousePressEvent = self._on_header_mouse_press
        header.mouseMoveEvent = self._on_header_mouse_move
        header.mouseReleaseEvent = self._on_header_mouse_release
        header.mouseDoubleClickEvent = self._on_header_double_click
        self.main_window._header_drag_start_pos: QPoint = None
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(16)

        # 左侧：简洁应用图标
        brand_icon = QLabel()
        brand_icon.setText("🔬")
        brand_icon.setStyleSheet("font-size: 36px;")
        brand_icon.setToolTip("TestFlow Manager")
        layout.addWidget(brand_icon)

        # 中间面包屑
        self.main_window._breadcrumb_label = QLabel("📁 项目管理 / Matrix 编辑器")
        self.main_window._breadcrumb_label.setObjectName("LimsBreadcrumbLabel")
        self.main_window._breadcrumb_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.main_window._breadcrumb_label, 1)

        # 右侧快捷操作区
        actions_widget = QWidget()
        actions_widget.setObjectName("LimsHeaderActions")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # 快捷按钮：全屏切换
        fullscreen_btn = QToolButton()
        fullscreen_btn.setObjectName("LimsHeaderMenuButton")
        fullscreen_btn.setText("⛶")
        fullscreen_btn.setToolTip("切换全屏模式 (F11)")
        fullscreen_btn.clicked.connect(self.main_window._toggle_fullscreen)
        
        # 快捷按钮：最小化
        minimize_btn = QToolButton()
        minimize_btn.setObjectName("LimsHeaderMenuButton")
        minimize_btn.setText("─")
        minimize_btn.setToolTip("最小化窗口")
        minimize_btn.clicked.connect(self.main_window.showMinimized)
        
        # 快捷按钮：最大化
        self.main_window._maximize_btn = QToolButton()
        self.main_window._maximize_btn.setObjectName("LimsHeaderMenuButton")
        self.main_window._maximize_btn.setText("□")
        self.main_window._maximize_btn.setToolTip("最大化窗口")
        self.main_window._maximize_btn.clicked.connect(self.main_window._toggle_maximize)
        
        # 快捷按钮：关闭
        close_btn = QToolButton()
        close_btn.setObjectName("LimsHeaderMenuButton")
        close_btn.setText("✕")
        close_btn.setToolTip("关闭应用")
        close_btn.clicked.connect(self.main_window.close)
        
        # 右侧快捷操作区
        actions_layout.addWidget(fullscreen_btn)
        actions_layout.addWidget(minimize_btn)
        actions_layout.addWidget(self.main_window._maximize_btn)
        actions_layout.addWidget(close_btn)
        layout.addWidget(actions_widget)
        
        return header
    
    def _on_header_mouse_press(self, event: QMouseEvent):
        """鼠标按下：开始拖拽"""
        if event.button() == Qt.LeftButton:
            self.main_window._header_drag_start_pos = event.globalPos()
            self.main_window._header_drag_started = True

    def _on_header_mouse_move(self, event: QMouseEvent):
        """鼠标移动：拖拽窗口"""
        if hasattr(self.main_window, '_header_drag_started') and self.main_window._header_drag_started and self.main_window._header_drag_start_pos:
            if event.buttons() & Qt.LeftButton:
                delta = event.globalPos() - self.main_window._header_drag_start_pos
                self.main_window.move(self.main_window.pos() + delta)
                self.main_window._header_drag_start_pos = event.globalPos()

    def _on_header_mouse_release(self, event: QMouseEvent):
        """鼠标释放：结束拖拽"""
        if event.button() == Qt.LeftButton:
            self.main_window._header_drag_start_pos = None
            self.main_window._header_drag_started = False

    def _on_header_double_click(self, event: QMouseEvent):
        """双击顶栏：切换最大化"""
        if event.button() == Qt.LeftButton:
            self.main_window._toggle_maximize()
