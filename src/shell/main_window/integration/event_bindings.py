"""
Event Binding Manager for MainWindow.

Centralizes event subscription management, separating infrastructure
concerns from business logic in MainWindowController.

设计决策 (2026-04-16 方案A收口):
- StateManager 不再自动派发 state.changed 事件 (纯状态容器)
- 本管理器直接订阅业务领域事件 project.opened
- 所有跨模块通信统一走 event_dispatcher 显式派发

职责范围:
- project.opened → 更新 controller._project_context

不负责:
- LTR events (LTRStatusCoordinator)
- Matrix 自动导入 (ProjectSessionCoordinator)
- application_status (由 controller 直接设置)
"""
from src.core.event_dispatcher import event_dispatcher, EventTopics
from src.core.project_context import ProjectContext
from src.core.logger import logger


class EventBindingManager:
    """
    管理 MainWindow shell 的事件订阅。

    职责：
    - 订阅 shell 级别的领域事件
    - 更新 shell 内部状态（如 controller 的项目上下文引用）

    不处理：
    - project.opened 的副作用编排（由 ProjectSessionCoordinator 负责）
    - LTR 相关事件（由 LTRStatusCoordinator 负责）
    - 业务逻辑实现
    """

    def __init__(self, controller, status_service):
        """
        初始化事件绑定管理器。

        Args:
            controller: MainWindowController 实例，用于更新内部状态
            status_service: 具有 update_status 方法的对象（如 MainWindowData）
        """
        self.controller = controller
        self.status_service = status_service
        self._bound = False

        # 注册清理钩子
        from src.core.shutdown_registry import shutdown_registry
        shutdown_registry.register(
            name="EventBindingManager.unbind_all",
            cleanup_fn=self.unbind_all,
            priority=10  # 高优先级，最先执行
        )

    def bind_all(self) -> None:
        """绑定所有事件订阅。"""
        if self._bound:
            logger.warning("EventBindingManager already bound, skipping")
            return

        self._bind_project_events()

        self._bound = True
        logger.info("EventBindingManager: Bound to project.opened")

    def unbind_all(self) -> None:
        """解绑所有事件订阅（用于清理/测试）。"""
        if not self._bound:
            return

        event_dispatcher.unsubscribe(EventTopics.PROJECT_OPENED, self._on_project_opened)

        self._bound = False
        logger.info("EventBindingManager: All events unbound")

    def _bind_project_events(self) -> None:
        """绑定项目相关领域事件。"""
        event_dispatcher.subscribe(EventTopics.PROJECT_OPENED, self._on_project_opened)

    def _on_project_opened(self, data: dict) -> None:
        """
        处理 project.opened 事件。

        职责：仅更新 controller 内部持有的项目上下文引用。
        副作用编排（窗口标题、Matrix 导入等）由 ProjectSessionCoordinator 负责。

        Args:
            data: 事件数据，包含 project_path、dl_number 等
        """
        logger.info(f"EventBindingManager._on_project_opened: received event")

        try:
            project_context = ProjectContext.from_event_data(data)
            if not project_context:
                logger.warning("EventBindingManager: Invalid project context in event")
                return

            # 更新 controller 内部的项目上下文引用
            if hasattr(self.controller, '_project_context'):
                self.controller._project_context = project_context
                logger.info(
                    f"EventBindingManager: Updated controller "
                    f"project_context={project_context.project_path}"
                )
        except Exception as e:
            logger.error(f"EventBindingManager: Error handling project.opened: {e}")
