"""
核心模块 — 纯基础设施层

只包含零业务耦合的基础设施组件：
|- 配置管理 (config_manager)
|- 日志系统 (logger)
|- 事件总线 (event_dispatcher + EventTopics)
|- 状态容器 (state_manager)
|- 生命周期管理 (shutdown_registry)
|- 缓存体系 (cache/)
|- 数据缓存 (data_cache)
|- 项目上下文值对象 (project_context)
|- 服务基类 (base_service)
|- 会话服务编排 (project_session服务)
"""

from .config_manager import config_manager
from .event_dispatcher import event_dispatcher
from .logger import logger
from .state_manager import state_manager

__all__ = [
    "config_manager",
    "event_dispatcher",
    "logger",
    "state_manager",
]
