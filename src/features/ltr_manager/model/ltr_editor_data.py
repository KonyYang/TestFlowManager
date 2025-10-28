"""
LTR编辑器数据模型模块
定义LTR编辑器处理过程中使用的数据结构和字段映射
"""

from typing import List, Dict, Any, Optional
from src.features.ltr_manager.utils.field_config_loader import LTRFieldConfigLoader


class LTREditorData:
    """
    LTR编辑器数据模型类
    用于存储和管理LTR编辑器的数据
    """

    def __init__(self):
        """
        初始化LTR编辑器数据模型
        """
        self.dl_number: str = ""
        self.original_data: Dict[str, Any] = {}
        self.modified_data: Dict[str, Any] = {}

        # 从配置文件加载字段映射关系
        config_loader = LTRFieldConfigLoader()
        self.field_mapping: List[Dict[str, Any]] = config_loader.load_editor_field_mapping()
        
        # 如果字段映射为空，记录警告信息
        if not self.field_mapping:
            from src.core.logger import logger
            logger.warning("LTR编辑器字段映射为空，可能配置文件加载失败")

    def set_dl_number(self, dl_number: str):
        """
        设置DL编号

        Args:
            dl_number: DL编号
        """
        self.dl_number = dl_number

    def set_original_data(self, data: Dict[str, Any]):
        """
        设置原始数据

        Args:
            data: 原始数据字典
        """
        self.original_data = data.copy()

    def set_modified_data(self, data: Dict[str, Any]):
        """
        设置修改后的数据

        Args:
            data: 修改后的数据字典
        """
        self.modified_data = data.copy()

    def get_dl_number(self) -> str:
        """
        获取DL编号

        Returns:
            DL编号
        """
        return self.dl_number

    def get_original_data(self) -> Dict[str, Any]:
        """
        获取原始数据

        Returns:
            原始数据字典
        """
        return self.original_data.copy()

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
        return self.field_mapping

    def get_field_by_label(self, label: str) -> Optional[Dict[str, Any]]:
        """
        根据字段标签获取字段信息

        Args:
            label: 字段标签

        Returns:
            字段信息字典，如果未找到则返回None
        """
        for field_info in self.field_mapping:
            if field_info.get('label') == label:
                return field_info
        return None

    def get_field_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        根据字段键获取字段信息

        Args:
            key: 字段键

        Returns:
            字段信息字典，如果未找到则返回None
        """
        for field_info in self.field_mapping:
            if field_info.get('key') == key:
                return field_info
        return None