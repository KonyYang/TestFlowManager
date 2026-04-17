"""
状态管理器模块
负责管理应用程序的状态 (纯状态容器)

设计决策 (2026-04-16 方案A收口):
- StateManager 只负责状态的读写存储
- 不再自动派发事件或维护监听器列表
- 所有跨模块通信统一由业务层通过 event_dispatcher 显式派发
- 原因: 消除与 event_dispatcher 的隐式双通道问题
"""

from typing import Dict, Any
import threading

from src.core.logger import logger


class StateManager:
    """
    状态管理器类 — 纯状态容器

    职责:
    - 状态值的存取 (set/get/remove/clear)
    
    不再负责:
    - 事件派发 (已移至业务层显式 dispatch)
    - 监听器管理 (无人使用, 已删除)
    """

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def set_state(self, key: str, value: Any) -> None:
        """
        设置状态值 (纯存储，不派发事件)

        Args:
            key: 状态键名
            value: 状态值
        """
        with self._lock:
            self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        获取状态值

        Args:
            key: 状态键名
            default: 默认值

        Returns:
            状态值或默认值
        """
        with self._lock:
            return self._state.get(key, default)

    def remove_state(self, key: str) -> None:
        """
        移除状态值 (纯删除，不派发事件)

        Args:
            key: 状态键名
        """
        with self._lock:
            if key in self._state:
                del self._state[key]

    def get_all_state(self) -> Dict[str, Any]:
        """
        获取所有状态

        Returns:
            包含所有状态的字典 (副本)
        """
        with self._lock:
            return self._state.copy()

    def clear(self) -> None:
        """清空所有状态"""
        with self._lock:
            self._state.clear()


# 全局状态管理器实例
state_manager = StateManager()
