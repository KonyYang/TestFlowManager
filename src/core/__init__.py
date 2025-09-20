"""
核心模块
包含应用程序的核心功能
"""

from .config_manager import config_manager
from .event_dispatcher import event_dispatcher
from .logger import logger
from .state_manager import state_manager
from .font_utils import FontUtils
from .base_controller import BaseController

__all__ = [
    "config_manager",
    "event_dispatcher",
    "logger",
    "state_manager",
    "FontUtils",
    "BaseController"
]
