"""
事件分发器模块
负责管理事件的订阅、发布和处理
"""

from typing import Dict, List, Callable, Any
import threading
from src.core.logger import logger


class EventDispatcher:
    """
    事件分发器类
    实现观察者模式，用于组件间的解耦通信
    """

    def __init__(self):
        self._events: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        订阅事件

        Args:
            event_name: 事件名称
            callback: 回调函数
        """
        with self._lock:
            if event_name not in self._events:
                self._events[event_name] = []
            self._events[event_name].append(callback)
            # logger.debug(f"Subscribed to event '{event_name}', total subscribers: {len(self._events[event_name])}")

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        取消订阅事件

        Args:
            event_name: 事件名称
            callback: 回调函数
        """
        with self._lock:
            if event_name in self._events:
                try:
                    self._events[event_name].remove(callback)
                    logger.debug(f"Unsubscribed from event '{event_name}', remaining subscribers: {len(self._events[event_name])}")
                except ValueError:
                    logger.debug(f"Callback not found in event '{event_name}' subscribers")
                    pass  # 回调函数不在列表中

    def dispatch(self, event_name: str, *args, **kwargs) -> None:
        """
        分发事件

        Args:
            event_name: 事件名称
            *args: 传递给回调函数的位置参数
            **kwargs: 传递给回调函数的关键字参数
        """
        logger.debug(f"Dispatching event '{event_name}' with args: {args}, kwargs: {kwargs}")
        with self._lock:
            if event_name in self._events:
                for callback in self._events[event_name][:]:  # 使用副本防止在回调中修改列表
                    try:
                        callback(*args, **kwargs)
                    except Exception as e:
                        logger.error(f"Error in event callback for {event_name}: {e}")


# 全局事件分发器实例
event_dispatcher = EventDispatcher()