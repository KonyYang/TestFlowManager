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
    version: str = "A"
    date: str = ""  # 用于存储 report_date
    tester: str = ""
    report_title: str = ""
    requested_by: str = ""
    test_period: str = ""

    # 新增字段来存储具体的日期
    start_test_date: str = ""  # 用于存储 start_test_date
    finish_test_date: str = ""  # 用于存储 finish_test_date
    report_date: str = ""  # 用于存储 report_date

    @classmethod
    def from_json(cls, json_data: dict) -> 'HeaderData':
        """
        从JSON数据创建HeaderData实例

        Args:
            json_data: 包含页眉信息的字典

        Returns:
            HeaderData实例
        """
        # 从JSON数据中获取各个字段
        report_no = json_data.get("DL", "")
        version = json_data.get("version", "A")
        tester = json_data.get("project_leader", "")
        product_description = json_data.get("product_description", "")
        tests_to_be_performed = json_data.get("tests_to_be_performed", "")
        requested_by = json_data.get("requested_by", "")

        # 获取日期字段
        start_test_date = json_data.get("start_test_date", "")
        finish_test_date = json_data.get("finish_test_date", "")
        report_date = json_data.get("report_date", "")

        # 创建测试周期字符串（如果提供了开始和结束日期）
        test_period = ""
        if start_test_date and finish_test_date:
            test_period = f"{start_test_date}-{finish_test_date}"

        # 创建HeaderData实例
        return cls(
            report_no=report_no,
            version=version,
            date=report_date,  # 使用 report_date 字段作为date字段
            tester=tester,
            report_title=f"{product_description} {tests_to_be_performed}".strip(),
            requested_by=requested_by,
            test_period=test_period,
            report_date=report_date,  # 使用 report_date 字段作为report_date字段
            start_test_date=start_test_date,  # 使用从JSON获取的start_test_date字段
            finish_test_date=finish_test_date,  # 使用从JSON获取的finish_test_date字段
        )

    def increment_version(self):
        """
        递增版本号，按字母顺序 A -> B -> C -> ... -> Z -> AA -> AB -> ...
        """
        current_version = self.version.upper()
        if not current_version:
            self.version = "A"
            return

        # 将当前版本号转换为下一个字母
        next_version = self._get_next_version(current_version)
        self.version = next_version

    def _get_next_version(self, current_version: str) -> str:
        """
        获取下一个版本号
        
        Args:
            current_version: 当前版本号
            
        Returns:
            下一个版本号
        """
        # 将字母转换为数字进行计算
        num = 0
        for char in current_version:
            if 'A' <= char <= 'Z':
                num = num * 26 + (ord(char) - ord('A') + 1)
        
        # 递增数字
        num += 1
        
        # 将数字转换回字母
        if num <= 0:
            return "A"
        
        result = ""
        while num > 0:
            num -= 1  # 调整为0基索引
            result = chr(ord('A') + num % 26) + result
            num //= 26
        
        return result

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
            "test_period": self.test_period,
            "start_test_date": self.start_test_date,
            "finish_test_date": self.finish_test_date,
            "report_date": self.report_date
        }