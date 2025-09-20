# src/core/font_utils.py
from PyQt5.QtGui import QFont, QFontDatabase, QGuiApplication
from PyQt5.QtCore import Qt


class FontUtils:
    """
    字体工具类
    提供基于 DPI 的动态字体大小计算
    """

    @staticmethod
    def get_scaled_font(base_size=9):
        """
        根据 DPI 获取缩放后的字体

        Args:
            base_size: 基础字号（默认9pt）

        Returns:
            QFont: 缩放后的字体对象
        """
        # 获取当前屏幕的 DPI
        screen = QGuiApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch() if screen else 96
        if dpi <= 0:
            dpi = 96  # 默认 DPI

        # 计算缩放因子 (以96为基准DPI)
        scale_factor = dpi / 96.0
        scaled_size = max(int(base_size * scale_factor), 1)  # 确保字体大小至少为1

        font = QFont()
        font.setPointSize(scaled_size)
        return font

    @staticmethod
    def get_system_font():
        """获取系统默认字体"""
        return QFontDatabase.systemFont(QFontDatabase.DefaultFont)

    @staticmethod
    def get_monospace_font():
        """获取等宽字体"""
        return QFontDatabase.systemFont(QFontDatabase.MonospaceFont)
