"""
LTR数据模型模块
定义LTR相关的数据结构
"""

from typing import Optional, List
from src.core.logger import logger


class LTRViewerData:
    """
    LTR数据模型类
    管理LTR文件相关的数据
    """

    def __init__(self):
        self.file_path: str = ""
        self.current_sheet: str = ""
        self.last_valid_row: int = 0
        self.available_sheets: List[str] = []
        # 新增属性用于DL编号查找功能
        self.found_row: Optional[int] = None
        self.found_worksheet = None
        self.dl_number: Optional[str] = None

    def set_file_path(self, file_path: str) -> None:
        """
        设置文件路径

        Args:
            file_path: LTR文件路径
        """
        self.file_path = file_path
        logger.debug(f"LTR file path set to: {file_path}")

    def get_file_path(self) -> str:
        """
        获取文件路径

        Returns:
            LTR文件路径
        """
        return self.file_path

    def set_current_sheet(self, sheet_name: str) -> None:
        """
        设置当前工作表

        Args:
            sheet_name: 工作表名称
        """
        self.current_sheet = sheet_name
        logger.debug(f"Current sheet set to: {sheet_name}")

    def get_current_sheet(self) -> str:
        """
        获取当前工作表

        Returns:
            当前工作表名称
        """
        return self.current_sheet

    def set_last_valid_row(self, row_number: int) -> None:
        """
        设置最后一个有效行

        Args:
            row_number: 行号
        """
        self.last_valid_row = row_number
        logger.debug(f"Last valid row set to: {row_number}")

    def get_last_valid_row(self) -> int:
        """
        获取最后一个有效行

        Returns:
            最后一个有效行的行号
        """
        return self.last_valid_row

    def set_available_sheets(self, sheets: List[str]) -> None:
        """
        设置可用工作表列表

        Args:
            sheets: 工作表名称列表
        """
        self.available_sheets = sheets
        logger.debug(f"Available sheets set: {sheets}")

    def get_available_sheets(self) -> List[str]:
        """
        获取可用工作表列表

        Returns:
            工作表名称列表
        """
        return self.available_sheets.copy()

    # 新增方法用于DL编号查找功能
    def set_found_row(self, row: Optional[int]) -> None:
        """
        设置找到的行号

        Args:
            row: 找到的行号
        """
        self.found_row = row
        logger.debug(f"Found row set to: {row}")

    def get_found_row(self) -> Optional[int]:
        """
        获取找到的行号

        Returns:
            找到的行号
        """
        return self.found_row

    def set_found_worksheet(self, worksheet) -> None:
        """
        设置找到的工作表

        Args:
            worksheet: 找到的工作表对象
        """
        self.found_worksheet = worksheet
        logger.debug("Found worksheet set")

    def get_found_worksheet(self):
        """
        获取找到的工作表

        Returns:
            找到的工作表对象
        """
        return self.found_worksheet

    def set_dl_number(self, dl_number: Optional[str]) -> None:
        """
        设置DL编号

        Args:
            dl_number: DL编号
        """
        self.dl_number = dl_number
        logger.debug(f"DL number set to: {dl_number}")

    def get_dl_number(self) -> Optional[str]:
        """
        获取DL编号

        Returns:
            DL编号
        """
        return self.dl_number
