"""
项目创建服务模块
处理项目创建的核心业务逻辑
"""

import os
import tempfile
import shutil
from typing import Dict, Any, Optional, List

from src.core.logger import logger
from src.utils.date_utils import get_current_datetime
from src.core.config_manager import config_manager
from src.features.ltr_manager.service.ltr_application_service import LTRApplicationService


class ProjectCreatorService:
    """
    项目创建服务类
    处理项目创建的核心业务逻辑
    """

    def __init__(self):
        self.temp_folder = None

    def create_temp_folder_and_save_attachments(self, msg_file_path: str, attachments: List[Dict]) -> str:
        """
        创建临时项目结构，保存邮件和附件

        Args:
            msg_file_path: 邮件文件路径
            attachments: 附件列表

        Returns:
            临时文件夹路径
        """
        try:
            # 获取配置的临时目录路径
            temp_dir_config = config_manager.get("paths.temp_dir", "data/temp")

            # 确定基础路径
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

            # 确保临时目录是绝对路径
            if not os.path.isabs(temp_dir_config):
                temp_dir = os.path.join(base_path, temp_dir_config)
            else:
                temp_dir = temp_dir_config

            # 确保目录存在
            os.makedirs(temp_dir, exist_ok=True)

            # 使用项目中的日期工具生成时间戳
            timestamp = get_current_datetime("%Y%m%d_%H%M%S")
            temp_folder = os.path.join(temp_dir, f"ltr_application_{timestamp}")
            os.makedirs(temp_folder, exist_ok=True)

            # 保存原始.msg邮件文件
            if msg_file_path and os.path.exists(msg_file_path):
                msg_filename = os.path.basename(msg_file_path)
                dest_path = os.path.join(temp_folder, msg_filename)
                shutil.copy2(msg_file_path, dest_path)
                logger.info(f"已保存邮件文件到: {dest_path}")

            # 保存附件
            for attachment in attachments:
                filename = attachment.get('filename', '')
                content = attachment.get('content', b'')
                if filename and content:
                    attachment_path = os.path.join(temp_folder, filename)
                    with open(attachment_path, 'wb') as f:
                        f.write(content)
                    logger.info(f"已保存附件到: {attachment_path}")

            self.temp_folder = temp_folder
            logger.info(f"已创建临时文件夹: {temp_folder}")
            return temp_folder

        except Exception as e:
            logger.error(f"创建临时文件夹和保存附件时出错: {e}")
            raise

    def process_word_attachment(self, word_attachment: Dict) -> Dict[str, Any]:
        """
        处理Word附件，提取LTR申请单信息

        Args:
            word_attachment: Word附件信息

        Returns:
            提取的数据或错误信息
        """
        try:
            # 检查附件中是否包含已保存的文件路径
            saved_file_path = word_attachment.get('file_path')

            if saved_file_path and os.path.exists(saved_file_path):
                # 使用已保存的文件而不是创建临时文件
                logger.info(f"Using saved attachment file: {saved_file_path}")

                # 使用LTRApplicationService处理Word文档
                ltr_service = LTRApplicationService()
                result = ltr_service.process_application_file(saved_file_path)
                return result
            else:
                # 原有逻辑：创建临时文件
                temp_dir = tempfile.gettempdir()
                filename = word_attachment.get('filename', 'temp.doc')
                temp_file_path = os.path.join(temp_dir, filename)

                # 写入附件数据到临时文件
                content = word_attachment.get('content')
                if content:
                    with open(temp_file_path, 'wb') as f:
                        f.write(content)

                    # 使用LTRApplicationService处理Word文档
                    # 这会自动验证文档是否为申请单并在处理过程中提取版本信息
                    ltr_service = LTRApplicationService()
                    result = ltr_service.process_application_file(temp_file_path)
                    return result
                else:
                    return {"error": "附件内容为空"}

        except Exception as e:
            logger.error(f"处理Word附件时出错: {e}")
            return {"error": f"处理Word附件失败: {str(e)}"}

