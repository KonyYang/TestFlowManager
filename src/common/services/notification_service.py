"""
通知服务模块
提供应用程序通知功能
"""

from PyQt5.QtWidgets import QMessageBox
from typing import Optional
from src.core.logger import logger


class NotificationService:
    """
    通知服务类
    提供各种类型的通知功能
    """

    @staticmethod
    def show_info(parent, title: str, message: str) -> None:
        """
        显示信息通知

        Args:
            parent: 父窗口
            title: 通知标题
            message: 通知内容
        """
        try:
            QMessageBox.information(parent, title, message)
            logger.debug(f"Info notification shown: {title}")
        except Exception as e:
            logger.error(f"Failed to show info notification: {e}")

    @staticmethod
    def show_warning(parent, title: str, message: str) -> None:
        """
        显示警告通知

        Args:
            parent: 父窗口
            title: 通知标题
            message: 通知内容
        """
        try:
            QMessageBox.warning(parent, title, message)
            logger.debug(f"Warning notification shown: {title}")
        except Exception as e:
            logger.error(f"Failed to show warning notification: {e}")

    @staticmethod
    def show_error(parent, title: str, message: str) -> None:
        """
        显示错误通知

        Args:
            parent: 父窗口
            title: 通知标题
            message: 通知内容
        """
        try:
            QMessageBox.critical(parent, title, message)
            logger.debug(f"Error notification shown: {title}")
        except Exception as e:
            logger.error(f"Failed to show error notification: {e}")

    @staticmethod
    def show_question(parent, title: str, message: str) -> bool:
        """
        显示确认对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 对话框内容

        Returns:
            用户是否点击了"是"按钮
        """
        try:
            reply = QMessageBox.question(
                parent, title, message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            result = (reply == QMessageBox.Yes)
            logger.debug(f"Question dialog shown: {title}, result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to show question dialog: {e}")
            return False


# 全局通知服务实例
notification_service = NotificationService()
