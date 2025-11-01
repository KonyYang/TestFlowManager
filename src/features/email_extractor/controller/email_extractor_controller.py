"""
邮件提取控制器模块
处理简单的邮件文件选择和附件提取
"""

import os
from PyQt5.QtWidgets import QMessageBox
from src.core.logger import logger
from src.core.base_controller import BaseController
from src.features.email_extractor.model.email_extractor_data import EmailExtractorData
from src.features.email_extractor.service.email_extractor_service import EmailExtractorService


class EmailExtractorController(BaseController):
    """
    邮件提取控制器类
    处理简单的邮件文件选择和附件提取
    """

    def __init__(self, view):
        """
        初始化邮件提取控制器

        Args:
            view: 邮件选择对话框视图实例
        """
        super().__init__(view)
        self.data_model = EmailExtractorData()
        self.service = EmailExtractorService(self.data_model)

    def initialize(self) -> bool:
        """
        初始化控制器

        Returns:
            初始化是否成功
        """
        try:
            logger.info("正在初始化邮件提取控制器...")

            # 连接信号
            self.view.msg_file_selected.connect(self._on_msg_file_selected)

            logger.info("邮件提取控制器初始化成功")
            return True
        except Exception as e:
            return self.handle_error(e, "初始化邮件提取控制器失败")

    def _on_msg_file_selected(self, file_path: str):
        """
        MSG文件选中事件

        Args:
            file_path: MSG文件路径
        """
        try:
            logger.info(f"选中MSG文件: {file_path}")

            # 通过服务处理MSG文件
            result = self.service.process_msg_file(file_path)
            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                logger.error(f"处理MSG文件失败: {error_msg}")
                QMessageBox.critical(self.view, "错误", f"处理MSG文件失败: {error_msg}")
                return False

            # 更新视图显示
            email_data = result.get("email_data", {})
            subject = email_data.get('subject', '无主题')
            sender = email_data.get('sender', '未知发件人')
            received_time = email_data.get('received_time', '未知时间')

            info_text = f"主题: {subject}\n发件人: {sender}  时间: {received_time}"
            attachments = email_data.get("attachments", [])
            self.view.update_email_info(info_text, attachments)
            
            logger.debug(f"MSG file processed successfully, attachments count: {len(attachments)}")

            return True
        except Exception as e:
            logger.error(f"处理MSG文件选中事件失败: {e}", exc_info=True)
            return self.handle_error(e, "处理MSG文件选中事件失败")

    def handle_msg_file_selection(self, file_path: str):
        """
        处理MSG文件选择

        Args:
            file_path: MSG文件路径
        """
        self.data_model.set_msg_file_data(file_path, {})
        self.view.update_email_info("已选择MSG文件: " + os.path.basename(file_path))

    def process_msg_file(self, file_path: str):
        """
        处理MSG文件

        Args:
            file_path: MSG文件路径

        Returns:
            处理结果
        """
        return self.service.process_msg_file(file_path)

    def get_processed_email_data(self):
        """
        获取处理后的邮件数据

        Returns:
            邮件数据
        """
        return self.data_model.get_email_data()

    def get_selected_file_path(self):
        """
        获取选中的文件路径

        Returns:
            文件路径
        """
        return self.data_model.selected_msg_file

    def get_temp_folder_path(self):
        """
        获取临时文件夹路径

        Returns:
            临时文件夹路径
        """
        temp_folder_path = self.service.get_temp_folder()
        logger.debug(f"EmailExtractorController返回的临时文件夹路径: {temp_folder_path}")
        return temp_folder_path

    def connect_to_email_server(self) -> bool:
        """
        连接到邮件服务器

        Returns:
            是否成功连接
        """
        return self.service.connect_to_email_server()

    def load_email_list(self, limit: int = 50):
        """
        加载邮件列表

        Args:
            limit: 加载邮件的最大数量

        Returns:
            邮件信息列表
        """
        return self.service.load_email_list(limit)

    def select_email(self, email_id: str) -> bool:
        """
        选择邮件

        Args:
            email_id: 邮件ID

        Returns:
            是否成功选择邮件
        """
        return self.service.select_email(email_id)

    def load_email_attachments(self, email_id: str):
        """
        加载邮件附件

        Args:
            email_id: 邮件ID

        Returns:
            附件信息列表
        """
        return self.service.load_email_attachments(email_id)

    def get_selected_attachment(self):
        """
        获取当前选中的附件

        Returns:
            选中的附件数据或None
        """
        return self.view.get_selected_attachment()

    def select_attachment(self, attachment_info: dict) -> bool:
        """
        选择附件

        Args:
            attachment_info: 附件信息

        Returns:
            是否成功选择附件
        """
        return self.service.select_attachment(attachment_info)

    def save_selected_attachment(self, save_path: str) -> bool:
        """
        保存选中的附件

        Args:
            save_path: 保存路径

        Returns:
            是否成功保存
        """
        return self.service.save_selected_attachment(save_path)

    def disconnect_email_server(self):
        """断开邮件服务器连接"""
        self.service.disconnect_email_server()

    def clear_selection(self):
        """清空选择"""
        self.service.clear_selection()
        self.view.clear_selection()
