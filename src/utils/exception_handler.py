"""
异常处理工具模块
提供统一的异常处理和转换功能
"""

import traceback
from typing import Any, Callable, Optional
from PyQt5.QtWidgets import QMessageBox

from src.core.logger import logger


def handle_exception(exception: Exception, 
                    context: str = "", 
                    parent=None,
                    show_msgbox: bool = True) -> dict:
    """
    统一异常处理函数
    
    Args:
        exception: 捕获的异常
        context: 异常上下文信息
        parent: 父窗口（用于显示消息框）
        show_msgbox: 是否显示消息框
        
    Returns:
        包含错误信息的字典
    """
    # 记录详细日志
    error_msg = f"{context}: {str(exception)}" if context else str(exception)
    logger.error(error_msg)
    logger.error(f"异常详情:\n{traceback.format_exc()}")
    
    # 准备返回的错误信息
    error_info = {
        "success": False,
        "error": error_msg,
        "exception_type": type(exception).__name__
    }
    
    # 显示错误消息框
    if show_msgbox and parent:
        QMessageBox.critical(parent, "错误", error_msg)
    
    return error_info


def safe_execute(func: Callable, 
                *args, 
                context: str = "",
                parent=None,
                default_return=None,
                **kwargs) -> Any:
    """
    安全执行函数，捕获并处理异常
    
    Args:
        func: 要执行的函数
        args: 函数位置参数
        context: 执行上下文信息
        parent: 父窗口（用于显示消息框）
        default_return: 默认返回值
        kwargs: 函数关键字参数
        
    Returns:
        函数执行结果或默认返回值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = handle_exception(e, context, parent)
        logger.error(f"函数 {func.__name__} 执行失败: {error_info}")
        return default_return


def show_warning(parent, title: str, message: str) -> None:
    """
    显示警告消息框
    
    Args:
        parent: 父窗口
        title: 标题
        message: 消息内容
    """
    logger.warning(f"警告 [{title}]: {message}")
    QMessageBox.warning(parent, title, message)


def show_info(parent, title: str, message: str) -> None:
    """
    显示信息消息框
    
    Args:
        parent: 父窗口
        title: 标题
        message: 消息内容
    """
    logger.info(f"信息 [{title}]: {message}")
    QMessageBox.information(parent, title, message)