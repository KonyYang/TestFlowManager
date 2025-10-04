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

    def __init__(self):
        from src.core.event_dispatcher import event_dispatcher
        self.event_dispatcher = event_dispatcher

        # 订阅事件
        self.event_dispatcher.subscribe("project.creation.failed", self._on_project_creation_failed)
        self.event_dispatcher.subscribe("ltr.processing.failed", self._on_ltr_processing_failed)
        self.event_dispatcher.subscribe("error.notification", self._on_error_notification)

    def _on_project_creation_failed(self, data):
        """处理项目创建失败事件"""
        error = data.get("error", "未知错误")
        # 显示错误通知
        # 注意：需要确保有parent窗口引用
        pass

    def _on_ltr_processing_failed(self, data):
        """处理LTR处理失败事件"""
        error = data.get("error", "未知错误")
        # 显示错误通知
        pass

    def _on_error_notification(self, data):
        """处理通用错误通知事件"""
        title = data.get("title", "错误")
        message = data.get("message", "发生未知错误")
        # 显示错误通知
        pass
    
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
