"""
LTR编辑器数据模型模块
定义LTR编辑器相关的数据结构
"""

from typing import Optional, Dict, Any, List
from src.core.logger import logger


class LTREditorData:
    """
    LTR编辑器数据模型类
    管理LTR编辑器中的数据
    """

    def __init__(self):
        self.dl_number: str = ""
        self.original_data: Dict[str, Any] = {}
        self.modified_data: Dict[str, Any] = {}

        # 字段映射关系，定义字段类型和下拉选项
        self.field_mapping: List[Dict[str, Any]] = [
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

    def set_dl_number(self, dl_number: str) -> None:
        """
        设置DL编号

        Args:
            dl_number: DL编号
        """
        self.dl_number = dl_number
        logger.debug(f"DL number set to: {dl_number}")

    def get_dl_number(self) -> str:
        """
        获取DL编号

        Returns:
            DL编号
        """
        return self.dl_number

    def set_original_data(self, data: Dict[str, Any]) -> None:
        """
        设置原始数据

        Args:
            data: 原始数据字典
        """
        self.original_data = data
        self.modified_data = data.copy()
        logger.debug("Original data set")

    def get_original_data(self) -> Dict[str, Any]:
        """
        获取原始数据

        Returns:
            原始数据字典
        """
        return self.original_data.copy()

    def set_modified_data(self, data: Dict[str, Any]) -> None:
        """
        设置修改后的数据

        Args:
            data: 修改后的数据字典
        """
        self.modified_data = data
        logger.debug("Modified data set")

    def get_modified_data(self) -> Dict[str, Any]:
        """
        获取修改后的数据

        Returns:
            修改后的数据字典
        """
        return self.modified_data.copy()

    def get_field_mapping(self) -> List[Dict[str, Any]]:
        """
        获取字段映射关系

        Returns:
            字段映射关系列表
        """
        return self.field_mapping.copy()

    def get_field_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        根据键名获取字段信息

        Args:
            key: 字段键名

        Returns:
            字段信息字典，如果未找到则返回None
        """
        for field in self.field_mapping:
            if field['key'] == key:
                return field
        return None

    def get_field_by_label(self, label: str) -> Optional[Dict[str, Any]]:
        """
        根据标签获取字段信息

        Args:
            label: 字段标签

        Returns:
            字段信息字典，如果未找到则返回None
        """
        for field in self.field_mapping:
            if field['label'] == label:
                return field
        return None
