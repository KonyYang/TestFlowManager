"""
基础控制器模块
提供通用控制器功能
"""

from PyQt5.QtWidgets import QMessageBox
from src.core.logger import logger


class BaseController:
    """
    基础控制器类
    提供通用控制器功能，如错误处理、日志记录等
    """

    def __init__(self, view=None):
        """
        初始化基础控制器

        Args:
            view: 关联的视图实例
        """
        self.view = view

    def handle_error(self, error, message="操作失败"):
        """
        统一错误处理方法

        Args:
            error: 异常对象
            message: 错误消息
        """
        logger.error(f"{message}: {error}")
        if self.view:
            QMessageBox.critical(self.view, "错误", f"{message}: {str(error)}")
        return False

    def handle_success(self, message):
        """
        统一成功处理方法

        Args:
            message: 成功消息
        """
        logger.info(message)
        if self.view:
            QMessageBox.information(self.view, "成功", message)
        return True
