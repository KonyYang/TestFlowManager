"""
窗口行为管理器
处理拖拽、缩放、全屏切换等无边框窗口行为

从 main_window_ui.py 中抽取，作为独立组件。
"""
import os
import ctypes
import ctypes.wintypes
from typing import Optional

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication

from src.core.logger import logger


class WindowChromeManager:
    """窗口行为管理器 - 处理无边框窗口的拖拽、缩放、全屏等行为"""

    def __init__(self, window):
        """
        初始化窗口行为管理器

        Args:
            window: 父窗口对象（必须是 QWidget 子类）
        """
        self._window = window
        self._drag_start_pos: Optional[QPoint] = None
        self._resize_border_width: int = 8

    @property
    def resize_border_width(self) -> int:
        """获取边框宽度"""
        return self._resize_border_width

    @resize_border_width.setter
    def resize_border_width(self, width: int) -> None:
        """设置边框宽度"""
        self._resize_border_width = width

    def handle_mouse_press(self, event: QMouseEvent) -> None:
        """处理鼠标按下事件 - 开始拖拽"""
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.globalPos()

    def handle_mouse_move(self, event: QMouseEvent) -> None:
        """处理鼠标移动事件 - 拖拽窗口"""
        if self._drag_start_pos is not None:
            if event.buttons() & Qt.LeftButton:
                delta = event.globalPos() - self._drag_start_pos
                self._window.move(self._window.pos() + delta)
                self._drag_start_pos = event.globalPos()

    def handle_mouse_release(self, event: QMouseEvent) -> None:
        """处理鼠标释放事件 - 结束拖拽"""
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = None

    def handle_double_click(self, event: QMouseEvent) -> None:
        """处理双击事件 - 切换最大化"""
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()

    def _toggle_maximize(self) -> None:
        """切换最大化状态"""
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def toggle_fullscreen(self) -> None:
        """切换全屏模式"""
        if self._window.isFullScreen():
            self._window.showMaximized()
        else:
            self._window.showFullScreen()

    def native_event(self, event_type, message) -> tuple:
        """
        处理 Windows 原生事件，实现边缘缩放

        Args:
            event_type: 事件类型
            message: 消息指针

        Returns:
            (handled, result) 元组
        """
        if (
            os.name != "nt"
            or self._window.isMaximized()
            or self._window.isFullScreen()
            or event_type != "windows_generic_MSG"
        ):
            return False, None

        msg = ctypes.wintypes.MSG.from_address(int(message))
        WM_NCHITTEST = 0x0084
        if msg.message != WM_NCHITTEST:
            return False, None

        # 定义窗口缩放区域常量
        HTLEFT = 10
        HTRIGHT = 11
        HTTOP = 12
        HTTOPLEFT = 13
        HTTOPRIGHT = 14
        HTBOTTOM = 15
        HTBOTTOMLEFT = 16
        HTBOTTOMRIGHT = 17

        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
        pos = self._window.mapFromGlobal(QPoint(x, y))
        rect = self._window.rect()
        border = self._resize_border_width

        on_left = pos.x() <= border
        on_right = pos.x() >= rect.width() - border
        on_top = pos.y() <= border
        on_bottom = pos.y() >= rect.height() - border

        if on_top and on_left:
            return True, HTTOPLEFT
        if on_top and on_right:
            return True, HTTOPRIGHT
        if on_bottom and on_left:
            return True, HTBOTTOMLEFT
        if on_bottom and on_right:
            return True, HTBOTTOMRIGHT
        if on_left:
            return True, HTLEFT
        if on_right:
            return True, HTRIGHT
        if on_top:
            return True, HTTOP
        if on_bottom:
            return True, HTBOTTOM

        return False, None

    def show_normal(self) -> None:
        """
        显示正常大小窗口
        如果当前是最大化状态，先保存几何信息再切换
        """
        if self._window.isMaximized():
            self._window.is_custom_sized = True
        if not self._window.custom_geometry:
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            width = int(screen_geometry.width() * 0.3)
            height = int(screen_geometry.height() * 0.3)
            x = (screen_geometry.width() - width) // 2
            y = (screen_geometry.height() - height) // 2
            self._window.custom_geometry = QApplication.primaryScreen().geometry().normalized()
            self._window.showNormal()
            self._window.setGeometry(self._window.custom_geometry)  # type: ignore
        else:
            self._window.showNormal()

    def show_maximized(self) -> None:
        """显示最大化窗口"""
        self._window.is_custom_sized = False
        self._window.showMaximized()

    def show_minimized(self) -> None:
        """显示最小化窗口"""
        self._window.is_custom_sized = False
        self._window.showMinimized()

    def handle_window_state_change(self, event) -> None:
        """处理窗口状态变化事件"""
        if event.type() == event.WindowStateChange:
            if self._window.isMaximized() and self._window.is_custom_sized:
                self._window.is_custom_sized = False
