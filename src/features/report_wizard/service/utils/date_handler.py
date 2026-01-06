"""
日期处理工具模块
提供日期解析和格式化相关的功能
"""

from typing import Optional
from datetime import datetime
from src.core.logger import logger


class DateHandler:
    """
    日期处理器
    提供日期解析和格式化相关的功能
    """

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        解析多种格式的日期字符串
        :param date_str: 日期字符串
        :return: 解析后的datetime对象，如果解析失败则返回None
        """
        if not date_str:
            return None

        date_formats = [
            "%Y-%m-%d",         # 2024-12-01
            "%d %b %Y",         # 01 Dec 2024
            "%d %B %Y",         # 01 December 2024
            "%b %d, %Y",        # Dec 01, 2024
            "%m/%d/%Y",         # 12/01/2024
            "%Y/%m/%d",         # 2024/12/01
            "%d-%b-%Y",         # 31-Oct-2024
            "%d/%m/%Y",         # 31/10/2024
            "%d.%m.%Y",         # 31.10.2024
            "%d/%b/%Y",         # 01/Jan/2026
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def format_date_to_standard(date_str: str) -> str:
        """
        将日期字符串解析为标准格式 (dd/MMM/YYYY，如 31/Oct/2024)
        
        :param date_str: 输入的日期字符串
        :return: 格式化后的日期字符串
        """
        parsed_date = DateHandler.parse_date(date_str)
        if parsed_date:
            return parsed_date.strftime("%d/%b/%Y")  # 输出格式：31/Oct/2024
        return date_str  # 如果解析失败，返回原始字符串

    @staticmethod
    def format_date_to_month_day_year(date_str: str) -> str:
        """
        将日期字符串格式化为 "MMM dd, yyyy" 格式 (例如 "Dec 20, 2024")
        :param date_str: 输入的日期字符串
        :return: 格式化后的日期字符串
        """
        logger.debug(f"format_date_to_month_day_year: 输入日期字符串 = '{date_str}'")
        parsed_date = DateHandler.parse_date(date_str)
        if parsed_date:
            formatted = parsed_date.strftime("%b %d, %Y")  # 输出格式：Dec 20, 2024
            logger.debug(f"format_date_to_month_day_year: 解析成功，返回格式化日期 = '{formatted}'")
            return formatted
        logger.debug(f"format_date_to_month_day_year: 解析失败，返回原始日期字符串 = '{date_str}'")
        return date_str