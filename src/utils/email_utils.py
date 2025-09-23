"""
邮件工具模块
提供底层的邮件操作工具函数
"""

import win32com.client
import pythoncom
from typing import List, Dict, Any, Optional
from src.core.logger import logger


class EmailUtils:
    """
    邮件工具类
    提供与Outlook交互的功能
    """

    def __init__(self):
        """初始化邮件工具"""
        self.outlook = None
        self.namespace = None

    def connect_to_outlook(self) -> bool:
        """
        连接到Outlook应用程序

        Returns:
            bool: 连接是否成功
        """
        try:
            pythoncom.CoInitialize()
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook.GetNamespace("MAPI")
            logger.info("成功连接到Outlook")
            return True
        except Exception as e:
            logger.error(f"连接Outlook失败: {e}")
            return False

    def get_inbox_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取收件箱中的邮件列表

        Args:
            limit (int): 获取邮件的最大数量

        Returns:
            List[Dict[str, Any]]: 邮件信息列表
        """
        messages = []
        try:
            if not self.namespace:
                logger.error("Outlook未连接")
                return messages

            inbox = self.namespace.GetDefaultFolder(6)  # 6代表收件箱
            message_count = min(inbox.Items.Count, limit)

            # 按时间倒序排列获取最新的邮件
            for i in range(message_count):
                try:
                    # Outlook的索引从1开始
                    item = inbox.Items(inbox.Items.Count - i)
                    message_info = {
                        'subject': item.Subject,
                        'sender': item.SenderName,
                        'received_time': item.ReceivedTime,
                        'entry_id': item.EntryID,
                        'has_attachments': item.Attachments.Count > 0,
                        'attachment_count': item.Attachments.Count
                    }
                    messages.append(message_info)
                except Exception as e:
                    logger.warning(f"获取邮件信息时出错: {e}")
                    continue

            logger.info(f"成功获取 {len(messages)} 封邮件")
        except Exception as e:
            logger.error(f"获取收件箱邮件失败: {e}")

        return messages

    def get_message_by_id(self, entry_id: str) -> Optional[Any]:
        """
        根据EntryID获取邮件对象

        Args:
            entry_id (str): 邮件的EntryID

        Returns:
            Optional[Any]: 邮件对象，如果未找到则返回None
        """
        try:
            if not self.namespace:
                logger.error("Outlook未连接")
                return None

            message = self.namespace.GetItemFromID(entry_id)
            return message
        except Exception as e:
            logger.error(f"根据ID获取邮件失败: {e}")
            return None

    def get_message_attachments(self, message) -> List[Dict[str, Any]]:
        """
        获取邮件附件信息

        Args:
            message: 邮件对象

        Returns:
            List[Dict[str, Any]]: 附件信息列表
        """
        attachments = []
        try:
            for i in range(message.Attachments.Count):
                attachment = message.Attachments(i + 1)  # Outlook索引从1开始
                attachment_info = {
                    'filename': attachment.FileName,
                    'size': attachment.Size,
                    'attachment_object': attachment
                }
                attachments.append(attachment_info)
        except Exception as e:
            logger.error(f"获取邮件附件失败: {e}")

        return attachments

    def save_attachment(self, attachment, save_path: str) -> bool:
        """
        保存附件到指定路径

        Args:
            attachment: 附件对象
            save_path (str): 保存路径

        Returns:
            bool: 保存是否成功
        """
        try:
            attachment.SaveAsFile(save_path)
            logger.info(f"附件已保存到: {save_path}")
            return True
        except Exception as e:
            logger.error(f"保存附件失败: {e}")
            return False

    def disconnect(self) -> None:
        """断开与Outlook的连接"""
        try:
            if self.outlook:
                del self.outlook
            pythoncom.CoUninitialize()
            logger.info("已断开与Outlook的连接")
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")


# 全局邮件工具实例
email_utils = EmailUtils()
