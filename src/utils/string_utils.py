"""
字符串工具模块
提供字符串处理相关的工具函数
"""

import re
from typing import List, Optional
from src.core.logger import logger


def is_empty_or_whitespace(text: Optional[str]) -> bool:
    """
    检查字符串是否为空或只包含空白字符

    Args:
        text: 要检查的字符串

    Returns:
        如果字符串为空或只包含空白字符则返回True，否则返回False
    """
    return text is None or text.strip() == ""


def remove_whitespace(text: str) -> str:
    """
    移除字符串中的所有空白字符

    Args:
        text: 输入字符串

    Returns:
        移除空白字符后的字符串
    """
    return re.sub(r'\s+', '', text)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串到指定长度

    Args:
        text: 输入字符串
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length - len(suffix)] + suffix


def split_string_by_multiple_separators(text: str, separators: List[str]) -> List[str]:
    """
    使用多个分隔符分割字符串

    Args:
        text: 输入字符串
        separators: 分隔符列表

    Returns:
        分割后的字符串列表
    """
    try:
        # 构建正则表达式模式
        pattern = '|'.join(re.escape(sep) for sep in separators)
        return re.split(pattern, text)
    except Exception as e:
        logger.error(f"Failed to split string by multiple separators: {e}")
        return [text]


def is_valid_email(email: str) -> bool:
    """
    检查字符串是否为有效的电子邮件地址

    Args:
        email: 电子邮件地址

    Returns:
        如果是有效的电子邮件地址则返回True，否则返回False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_phone_number(phone: str) -> bool:
    """
    检查字符串是否为有效的电话号码（中国手机号）

    Args:
        phone: 电话号码

    Returns:
        如果是有效的电话号码则返回True，否则返回False
    """
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None


def capitalize_words(text: str) -> str:
    """
    将字符串中每个单词的首字母大写

    Args:
        text: 输入字符串

    Returns:
        处理后的字符串
    """
    return ' '.join(word.capitalize() for word in text.split())


def snake_to_camel(snake_str: str) -> str:
    """
    将蛇形命名转换为驼峰命名

    Args:
        snake_str: 蛇形命名字符串

    Returns:
        驼峰命名字符串
    """
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    将驼峰命名转换为蛇形命名

    Args:
        camel_str: 驼峰命名字符串

    Returns:
        蛇形命名字符串
    """
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', camel_str).lower()


def normalize_text(text: str) -> str:
    """
    规范化文本，去除前后空格和非字母符号

    Args:
        text: 原始文本

    Returns:
        规范化后的文本
    """
    if not text:
        return ""
    # 去除前后空格
    text = text.strip()
    # 去除非字母符号（保留字母、数字、空格）
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # 去除多余空格
    text = ' '.join(text.split())
    return text