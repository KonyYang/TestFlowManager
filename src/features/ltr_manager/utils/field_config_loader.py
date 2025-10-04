"""
LTR字段配置加载器
用于从配置文件加载字段映射关系
"""

import os
import sys
import json
from typing import List, Dict, Any
from src.core.logger import logger
from src.core.config_manager import config_manager


# 默认字段配置（内嵌在代码中）
DEFAULT_APPLICATION_FIELD_MAPPING = [
    {'key': 'DL', 'label': 'DL', 'editor_type': 'text'},
    {'key': 'project_type', 'label': 'Project Type', 'editor_type': 'dropdown',
     'options': ["NPD", "PEX", "OPS", "CR", "ADM"]},
    {'key': 'sample_information', 'label': 'Description P/N', 'editor_type': 'multiline'},
    {'key': 'tests_to_be_performed', 'label': 'Test Item', 'editor_type': 'multiline'},
    {'key': 'applicable_specifications', 'label': 'Applicable Specifications', 'editor_type': 'multiline'},
    {'key': 'test_type', 'label': 'Test Type', 'editor_type': 'dropdown',
     'options': ["Partial Qualification", "Qualification", "Failure Analysis", "Other", "Analysis",
                 "Chemical", "Electrical", "Environmental", "Whisker", "Mechanical", "ORT", "Solderability"]},
    {'key': 'requested_by', 'label': 'Requested by', 'editor_type': 'text'},
    {'key': 'location', 'label': 'Location', 'editor_type': 'text'},
    {'key': 'project_leader', 'label': 'Project Leader', 'editor_type': 'text'},
    {'key': 'test_result', 'label': 'Test Result', 'editor_type': 'dropdown',
     'options': ["In progress", "OK", "Ref", "NG", "In-waiting"]},
    {'key': 'failed_item', 'label': 'Failed item', 'editor_type': 'text'},
    {'key': 'sample_deposition', 'label': 'Sample deposition', 'editor_type': 'text'},
    {'key': 'sub_contract', 'label': 'Sub-contract', 'editor_type': 'dropdown', 'options': ["Yes", "No"]},
    {'key': 'test_fee', 'label': 'Test Fee', 'editor_type': 'text'},
    {'key': 'remarks_po', 'label': 'Remarks (PO)', 'editor_type': 'text'},
    {'key': 'phone', 'label': 'Phone', 'editor_type': 'text'},
    {'key': 'email_requestor', 'label': 'E-mail of Requestor', 'editor_type': 'text'},
    {'key': 'product_description', 'label': 'Product Description', 'editor_type': 'multiline'},
    {'key': 'lab_performing_the_tests', 'label': 'Lab Performing the Tests', 'editor_type': 'dropdown',
     'options': ["Dongguan", "Valley Green"]},
    {'key': 'condition_of_samples_when_received', 'label': 'Condition of Samples when Received', 'editor_type': 'dropdown',
     'options': ["Acceptable", "Not Acceptable"]},
    {'key': 'date_lab_received_samples', 'label': 'Date Lab Received Samples', 'editor_type': 'calendar'},
    {'key': 'estimated_completion_date', 'label': 'Estimated Completion Date', 'editor_type': 'calendar'},
    {'key': 'start_test_date', 'label': 'Start Test Date', 'editor_type': 'calendar'},
    {'key': 'finish_test_date', 'label': 'Finish Test Date', 'editor_type': 'calendar'},
    {'key': 'report_date', 'label': 'Report Date', 'editor_type': 'calendar'}
]

DEFAULT_EDITOR_FIELD_MAPPING = [
    {'key': 'project_type', 'label': 'Project Type', 'editor_type': 'dropdown',
     'options': ["NPD", "PEX", "OPS", "CR", "ADM"]},
    {'key': 'sample_information', 'label': 'Description P/N', 'editor_type': 'multiline'},
    {'key': 'tests_to_be_performed', 'label': 'Test Item', 'editor_type': 'multiline'},
    {'key': 'test_type', 'label': 'Test Type', 'editor_type': 'dropdown',
     'options': ["Partial Qualification", "Qualification", "Failure Analysis", "Other", "Analysis",
                 "Chemical", "Electrical", "Environmental", "Whisker", "Mechanical", "ORT", "Solderability"]},
    {'key': 'requested_by', 'label': 'Requested by', 'editor_type': 'text'},
    {'key': 'location', 'label': 'Location', 'editor_type': 'text'},
    {'key': 'project_leader', 'label': 'Project Leader', 'editor_type': 'text'},
    {'key': 'test_result', 'label': 'Test Result', 'editor_type': 'dropdown',
     'options': ["In progress", "OK", "Ref", "NG", "In-waiting"]},
    {'key': 'failed_item', 'label': 'Failed item', 'editor_type': 'text'},
    {'key': 'sample_deposition', 'label': 'Sample deposition', 'editor_type': 'text'},
    {'key': 'sub_contract', 'label': 'Sub-contract', 'editor_type': 'dropdown', 'options': ["Yes", "No"]},
    {'key': 'test_fee', 'label': 'Test Fee', 'editor_type': 'text'},
    {'key': 'remarks_po', 'label': 'Remarks (PO)', 'editor_type': 'text'}
]


class LTRFieldConfigLoader:
    """LTR字段配置加载器类"""

    def __init__(self):
        """
        初始化LTR字段配置加载器
        """
        # 获取配置文件路径
        self.config_file_path = self._get_config_file_path()

    def _get_config_file_path(self) -> str:
        """
        获取配置文件路径

        Returns:
            配置文件路径
        """
        # 从配置管理器获取配置文件相对路径
        config_file_relative_path = config_manager.get("ltr.fields_config", "src/app/config/ltr_fields.json")

        # 根据运行环境确定基础路径
        if getattr(sys, 'frozen', False):
            # 在可执行文件环境中，使用可执行文件所在目录作为基础路径
            base_path = os.path.dirname(sys.executable)
        else:
            # 在开发环境中，使用项目根目录作为基础路径
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        # 组合完整路径
        config_file_path = os.path.join(base_path, config_file_relative_path)
        return config_file_path

    def load_application_field_mapping(self) -> List[Dict[str, Any]]:
        """
        从配置文件加载申请单字段映射关系

        Returns:
            字段映射关系列表
        """
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file_path):
                logger.info(f"LTR字段配置文件不存在: {self.config_file_path}，使用内嵌默认配置")
                return DEFAULT_APPLICATION_FIELD_MAPPING.copy()

            # 读取并解析JSON配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            field_mapping = config.get('application_field_mapping', [])

            logger.info(f"成功从 {self.config_file_path} 加载 {len(field_mapping)} 个申请单字段配置")
            return field_mapping

        except json.JSONDecodeError as e:
            logger.error(f"LTR字段配置文件格式错误: {e}，使用内嵌默认配置")
            return DEFAULT_APPLICATION_FIELD_MAPPING.copy()
        except Exception as e:
            logger.error(f"加载LTR申请单字段配置时发生错误: {e}，使用内嵌默认配置")
            return DEFAULT_APPLICATION_FIELD_MAPPING.copy()

    def load_editor_field_mapping(self) -> List[Dict[str, Any]]:
        """
        从配置文件加载编辑器字段映射关系

        Returns:
            字段映射关系列表
        """
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file_path):
                logger.info(f"LTR字段配置文件不存在: {self.config_file_path}，使用内嵌默认配置")
                return DEFAULT_EDITOR_FIELD_MAPPING.copy()

            # 读取并解析JSON配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            field_mapping = config.get('editor_field_mapping', [])

            logger.info(f"成功从 {self.config_file_path} 加载 {len(field_mapping)} 个编辑器字段配置")
            return field_mapping

        except json.JSONDecodeError as e:
            logger.error(f"LTR字段配置文件格式错误: {e}，使用内嵌默认配置")
            return DEFAULT_EDITOR_FIELD_MAPPING.copy()
        except Exception as e:
            logger.error(f"加载LTR编辑器字段配置时发生错误: {e}，使用内嵌默认配置")
            return DEFAULT_EDITOR_FIELD_MAPPING.copy()
