"""
LTR申请单服务模块
提供LTR申请单处理相关的服务功能
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
from src.features.ltr_manager.service.application_processing.document_validator import LTRApplicationFormValidator
from src.features.ltr_manager.service.application_processing.data_extractor import LTRApplicationDataExtractor
from src.utils.word_utils import get_shared_word_app, release_word_app

# 配置日志
processor_logger = logging.getLogger(__name__)

class LTRApplicationService:
    """
    LTR申请单服务类
    提供LTR申请单处理相关的服务功能
    """

    def __init__(self):
        """
        初始化LTR申请单服务
        """
        self.data_model = LTRApplicationData()
        self.validator = LTRApplicationFormValidator()
        self.extractor = LTRApplicationDataExtractor()

    def process_word_application(self, doc_filepath: str) -> LTRApplicationData:
        """
        处理Word格式的LTR申请单

        Args:
            doc_filepath: Word文档路径

        Returns:
            LTRApplicationData对象，包含提取的数据
        """
        try:
            logger.info(f"Processing Word application: {doc_filepath}")

            # 使用处理器提取数据
            result = self.process_application_file(doc_filepath)

            # 检查是否有错误
            if "error" in result:
                application_data = LTRApplicationData()
                application_data.status = "failed"
                application_data.error_message = result["error"]
                if "partial_data" in result:
                    # 如果有部分数据，也进行填充
                    for key, value in result["partial_data"].items():
                        if hasattr(application_data, key):
                            setattr(application_data, key, value)
                return application_data

            # 成功处理，填充数据模型
            application_data = LTRApplicationData.from_dict(result)
            application_data.file_path = doc_filepath
            application_data.status = "completed"

            logger.info("Successfully processed Word application")
            return application_data

        except Exception as e:
            logger.error(f"Error processing Word application: {e}")
            application_data = LTRApplicationData()
            application_data.status = "failed"
            application_data.error_message = str(e)
            return application_data

    def create_new_application(self) -> LTRApplicationData:
        """
        创建新的空白LTR申请单

        Returns:
            空的LTRApplicationData对象
        """
        logger.info("Creating new blank LTR application")
        return LTRApplicationData()

    def validate_application_data(self, application_data: LTRApplicationData) -> Dict[str, Any]:
        """
        验证申请单数据的完整性

        Args:
            application_data: LTR申请单数据

        Returns:
            包含验证结果的字典
        """
        try:
            logger.debug("Validating application data")
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }

            # 检查必填字段
            required_fields = ['requested_by', 'location', 'project_type', 'test_type']
            for field in required_fields:
                value = getattr(application_data, field, "")
                if not value or not str(value).strip():
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"必填字段 '{field}' 不能为空")

            # 检查日期格式（如果有提供）
            date_fields = ['date_lab_received_samples', 'estimated_completion_date']
            # 这里可以添加更详细的日期格式验证逻辑

            logger.debug(f"Validation result: {validation_result}")
            return validation_result

        except Exception as e:
            logger.error(f"Error validating application data: {e}")
            return {
                "is_valid": False,
                "errors": [f"验证过程中出错: {str(e)}"],
                "warnings": []
            }

    def validate_application_form(self, doc_filepath: str) -> Dict[str, Any]:
        """
        校验 Word 文件是否为测试申请单，并在页脚提取版本号。

        Args:
            doc_filepath (str): Word 文件的完整路径 (.doc, .docx)。

        Returns:
            dict: 包含验证结果和版本号的字典
        """
        return self.validator.validate_application_form(doc_filepath)

    def _validate_docx_application_form(self, doc_filepath: str) -> Tuple[bool, Optional[str]]:
        """
        校验 Word 文件是否为测试申请单，并在页脚提取版本号。
        """
        return self.validator._validate_docx_application_form(doc_filepath)

    def process_application_file(self, doc_filepath: str, email_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理申请单文件，使用共享的Word实例提高性能

        Args:
            doc_filepath: Word文档路径
            email_data: 邮件数据（可选）

        Returns:
            dict: 提取的数据或错误信息
        """
        logger.info(f"Processing application file: {doc_filepath}")

        # 获取共享的Word应用实例
        word_app = get_shared_word_app()
        if not word_app:
            logger.error("无法获取Word应用实例")
            return {"error": "无法初始化Word应用程序"}

        try:
            # 首先验证文档是否为申请单（仅对.docx文件）
            if doc_filepath.lower().endswith('.docx'):
                validation_result = self.validate_application_form(doc_filepath)
                if not validation_result.get("is_valid"):
                    logger.warning(f"Document {doc_filepath} is not a valid application form")
                    return {"error": validation_result.get("error", "文档不是有效的申请单")}
            elif doc_filepath.lower().endswith('.doc'):
                # 对于.doc文件，继续使用原来的处理方式
                logger.info("Processing .doc file")
            else:
                logger.warning(f"Unsupported file type: {doc_filepath}")
                return {"error": "不支持的文件类型"}

            # 提取数据
            return self.extractor.extract_application_data(doc_filepath)

        except Exception as e:
            logger.error(f"Error processing application file: {e}", exc_info=True)
            return {
                "error": f"处理申请单文件时出错: {str(e)}",
            }
        finally:
            # 释放Word应用实例
            release_word_app()

    # 保持其他方法以确保向后兼容性
    def _extract_field_value_from_table(self, doc, search_keyword: str, next_row: bool = False):
        from src.utils.word_utils import extract_field_value_from_table
        return extract_field_value_from_table(doc, search_keyword, next_row)

    def _extract_requested_testing_info(self, doc) -> Dict[str, str]:
        return self.extractor._extract_requested_testing_info(doc)

    def _extract_test_sample_info(self, doc) -> str:
        return self.extractor._extract_test_sample_info(doc)

    def _quit_word_app(self):
        # 不再需要单独退出Word应用，由word_utils统一管理
        pass
