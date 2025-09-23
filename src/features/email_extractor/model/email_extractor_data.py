"""
邮件提取数据模型模块
定义邮件提取相关的数据结构，简化版本
"""

from typing import List, Dict, Optional
from src.core.logger import logger


class EmailExtractorData:
    """
    邮件提取数据模型类
    管理邮件提取相关的数据，简化版本
    """

    def __init__(self):
        # MSG文件相关数据
        self.selected_msg_file: Optional[str] = None
        self.msg_file_data: Optional[Dict] = None

        # 邮件服务器相关数据
        self.email_list: List[Dict] = []
        self.selected_email: Optional[Dict] = None
        self.selected_email_id: Optional[str] = None

        # 附件相关数据
        self.attachments: List[Dict] = []
        self.selected_attachment: Optional[Dict] = None

    def set_msg_file_data(self, file_path: str, email_data: Dict) -> None:
        """
        设置MSG文件数据

        Args:
            file_path: MSG文件路径
            email_data: 邮件数据
        """
        self.selected_msg_file = file_path
        self.msg_file_data = email_data
        logger.debug(f"已设置MSG文件数据: {file_path}")

    def get_msg_file_data(self) -> Optional[Dict]:
        """
        获取MSG文件数据

        Returns:
            邮件数据
        """
        return self.msg_file_data

    def get_email_data(self) -> Dict:
        """
        获取邮件数据（统一接口）

        Returns:
            邮件数据
        """
        if self.msg_file_data:
            return self.msg_file_data
        else:
            return {}

    def set_email_list(self, email_list: List[Dict]) -> None:
        """
        设置邮件列表

        Args:
            email_list: 邮件列表
        """
        self.email_list = email_list
        logger.debug(f"已设置邮件列表，共 {len(email_list)} 封邮件")

    def get_email_list(self) -> List[Dict]:
        """
        获取邮件列表

        Returns:
            邮件列表
        """
        return self.email_list

    def set_selected_email(self, email_id: str, email_data: Dict) -> None:
        """
        设置选中的邮件

        Args:
            email_id: 邮件ID
            email_data: 邮件数据
        """
        self.selected_email_id = email_id
        self.selected_email = email_data
        logger.debug(f"已选择邮件: {email_id}")

    def get_selected_email(self) -> Optional[Dict]:
        """
        获取选中的邮件

        Returns:
            邮件数据
        """
        return self.selected_email

    def set_attachments(self, attachments: List[Dict]) -> None:
        """
        设置附件列表

        Args:
            attachments: 附件列表
        """
        self.attachments = attachments
        logger.debug(f"已设置附件列表，共 {len(attachments)} 个附件")

    def get_attachments(self) -> List[Dict]:
        """
        获取附件列表

        Returns:
            附件列表
        """
        return self.attachments

    def set_selected_attachment(self, attachment_info: Dict) -> None:
        """
        设置选中的附件

        Args:
            attachment_info: 附件信息
        """
        self.selected_attachment = attachment_info
        logger.debug(f"已选择附件: {attachment_info.get('filename', 'Unknown')}")

    def get_selected_attachment(self) -> Optional[Dict]:
        """
        获取选中的附件

        Returns:
            附件信息
        """
        return self.selected_attachment

    def clear_selection(self) -> None:
        """清空选择"""
        self.selected_email = None
        self.selected_email_id = None
        self.attachments = []
        self.selected_attachment = None
        logger.debug("已清空选择")
