"""
事件分发器模块

负责管理事件的订阅、发布和处理。

设计原则:
- 轻量级观察者模式实现，用于组件间解耦通信
- dispatch 在持锁外执行回调（避免死锁）
- 事件名称统一使用 EventTopics 常量（避免拼写错误）
"""

from typing import Dict, List, Callable, Any, Optional
import threading
from src.core.logger import logger


class EventTopics:
    """
    全局事件名称常量注册表。

    所有事件名称集中定义于此，消除散落各处的裸字符串。
    
    使用方式:
        from src.core.event_dispatcher import event_dispatcher, EventTopics
        
        # 发布
        event_dispatcher.dispatch(EventTopics.PROJECT_OPENED, data)
        
        # 订阅
        event_dispatcher.subscribe(EventTopics.PROJECT_OPENED, handler)
    """

    # ========== 项目会话事件 ==========
    PROJECT_OPENED = "project.opened"

    # ========== LTR 申请单事件 ==========
    LTR_APPLICATION_PROCESSED = "ltr.application.processed"
    LTR_APPLICATION_CONFIRMED = "ltr.application.confirmed"

    # ========== LTR 处理流程事件 ==========
    LTR_PROCESSING_STARTED = "ltr.processing.started"
    LTR_PROCESSING_COMPLETED = "ltr.processing.completed"
    LTR_PROCESSING_FAILED = "ltr.processing.failed"

    # ========== 已废弃的事件（保留作为迁移参考）==========
    # STATE_CHANGED = "state.changed"      ← 方案A已移除: StateManager 不再自动派发
    # STATE_REMOVED = "state.removed"       ← 方案A已移除: StateManager 不再自动派发

    @classmethod
    def all_topics(cls) -> List[str]:
        """返回所有已定义的事件名列表（用于调试/文档）。"""
        return [
            attr for attr_name, attr in vars(cls).items()
            if not attr_name.startswith('_') and isinstance(attr, str)
        ]


class EventDispatcher:
    """
    事件分发器 — 线程安全的观察者模式实现。

    核心约束:
    - subscribe/unsubscribe: 持锁操作回调列表 ✅
    - dispatch: 复制列表后释放锁，在锁外执行回调 ✅ （避免死键）
    - 回调异常不中断其他订阅者 ✅
    """

    def __init__(self):
        self._events: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        订阅事件。

        Args:
            event_name: 事件名称 (推荐使用 EventTopics 常量)
            callback: 回调函数，签名为 callback(data: dict) -> None
        """
        with self._lock:
            if event_name not in self._events:
                self._events[event_name] = []
            self._events[event_name].append(callback)
            logger.debug(f"Subscribed to '{event_name}', total: {len(self._events[event_name])}")

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        取消订阅事件。

        Args:
            event_name: 事件名称
            callback: 要移除的回调函数引用（必须与 subscribe 时是同一对象）
        """
        with self._lock:
            if event_name in self._events:
                try:
                    self._events[event_name].remove(callback)
                    logger.debug(f"Unsubscribed from '{event_name}', remaining: {len(self._events[event_name])}")
                except ValueError:
                    logger.debug(f"Callback not found in '{event_name}' subscribers")

    def dispatch(self, event_name: str, data: Optional[dict] = None) -> None:
        """
        分发事件。

        关键设计: 先在锁内复制回调列表到局部变量，
        然后在锁外遍历执行。避免回调内再次调用
        subscribe/dispatch 导致的死锁。

        Args:
            event_name: 事件名称 (推荐使用 EventTopics 常量)
            data: 事件数据字典，传递给每个订阅者
        """
        if data is None:
            data = {}

        logger.debug(f"Dispatching '{event_name}'")

        # 锁内复制，立即释放
        with self._lock:
            listeners = self._events.get(event_name, [])[:]

        # 锁外执行回调
        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback for '{event_name}': {e}", exc_info=True)

    def get_subscribers_count(self, event_name: str) -> int:
        """获取指定事件的订阅者数量（调试/测试用）。"""
        with self._lock:
            return len(self._events.get(event_name, []))

    def get_all_event_names(self) -> List[str]:
        """获取所有已注册事件名（调试/文档用）。"""
        with self._lock:
            return list(self._events.keys())


# 全局事件分发器实例
event_dispatcher = EventDispatcher()
