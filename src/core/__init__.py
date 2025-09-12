"""
核心模块初始化文件
"""

# 导入核心组件，方便其他模块使用
from .logger import logger
from .config_manager import config_manager
from .event_dispatcher import event_dispatcher
from .state_manager import state_manager

__all__ = ['logger', 'config_manager', 'event_dispatcher', 'state_manager']
