"""
页眉数据模型模块
定义页眉信息的数据结构
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HeaderData:
    """
    页眉数据模型
    存储报告页眉所需的信息
    """
    report_no: str = ""
    version: str = "Rev.A"
    date: str = ""
    tester: str = ""
    report_title: str = ""
    requested_by: str = ""
    test_period: str = ""
    completion_date: str = ""

    @classmethod
    def from_json(cls, json_data: dict) -> 'HeaderData':
        """
        从JSON数据创建HeaderData实例
        
        Args:
            json_data: 包含页眉信息的字典
            
        Returns:
            HeaderData实例
        """
        return cls(
            report_no=json_data.get("DL", ""),
            version=json_data.get("version", "1.0"),
            date=json_data.get("report_date", ""),
            tester=json_data.get("project_leader", ""),
            report_title=f"{json_data.get('product_description', '')} {json_data.get('tests_to_be_performed', '')}".strip(),
            requested_by=json_data.get("requested_by", ""),
            test_period=""
        )

    def to_dict(self) -> dict:
        """
        将HeaderData实例转换为字典
        
        Returns:
            包含页眉信息的字典
        """
        return {
            "report_no": self.report_no,
            "version": self.version,
            "date": self.date,
            "tester": self.tester,
            "report_title": self.report_title,
            "requested_by": self.requested_by,
            "test_period": self.test_period
        }