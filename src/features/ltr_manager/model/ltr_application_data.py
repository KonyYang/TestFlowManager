"""
LTR申请单数据模型模块
定义LTR申请单处理过程中使用的数据结构
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class LTRApplicationData:
    """
    LTR申请单数据模型
    用于存储和传递LTR申请单处理过程中的数据
    """

    # 申请单基本信息
    dl_number: str = ""
    requested_by: str = ""
    location: str = ""
    phone: str = ""
    email_requestor: str = ""

    # 日期信息
    date_lab_received_samples: str = ""
    estimated_completion_date: str = ""
    start_test_date: str = ""
    finish_test_date: str = ""
    report_date: str = ""

    # 项目信息
    project_type: str = ""
    test_type: str = ""
    sub_contract: str = ""

    # 测试信息
    sample_information: str = ""
    tests_to_be_performed: str = ""
    applicable_specifications: str = ""
    
    # 样品详细信息
    product_name: str = ""       # 产品名称
    part_number: str = ""        # 料号
    lot_info: str = ""           # 批次
    base_material: str = ""      # 基材
    contact_plating: str = ""    # 接触镀层
    contact_lubricant: str = ""  # 润滑油
    housing_material: str = ""   # 塑材

    # 其他信息
    project_leader: str = ""
    failed_item: str = ""
    sample_deposition: str = ""
    test_fee: str = ""
    remarks_po: str = ""

    # 系统信息
    file_path: str = ""
    status: str = "new"  # new, processing, completed, failed
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        将对象转换为字典格式

        Returns:
            包含所有字段的字典
        """
        return {
            'dl_number': self.dl_number,
            'requested_by': self.requested_by,
            'location': self.location,
            'phone': self.phone,
            'email_requestor': self.email_requestor,
            'date_lab_received_samples': self.date_lab_received_samples,
            'estimated_completion_date': self.estimated_completion_date,
            'start_test_date': self.start_test_date,
            'finish_test_date': self.finish_test_date,
            'report_date': self.report_date,
            'project_type': self.project_type,
            'test_type': self.test_type,
            'sub_contract': self.sub_contract,
            'sample_information': self.sample_information,
            'tests_to_be_performed': self.tests_to_be_performed,
            'applicable_specifications': self.applicable_specifications,
            'product_name': self.product_name,              # 产品名称
            'part_number': self.part_number,                # 料号
            'lot_info': self.lot_info,                      # 批次
            'base_material': self.base_material,            # 基材
            'contact_plating': self.contact_plating,        # 接触镀层
            'contact_lubricant': self.contact_lubricant,    # 润滑油
            'housing_material': self.housing_material,      # 塑材
            'project_leader': self.project_leader,
            'failed_item': self.failed_item,
            'sample_deposition': self.sample_deposition,
            'test_fee': self.test_fee,
            'remarks_po': self.remarks_po,
            'file_path': self.file_path,
            'status': self.status,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LTRApplicationData':
        """
        从字典创建LTRApplicationData对象

        Args:
            data: 包含字段数据的字典

        Returns:
            LTRApplicationData对象
        """
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
