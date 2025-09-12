"""
状态管理器模块
负责管理应用程序的状态
"""

from typing import Dict, Any, Optional, Callable, List
import json
import threading


class StateManager:
    """
    状态管理器类
    管理应用程序的各种状态，支持状态监听和持久化
    """

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def set_state(self, key: str, value: Any) -> None:
        """
        设置状态值

        Args:
            key: 状态键名
            value: 状态值
        """
        with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value

            # 通知监听器
            if key in self._listeners:
                for listener in self._listeners[key][:]:
                    try:
                        listener(key, old_value, value)
                    except Exception as e:
                        print(f"Error in state listener for {key}: {e}")

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
        移除状态值

        Args:
            key: 状态键名
        """
        with self._lock:
            if key in self._state:
                del self._state[key]

    def add_listener(self, key: str, listener: Callable) -> None:
        """
        添加状态监听器

        Args:
            key: 状态键名
            listener: 监听器回调函数，接收(key, old_value, new_value)参数
        """
        with self._lock:
            if key not in self._listeners:
                self._listeners[key] = []
            self._listeners[key].append(listener)

    def remove_listener(self, key: str, listener: Callable) -> None:
        """
        移除状态监听器

        Args:
            key: 状态键名
            listener: 监听器回调函数
        """
        with self._lock:
            if key in self._listeners:
                try:
                    self._listeners[key].remove(listener)
                except ValueError:
                    pass  # 监听器不在列表中

    def get_all_state(self) -> Dict[str, Any]:
        """
        获取所有状态

        Returns:
            包含所有状态的字典
        """
        with self._lock:
            return self._state.copy()

    def clear(self) -> None:
        """清空所有状态"""
        with self._lock:
            self._state.clear()
            self._listeners.clear()


# 全局状态管理器实例
state_manager = StateManager()
