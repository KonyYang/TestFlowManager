# src/core/font_utils.py
"""
字体工具类
提供基于 DPI 的动态字体大小计算
"""

from PyQt5.QtGui import QFont, QGuiApplication
from src.core.logger import logger


class FontUtils:
    """
    字体工具类
    提供基于 DPI 的动态字体大小计算
    """

    @staticmethod
    def get_scaled_font(base_size):
        """
        根据 DPI 获取缩放后的字体

        Args:
            base_size: 基础字体大小

        Returns:
            缩放后的字体
        """
        # 获取当前屏幕的 DPI
        screen = QGuiApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch() if screen else 96
        # 移除DPI调试信息，仅在需要时启用
        # logger.debug(f"Screen DPI: {dpi}")
        if dpi <= 0:
            dpi = 96  # 默认 DPI

        # 计算缩放因子 (以96为基准DPI)
        # 使用更合理的缩放因子，避免在高DPI下界面元素过大
        scale_factor = min(dpi / 96.0, 1.5) * 0.7  # 限制最大缩放并进一步减小
        scaled_size = int(base_size * scale_factor)
        # 移除缩放调试信息，仅在需要时启用
        # logger.debug(f"Scaling factor: {scale_factor}, base: {base_size}, scaled: {scaled_size}")

        font = QFont()
        font.setPointSize(scaled_size)
        return font

    @staticmethod
    def get_scaled_window_size(base_width, base_height):
        """
        根据 DPI 获取缩放后的窗口尺寸

        Args:
            base_width: 基础窗口宽度
            base_height: 基础窗口高度

        Returns:
            (宽度, 高度)的元组
        """
        # 获取当前屏幕的 DPI
        screen = QGuiApplication.primaryScreen()
        dpi = screen.logicalDotsPerInch() if screen else 96
        # 移除DPI调试信息，仅在需要时启用
        # logger.debug(f"Screen DPI for window size: {dpi}")
        if dpi <= 0:
            dpi = 96  # 默认 DPI

        # 计算缩放因子 (以96为基准DPI)
        # 使用更合理的缩放因子，避免在高DPI下界面元素过大
        scale_factor = min(dpi / 96.0, 1.5) * 0.7  # 限制最大缩放并进一步减小
        # 移除缩放调试信息，仅在需要时启用
        # logger.debug(f"Window scaling factor: {scale_factor}")

        scaled_width = int(base_width * scale_factor)
        scaled_height = int(base_height * scale_factor)
        
        # 移除窗口尺寸调试信息，仅在需要时启用
        # logger.debug(f"Base window size: {base_width}x{base_height}, Scaled: {scaled_width}x{scaled_height}")

        return scaled_width, scaled_height