"""
日期工具模块
提供日期处理相关的工具函数
"""

from datetime import datetime, date, timedelta
from typing import Optional
from src.core.logger import logger


def get_current_datetime(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前日期时间字符串

    Args:
        format_str: 日期时间格式

    Returns:
        格式化后的当前日期时间字符串
    """
    return datetime.now().strftime(format_str)


def get_current_date(format_str: str = "%Y-%m-%d") -> str:
    """
    获取当前日期字符串

    Args:
        format_str: 日期格式

    Returns:
        格式化后的当前日期字符串
    """
    return date.today().strftime(format_str)


def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[date]:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串
        format_str: 日期格式

    Returns:
        解析后的日期对象，如果解析失败则返回None
    """
    try:
        return datetime.strptime(date_str, format_str).date()
    except Exception as e:
        logger.error(f"Failed to parse date '{date_str}' with format '{format_str}': {e}")
        return None


def format_date(date_obj: date, format_str: str = "%Y-%m-%d") -> str:
    """
    格式化日期对象

    Args:
        date_obj: 日期对象
        format_str: 日期格式

    Returns:
        格式化后的日期字符串
    """
    return date_obj.strftime(format_str)


def add_days(date_obj: date, days: int) -> date:
    """
    给日期对象增加指定天数

    Args:
        date_obj: 日期对象
        days: 要增加的天数（可以为负数）

    Returns:
        增加天数后的日期对象
    """
    return date_obj + timedelta(days=days)


def get_days_difference(date1: date, date2: date) -> int:
    """
    计算两个日期之间的天数差

    Args:
        date1: 第一个日期
        date2: 第二个日期

    Returns:
        天数差（date2 - date1）
    """
    return (date2 - date1).days


def is_weekend(date_obj: date) -> bool:
    """
    检查日期是否为周末

    Args:
        date_obj: 日期对象

    Returns:
        如果是周末则返回True，否则返回False
    """
    return date_obj.weekday() >= 5  # 5=Saturday, 6=Sunday


def get_month_first_day(date_obj: date) -> date:
    """
    获取指定日期所在月份的第一天

    Args:
        date_obj: 日期对象

    Returns:
        月份第一天的日期对象
    """
    return date_obj.replace(day=1)


def get_month_last_day(date_obj: date) -> date:
    """
    获取指定日期所在月份的最后一天

    Args:
        date_obj: 日期对象

    Returns:
        月份最后一天的日期对象
    """
    if date_obj.month == 12:
        next_month = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
    else:
        next_month = date_obj.replace(month=date_obj.month + 1, day=1)
    return next_month - timedelta(days=1)
