"""
Event Binding Manager for MainWindow.

Centralizes event subscription management, separating infrastructure
concerns from business logic in MainWindowController.

NOTE: This manager only handles 1 event now:
- state.changed - handles application_status directly

project.opened is consumed directly by ProjectSessionCoordinator (event decoupling).

All LTR-related events are handled by LTRStatusCoordinator.
"""
from src.core.event_dispatcher import event_dispatcher
from src.core.project_context import ProjectContext
from src.core.logger import logger


class EventBindingManager:
    """
    Manages event subscriptions for MainWindow shell.
    
    Responsibilities:
    - Subscribe to shell-level state changes only
    - Update shell internal state
    
    Does NOT handle:
    - project.opened (handled by ProjectSessionCoordinator directly)
    - LTR events (handled by LTRStatusCoordinator)
    - Business logic implementation
    """
    
    def __init__(self, controller, status_service):
        """
        Initialize event binding manager.
        
        Args:
            controller: MainWindowController instance for internal state updates
            status_service: Object with update_status method (e.g., MainWindowData)
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
        """Bind all event subscriptions."""
        if self._bound:
            logger.warning("EventBindingManager already bound, skipping")
            return
            
        self._bind_shell_state_events()
        
        self._bound = True
        logger.info("EventBindingManager: Bound to state.changed only (project.opened moved to coordinator)")
        
    def unbind_all(self) -> None:
        """Unbind all event subscriptions (for cleanup/testing)."""
        if not self._bound:
            return
            
        event_dispatcher.unsubscribe("state.changed", self._on_state_changed)
        
        self._bound = False
        logger.info("EventBindingManager: All events unbound")
        
    def _bind_shell_state_events(self) -> None:
        """Bind shell-level state change events."""
        event_dispatcher.subscribe("state.changed", self._on_state_changed)
            
    def _on_state_changed(self, data: dict) -> None:
        """
        Handle state changed event.
        
        Args:
            data: Event data containing key and new_value
        """
        key = data.get("key")
        
        if key == "application_status":
            # Direct status update
            new_value = data.get("new_value")
            self.status_service.update_status(new_value)
            logger.debug("EventBindingManager: application_status updated")
            
        elif key == "current_project_context":
            # Update controller internal state
            new_value = data.get("new_value")
            if hasattr(self.controller, '_project_context'):
                self.controller._project_context = new_value
                logger.debug(f"EventBindingManager: Updated controller project context")
            
        else:
            logger.debug(f"EventBindingManager: Ignored state key: {key}")
