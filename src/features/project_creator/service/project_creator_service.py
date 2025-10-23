"""
项目创建服务模块
处理项目创建的核心业务逻辑
"""

import os
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
        pass

    def process_word_attachment(self, word_attachment: Dict) -> Dict[str, Any]:
        """
        处理Word附件，提取LTR申请单信息

        Args:
            word_attachment: Word附件信息

        Returns:
            提取的数据或错误信息
        """
        try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                logger.info(f"[ProjectCreatorService] Word附件处理使用临时目录: {temp_dir}")
                filename = word_attachment.get('filename', 'temp.doc')
                temp_file_path = os.path.join(temp_dir, filename)
                logger.info(f"[ProjectCreatorService] Word附件临时文件路径: {temp_file_path}")

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
