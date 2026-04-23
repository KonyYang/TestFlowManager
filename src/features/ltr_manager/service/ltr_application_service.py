"""
LTR申请单服务模块
提供LTR申请单处理相关的服务功能
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from src.core.logger import logger
from src.core.event_dispatcher import event_dispatcher, EventTopics
from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
from src.features.ltr_manager.service.application_processing.document_validator import LTRApplicationFormValidator
from src.features.ltr_manager.service.application_processing.data_extractor import LTRApplicationDataExtractor
from src.features.ltr_manager.service.application_processing.ltr_number_generator import LTRNumberGenerator
from src.infrastructure.office.facade import OfficeFacade

# 配置日志
processor_logger = logging.getLogger(__name__)

class LTRApplicationService:
    """
    LTR申请单服务类
    提供LTR申请单处理相关的服务功能
    """

    def __init__(self, office_facade: OfficeFacade | None = None):
        """
        初始化LTR申请单服务
        """
        self.office_facade = office_facade or OfficeFacade()
        self.validator = LTRApplicationFormValidator(office_facade=self.office_facade)
        self.extractor = LTRApplicationDataExtractor(office_facade=self.office_facade)

        self.event_dispatcher = event_dispatcher
        # Note: ltr.application.confirmed 事件由 LTRStatusCoordinator 处理

    def apply_ltr(self, application_data: Dict[str, Any], parent=None) -> Dict[str, Any]:
        """
        执行LTR编号申请
        """
        logger.info("开始执行LTR编号申请")

        try:
            # 验证必要参数
            if not application_data:
                return {"success": False, "error": "申请数据为空"}

            # 准备写入Excel的数据列
            data_columns = self._prepare_data_columns(application_data)

            # 获取DL编号（如果有的话）
            dl_number = application_data.get('DL', '').strip()

            # 直接调用LTR编号生成器，让其内部处理不同类型的DL编号
            try:
                generator = LTRNumberGenerator(parent)
                result = generator.create_and_write_ltr_number(
                    DL=dl_number,
                    data_columns=data_columns
                )
                return self._handle_ltr_result(result)
            except Exception as e:
                logger.error(f"调用LTR编号生成器时发生错误: {e}")
                return {"success": False, "error": f"申请LTR编号时发生错误: {str(e)}"}

        except Exception as e:
            logger.error(f"调用LTR编号生成器时发生错误: {e}")
            return {"success": False, "error": f"申请LTR编号时发生错误: {str(e)}"}


    def _handle_ltr_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理LTR编号生成器的返回结果

        Args:
            result: LTR编号生成器的返回结果

        Returns:
            格式化的返回字典
        """
        if result and result.get('executed_write'):
            ltr_number = result.get('ltr_number')
            logger.info(f"LTR编号申请成功: {ltr_number}")
            return {
                "success": True,
                "ltr_number": ltr_number,
                "message": "LTR编号申请成功"
            }
        else:
            # 检查是否有 retry 标志并传递
            response = {
                "success": False,
                "error": result.get('error', "LTR编号申请未执行写入操作")
            }

            # 如果有 retry 标志，传递给上层
            if 'retry' in result:
                response['retry'] = result['retry']

            logger.warning("LTR编号申请未执行写入操作")
            return response

    def _prepare_data_columns(self, application_data: Dict[str, Any]) -> list:
        """
        准备要写入Excel的数据列

        Args:
            application_data: 申请数据

        Returns:
            数据列列表
        """
        # 根据实际需求映射数据到Excel列
        data_columns = [
            application_data.get('project_type', ''),
            application_data.get('sample_information', ''),
            application_data.get('tests_to_be_performed', ''),
            application_data.get('test_type', ''),
            application_data.get('requested_by', ''),
            application_data.get('location', ''),
            application_data.get('project_leader', ''),
            application_data.get('test_result', ''),
            application_data.get('failed_item', ''),
            application_data.get('sample_deposition', ''),
            application_data.get('sub_contract', ''),
            application_data.get('test_fee', ''),
            application_data.get('remarks_po', '')
        ]

        return data_columns

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
        from src.core.config_manager import config_manager
        application_data = LTRApplicationData()
        # 设置默认的project_leader
        default_project_leader = config_manager.get_default("project_leader", "")
        if default_project_leader:
            application_data.project_leader = default_project_leader
        return application_data

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

        # 发送处理开始事件
        self.event_dispatcher.dispatch(EventTopics.LTR_PROCESSING_STARTED, {
            "file_path": doc_filepath
        })

        try:
            # 首先验证文档是否为申请单（仅对.docx文件）
            if doc_filepath.lower().endswith('.docx'):
                validation_result = self.validate_application_form(doc_filepath)
                if not validation_result.get("is_valid"):
                    error_msg = validation_result.get("error", "文档不是有效的申请单")
                    logger.warning(f"Document {doc_filepath} is not a valid application form")
                    # 发送处理失败事件
                    self.event_dispatcher.dispatch(EventTopics.LTR_PROCESSING_FAILED, {
                        "file_path": doc_filepath,
                        "error": error_msg
                    })
                    return {"error": error_msg}
            elif doc_filepath.lower().endswith('.doc'):
                # 对于.doc文件，继续使用原来的处理方式
                logger.info("Processing .doc file")
            else:
                error_msg = "不支持的文件类型"
                logger.warning(f"Unsupported file type: {doc_filepath}")
                # 发送处理失败事件
                self.event_dispatcher.dispatch(EventTopics.LTR_PROCESSING_FAILED, {
                    "file_path": doc_filepath,
                    "error": error_msg
                })
                return {"error": error_msg}

            # 提取数据
            result = self.extractor.extract_application_data(doc_filepath)

            # 发送处理完成事件
            self.event_dispatcher.dispatch(EventTopics.LTR_PROCESSING_COMPLETED, {
                "file_path": doc_filepath,
                "data": result
            })

            return result

        except Exception as e:
            error_msg = f"处理申请单文件时出错: {str(e)}"
            logger.error(f"Error processing application file: {e}", exc_info=True)
            # 发送处理失败事件
            self.event_dispatcher.dispatch(EventTopics.LTR_PROCESSING_FAILED, {
                "file_path": doc_filepath,
                "error": error_msg
            })
            return {
                "error": error_msg,
            }

    # 保持其他方法以确保向后兼容性
    def _extract_field_value_from_table(self, doc, search_keyword: str, next_row: bool = False):
        from src.utils.word_utils import extract_field_value_from_table
        return extract_field_value_from_table(doc, search_keyword, next_row)

    def _extract_requested_testing_info(self, doc) -> Dict[str, str]:
        return self.extractor._extract_requested_testing_info(doc)

    def _extract_test_sample_info(self, doc) -> Dict[str, str]:
        return self.extractor._extract_test_sample_info(doc)

    def _quit_word_app(self):
        # 不再需要单独退出Word应用，由word_utils统一管理
        pass
