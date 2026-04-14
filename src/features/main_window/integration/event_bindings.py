"""
Event Binding Manager for MainWindow.

Centralizes event subscription management, separating infrastructure
concerns from business logic in MainWindowController.

NOTE: This manager only handles 2 events:
1. project.opened - forwards to ProjectSessionCoordinator via controller
2. state.changed - handles application_status directly

All LTR-related events are handled by LTRStatusCoordinator.
"""
from src.core.event_dispatcher import event_dispatcher
from src.core.project_context import ProjectContext
from src.core.logger import logger


class EventBindingManager:
    """
    Manages event subscriptions for MainWindow shell.
    
    Responsibilities:
    - Subscribe to shell-relevant events only (project.opened, state.changed)
    - Log event reception
    - Delegate to appropriate handlers
    
    Does NOT handle:
    - LTR events (handled by LTRStatusCoordinator)
    - Business logic implementation
    """
    
    def __init__(self, controller, status_service):
        """
        Initialize event binding manager.
        
        Args:
            controller: MainWindowController instance for delegation
            status_service: Service for status bar updates
        """
        self.controller = controller
        self.status_service = status_service
        self._bound = False
        
    def bind_all(self) -> None:
        """Bind all event subscriptions."""
        if self._bound:
            logger.warning("EventBindingManager already bound, skipping")
            return
            
        self._bind_project_events()
        self._bind_shell_state_events()
        
        self._bound = True
        logger.info("EventBindingManager: Bound to project.opened and state.changed")
        
    def unbind_all(self) -> None:
        """Unbind all event subscriptions (for cleanup/testing)."""
        if not self._bound:
            return
            
        event_dispatcher.unsubscribe("project.opened", self._on_project_opened)
        event_dispatcher.unsubscribe("state.changed", self._on_state_changed)
        
        self._bound = False
        logger.info("EventBindingManager: All events unbound")
        
    def _bind_project_events(self) -> None:
        """Bind project lifecycle events."""
        event_dispatcher.subscribe("project.opened", self._on_project_opened)
        
    def _bind_shell_state_events(self) -> None:
        """Bind shell-level state change events."""
        event_dispatcher.subscribe("state.changed", self._on_state_changed)
        
    def _on_project_opened(self, data: dict) -> None:
        """
        Handle project opened event - lightweight forwarding.
        
        Args:
            data: Event data containing project_path and dl_number
        """
        context = ProjectContext.from_event_data(data)
        dl_number = context.dl_number if context else data.get("dl_number")
        
        logger.debug(f"EventBindingManager: project.opened - {dl_number}")
        
        # Delegate to controller's _on_project_opened (which uses ProjectSessionCoordinator)
        self.controller._on_project_opened(data)
            
    def _on_state_changed(self, data: dict) -> None:
        """
        Handle state changed event - split handling.
        
        Args:
            data: Event data containing key and new_value
        """
        key = data.get("key")
        
        if key == "application_status":
            # Direct status update (no controller involvement needed)
            new_value = data.get("new_value")
            self.status_service.update_status(new_value)
            logger.debug("EventBindingManager: application_status updated")
            
        elif key == "current_project_context":
            # Delegate to controller for internal state management
            self.controller._on_state_changed(data)
            
        else:
            logger.debug(f"EventBindingManager: Ignored state key: {key}")
