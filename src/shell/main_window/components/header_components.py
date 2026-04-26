"""
主窗口头部组件
包含顶栏（App Header）的创建和相关事件处理

注意：组件通过 duck typing 使用 main_window 的属性，不需要导入 MainWindow 类型。
"""

from typing import Any, Optional
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QSize, QEvent
from PyQt5.QtGui import QMouseEvent, QPainter, QColor, QFont, QPaintEvent
from src.core.logger import logger


class TitleBarButton(QWidget):
    """自定义标题栏按钮 — 自绘渲染，轻量可靠"""

    clicked = pyqtSignal()

    def __init__(self, icon_text: str, hover_bg: str = "rgba(255,255,255,0.15)",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._icon = icon_text
        self._hover_bg = hover_bg
        self._hovered = False
        self._pressed = False
        self.setFixedSize(46, 32)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self) -> QSize:
        return QSize(46, 32)

    @property
    def icon(self) -> str:
        return self._icon

    @icon.setter
    def icon(self, value: str) -> None:
        if self._icon != value:
            self._icon = value
            self.update()

    # ---- 绘制 ----

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = None
        if self._pressed:
            bg = QColor("rgba(255,255,255,0.25)")
        elif self._hovered:
            bg = QColor(self._hover_bg)
        if bg:
            p.fillRect(self.rect(), bg)
        p.setPen(QColor(255, 255, 255, 230))
        font = QFont("Segoe UI Symbol", 11)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, self._icon)
        p.end()

    # ---- 事件 ----

    def enterEvent(self, event: QEvent) -> None:
        self._hovered = True
        self.update()

    def leaveEvent(self, event: QEvent) -> None:
        self._hovered = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            self.update()
            if self.rect().contains(event.pos()):
                self.clicked.emit()


class HeaderComponents:
    """主窗口头部组件管理器"""

    def __init__(self, main_window: Any):
        self.main_window = main_window

    def create_app_header(self) -> QWidget:
        """创建现代化顶栏：简洁图标 + DL编号 + 面包屑 + 快捷操作（支持拖拽和双击最大化）"""
        header = QWidget()
        header.setObjectName("LimsAppHeader")
        header.setAccessibleName("应用顶栏")
        header.setAccessibleDescription("TestFlow Manager 应用标题栏，包含窗口控制和导航信息")
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

        # 左侧：应用图标 + DL编号
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        brand_icon = QLabel()
        brand_icon.setText("🔬")
        brand_icon.setStyleSheet("font-size: 36px;")
        brand_icon.setToolTip("TestFlow Manager")
        left_layout.addWidget(brand_icon)

        # DL编号标签（初始为空）
        self.main_window._dl_number_label = QLabel("")
        self.main_window._dl_number_label.setObjectName("LimsDLNumberLabel")
        self.main_window._dl_number_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 20px;
            font-weight: bold;
            padding: 4px 12px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
        """)
        self.main_window._dl_number_label.setVisible(False)  # 初始隐藏
        left_layout.addWidget(self.main_window._dl_number_label)

        layout.addWidget(left_widget)

        # 中间面包屑
        self.main_window._breadcrumb_label = QLabel("项目管理 / Matrix 编辑器")
        self.main_window._breadcrumb_label.setObjectName("LimsBreadcrumbLabel")
        self.main_window._breadcrumb_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.main_window._breadcrumb_label, 1)

        # 右侧快捷操作区
        actions_widget = QWidget()
        actions_widget.setObjectName("LimsHeaderActions")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # 快捷按钮：最大化/还原
        self.main_window._maximize_btn = TitleBarButton("□")
        self.main_window._maximize_btn.setToolTip("最大化窗口")
        self.main_window._maximize_btn.setAccessibleName("最大化按钮")
        self.main_window._maximize_btn.setAccessibleDescription("双击顶栏或点击此按钮可最大化/还原窗口")
        self.main_window._maximize_btn.clicked.connect(lambda: QTimer.singleShot(0, self.main_window._toggle_maximize))

        # 快捷按钮：关闭（hover 时红色背景）
        close_btn = TitleBarButton("✕", hover_bg="rgba(232, 17, 35, 0.9)")
        close_btn.setToolTip("关闭应用")
        close_btn.setAccessibleName("关闭按钮")
        close_btn.setAccessibleDescription("点击关闭 TestFlow Manager 主窗口")
        close_btn.clicked.connect(self.main_window.close)

        # 右侧快捷操作区（─ □ ✕）
        minimize_btn = TitleBarButton("─")
        minimize_btn.setToolTip("最小化窗口")
        minimize_btn.setAccessibleName("最小化按钮")
        minimize_btn.setAccessibleDescription("点击最小化窗口到任务栏")
        minimize_btn.clicked.connect(lambda: QTimer.singleShot(0, self.main_window.showMinimized))
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
