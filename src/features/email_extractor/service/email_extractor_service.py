"""
邮件提取服务模块
提供邮件提取相关的服务功能，支持多种输入方式
"""

import os
import tempfile
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.core.logger import logger
from src.features.email_extractor.model.email_extractor_data import EmailExtractorData
from src.utils.email_utils import email_utils
from src.utils.msg_file_utils import process_msg_file
from src.core.config_manager import config_manager


class EmailExtractorService:
    """
    邮件提取服务类
    提供邮件提取相关的服务功能，支持多种输入方式
    """

    def __init__(self, data_model: EmailExtractorData):
        """
        初始化邮件提取服务

        Args:
            data_model: 邮件提取数据模型实例
        """
        self.data_model = data_model
        self.temp_folder = None

    def connect_to_email_server(self) -> bool:
        """
        连接到邮件服务器

        Returns:
            是否成功连接
        """
        try:
            logger.info("正在连接到邮件服务器...")
            success = email_utils.connect_to_outlook()
            if success:
                logger.info("成功连接到邮件服务器")
            else:
                logger.error("连接邮件服务器失败")
            return success
        except Exception as e:
            logger.error(f"连接邮件服务器时发生错误: {e}")
            return False

    def load_email_list(self, limit: int = 50) -> List[Dict]:
        """
        加载邮件列表

        Args:
            limit: 加载邮件的最大数量

        Returns:
            邮件信息列表
        """
        try:
            logger.info("正在加载邮件列表...")
            email_list = email_utils.get_inbox_messages(limit)
            self.data_model.set_email_list(email_list)
            logger.info(f"成功加载 {len(email_list)} 封邮件")
            return email_list
        except Exception as e:
            logger.error(f"加载邮件列表时发生错误: {e}")
            return []

    def select_email(self, email_id: str) -> bool:
        """
        选择邮件

        Args:
            email_id: 邮件ID

        Returns:
            是否成功选择邮件
        """
        try:
            logger.info(f"正在选择邮件: {email_id}")
            # 在数据模型中查找邮件信息
            email_list = self.data_model.get_email_list()
            selected_email = None
            for email in email_list:
                if email.get('entry_id') == email_id:
                    selected_email = email
                    break

            if selected_email:
                self.data_model.set_selected_email(email_id, selected_email)
                logger.info(f"成功选择邮件: {selected_email.get('subject', 'Unknown')}")
                return True
            else:
                logger.error(f"未找到邮件: {email_id}")
                return False
        except Exception as e:
            logger.error(f"选择邮件时发生错误: {e}")
            return False

    def load_email_attachments(self, email_id: str) -> List[Dict]:
        """
        加载邮件附件

        Args:
            email_id: 邮件ID

        Returns:
            附件信息列表
        """
        try:
            logger.info(f"正在加载邮件附件: {email_id}")
            email_obj = email_utils.get_message_by_id(email_id)
            if not email_obj:
                logger.error("无法获取邮件对象")
                return []

            attachments = email_utils.get_message_attachments(email_obj)
            self.data_model.set_attachments(attachments)
            logger.info(f"成功加载 {len(attachments)} 个附件")
            return attachments
        except Exception as e:
            logger.error(f"加载邮件附件时发生错误: {e}")
            return []

    def select_attachment(self, attachment_info: Dict) -> bool:
        """
        选择附件

        Args:
            attachment_info: 附件信息

        Returns:
            是否成功选择附件
        """
        try:
            logger.info(f"正在选择附件: {attachment_info.get('filename', 'Unknown')}")
            self.data_model.set_selected_attachment(attachment_info)
            logger.info(f"成功选择附件: {attachment_info.get('filename', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"选择附件时发生错误: {e}")
            return False

    def save_selected_attachment(self, save_path: str) -> bool:
        """
        保存选中的附件

        Args:
            save_path: 保存路径

        Returns:
            是否成功保存
        """
        try:
            logger.info("正在保存选中的附件...")
            selected_attachment = self.data_model.get_selected_attachment()
            if not selected_attachment:
                logger.error("未选择任何附件")
                return False

            attachment_obj = selected_attachment.get('attachment_object')
            if not attachment_obj:
                # 如果是来自MSG文件的附件，直接保存内容
                content = selected_attachment.get('content')
                if content:
                    try:
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        logger.info(f"附件已保存到: {save_path}")
                        return True
                    except Exception as e:
                        logger.error(f"保存附件内容失败: {e}")
                        return False
                else:
                    logger.error("附件对象无效")
                    return False

            success = email_utils.save_attachment(attachment_obj, save_path)
            if success:
                logger.info(f"附件已保存到: {save_path}")
            else:
                logger.error("保存附件失败")
            return success
        except Exception as e:
            logger.error(f"保存附件时发生错误: {e}")
            return False

    def process_msg_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理MSG文件

        Args:
            file_path: MSG文件路径

        Returns:
            处理结果
        """
        try:
            logger.info(f"正在处理MSG文件: {file_path}")
            result = process_msg_file(file_path)
            if result.get("success"):
                email_data = result.get("email_data", {})
                self.data_model.set_msg_file_data(file_path, email_data)
                logger.info("MSG文件处理成功")
                
                # 创建包含附件的临时文件夹
                attachments = email_data.get("attachments", [])
                if attachments:
                    self.temp_folder = self.create_temp_folder_with_attachments(attachments, file_path)
                    if self.temp_folder:
                        logger.info(f"已创建包含附件的临时文件夹: {self.temp_folder}")
                    else:
                        logger.error("创建包含附件的临时文件夹失败")
            else:
                logger.error(f"MSG文件处理失败: {result.get('error', '未知错误')}")
            return result
        except Exception as e:
            logger.error(f"处理MSG文件时发生错误: {e}")
            return {"success": False, "error": str(e)}

    def create_temp_folder_with_attachments(self, attachments: List[Dict], msg_file_path: str) -> Optional[str]:
        """
        创建包含附件的临时文件夹

        Args:
            attachments: 附件列表
            msg_file_path: MSG文件路径

        Returns:
            临时文件夹路径
        """
        try:
            # 获取配置的临时目录路径
            temp_base_dir = config_manager.get("paths.temp_dir", r"D:\TestFlowManager\Temp")
            
            # 确保临时目录存在
            if not os.path.exists(temp_base_dir):
                os.makedirs(temp_base_dir)
            
            # 创建带时间戳的临时文件夹
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_folder_name = f"email_attachments_{timestamp}"
            self.temp_folder = os.path.join(temp_base_dir, temp_folder_name)
            
            # 创建临时文件夹
            os.makedirs(self.temp_folder)
            logger.info(f"创建临时文件夹: {self.temp_folder}")

            # 将附件保存到临时文件夹
            for attachment in attachments:
                filename = attachment.get('filename', 'unknown_file')
                content = attachment.get('content')
                
                if content:
                    file_path = os.path.join(self.temp_folder, filename)
                    try:
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        logger.info(f"附件已保存到临时文件夹: {file_path}")
                    except Exception as e:
                        logger.error(f"保存附件到临时文件夹失败: {e}")

            # 同时复制.msg文件到临时文件夹
            if msg_file_path and os.path.exists(msg_file_path):
                msg_filename = os.path.basename(msg_file_path)
                temp_msg_path = os.path.join(self.temp_folder, msg_filename)
                try:
                    shutil.copy2(msg_file_path, temp_msg_path)
                    logger.info(f"MSG文件已复制到临时文件夹: {temp_msg_path}")
                except Exception as e:
                    logger.error(f"复制MSG文件到临时文件夹失败: {e}")

            return self.temp_folder
        except Exception as e:
            logger.error(f"创建包含附件的临时文件夹失败: {e}")
            return None

    def get_temp_folder(self) -> Optional[str]:
        """
        获取临时文件夹路径

        Returns:
            临时文件夹路径
        """
        return self.temp_folder

    def cleanup_temp_folder(self) -> bool:
        """
        清理临时文件夹

        Returns:
            是否成功清理
        """
        if self.temp_folder and os.path.exists(self.temp_folder):
            try:
                shutil.rmtree(self.temp_folder)
                logger.info(f"已清理临时文件夹: {self.temp_folder}")
                self.temp_folder = None
                return True
            except Exception as e:
                logger.error(f"清理临时文件夹失败: {e}")
                return False
        return True

    def disconnect_email_server(self) -> None:
        """断开邮件服务器连接"""
        try:
            logger.info("正在断开邮件服务器连接...")
            email_utils.disconnect()
            logger.info("已断开邮件服务器连接")
        except Exception as e:
            logger.error(f"断开邮件服务器连接时发生错误: {e}")

    def clear_selection(self) -> None:
        """清空选择"""
        try:
            logger.info("正在清空选择...")
            self.data_model.clear_selection()
            # 清理临时文件夹
            self.cleanup_temp_folder()
            logger.info("已清空选择")
        except Exception as e:
            logger.error(f"清空选择时发生错误: {e}")