
# src/core/window_utils.py
"""
窗口工具类
提供基于 DPI 的动态窗口大小计算
"""

from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtGui import QGuiApplication
from src.core.logger import logger


class WindowUtils:
    """
    窗口工具类
    提供基于 DPI 的动态窗口大小计算
    """

    @staticmethod
    def get_scaled_size(base_size):
        """
        根据 DPI 获取缩放后的尺寸

        Args:
            base_size: 基础尺寸

        Returns:
            缩放后的尺寸
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

        return scaled_size

    @staticmethod
    def get_scaled_window_size(base_width, base_height):
        """
        根据 DPI 获取缩放后的窗口尺寸

        Args:
            base_width: 基础窗口宽度
            base_height: 基础窗口高度

        Returns:
            tuple: (缩放后的宽度, 缩放后的高度)
        """
        scaled_width = WindowUtils.get_scaled_size(base_width)
        scaled_height = WindowUtils.get_scaled_size(base_height)
        return scaled_width, scaled_height

    @staticmethod
    def get_screen_geometry():
        """
        获取屏幕可用几何尺寸

        Returns:
            tuple: (屏幕宽度, 屏幕高度)
        """
        desktop = QDesktopWidget().availableGeometry()
        return desktop.width(), desktop.height()

    @staticmethod
    def get_scaled_screen_geometry(scale_factor=0.6):
        """
        获取屏幕缩放后的几何尺寸

        Args:
            scale_factor: 缩放因子，默认为0.6（60%）

        Returns:
            tuple: (缩放后的宽度, 缩放后的高度)
        """
        screen_width, screen_height = WindowUtils.get_screen_geometry()
        scaled_width = int(screen_width * scale_factor)
        scaled_height = int(screen_height * scale_factor)
        return scaled_width, scaled_height