import win32com.client
import pythoncom
from typing import List, Dict, Any, Optional
from src.core.logger import logger


class EmailUtils:
    """
    邮件工具类
    提供邮件相关的工具功能
    """

    def __init__(self):
        """初始化邮件工具"""
        self.outlook = None
        self.namespace = None

    def connect_to_outlook(self) -> bool:
        """
        连接到Outlook

        Returns:
            是否成功连接
        """
        try:
            # 初始化COM库
            pythoncom.CoInitialize()
            
            # 尝试获取已运行的Outlook实例
            try:
                self.outlook = win32com.client.GetActiveObject("Outlook.Application")
                logger.info("成功连接到已运行的Outlook实例")
            except:
                # 如果没有运行的实例，则创建新的
                self.outlook = win32com.client.Dispatch("Outlook.Application")
                logger.info("成功创建新的Outlook实例")

            self.namespace = self.outlook.GetNamespace("MAPI")
            logger.info("成功连接到Outlook")
            return True
        except Exception as e:
            logger.error(f"连接Outlook失败: {e}")
            return False

    def get_inbox_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取收件箱邮件

        Args:
            limit: 获取邮件的最大数量

        Returns:
            邮件信息列表
        """
        messages = []
        try:
            if not self.namespace:
                logger.error("Outlook未连接")
                return messages

            inbox = self.namespace.GetDefaultFolder(6)  # 6代表收件箱
            items = inbox.Items

            # 按接收时间排序
            items.Sort("[ReceivedTime]", True)

            count = 0
            for item in items:
                if count >= limit:
                    break

                try:
                    # 获取邮件基本信息
                    message_info = {
                        'entry_id': item.EntryID,
                        'subject': getattr(item, 'Subject', '') or '',
                        'sender_name': getattr(item, 'SenderName', '') or '',
                        'received_time': getattr(item, 'ReceivedTime', '') or '',
                        'size': getattr(item, 'Size', 0) or 0
                    }
                    messages.append(message_info)
                    count += 1
                except Exception as e:
                    logger.warning(f"获取邮件信息失败: {e}")
                    continue

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
            # 反初始化COM库
            pythoncom.CoUninitialize()
            logger.info("已断开与Outlook的连接")
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")


# 全局邮件工具实例
email_utils = EmailUtils()