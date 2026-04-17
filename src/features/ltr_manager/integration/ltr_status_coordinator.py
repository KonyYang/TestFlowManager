"""
LTR Status Coordinator.

Owns LTR-related events, handles status bar updates and UI feedback.
This separates LTR domain events from Shell controller.
"""
from src.core.logger import logger


class LTRStatusCoordinator:
    """
    Coordinates LTR-related events and status updates.
    
    Responsibilities:
    - Handle ltr.processing.started/completed/failed events
    - Handle ltr.application.confirmed event
    - Update status bar through provided callback
    
    Does NOT handle:
    - LTR business logic (belongs to LTRApplicationService)
    - Project context management (belongs to ProjectSessionCoordinator)
    """
    
    def __init__(self, status_updater=None):
        """
        Initialize LTR status coordinator.
        
        Args:
            status_updater: Callback function for status bar updates
        """
        self._status_updater = status_updater
        self._bound = False
        self._setup_event_subscriptions()
        
        # 注册清理钩子
        from src.core.shutdown_registry import shutdown_registry
        shutdown_registry.register(
            name="LTRStatusCoordinator.cleanup",
            cleanup_fn=self.cleanup,
            priority=20
        )
        
    def _setup_event_subscriptions(self) -> None:
        """Subscribe to LTR-related events."""
        from src.core.event_dispatcher import event_dispatcher, EventTopics
        
        event_dispatcher.subscribe(EventTopics.LTR_PROCESSING_STARTED, self._on_ltr_processing_started)
        event_dispatcher.subscribe(EventTopics.LTR_PROCESSING_COMPLETED, self._on_ltr_processing_completed)
        event_dispatcher.subscribe(EventTopics.LTR_PROCESSING_FAILED, self._on_ltr_processing_failed)
        event_dispatcher.subscribe(EventTopics.LTR_APPLICATION_CONFIRMED, self._on_ltr_application_confirmed)
        
        self._bound = True
        logger.info("LTRStatusCoordinator: Subscribed to LTR events")
        
    def _update_status(self, message: str) -> None:
        """Update status bar if callback is available."""
        if self._status_updater:
            self._status_updater(message)
            
    def _on_ltr_processing_started(self, data: dict) -> None:
        """Handle LTR processing started event."""
        import os
        file_path = data.get("file_path", "未知文件")
        message = f"正在处理LTR申请单: {os.path.basename(file_path)}"
        logger.debug(f"LTRStatusCoordinator: {message}")
        self._update_status(message)
        
    def _on_ltr_processing_completed(self, data: dict) -> None:
        """Handle LTR processing completed event."""
        import os
        file_path = data.get("file_path", "未知文件")
        message = f"LTR申请单处理完成: {os.path.basename(file_path)}"
        logger.debug(f"LTRStatusCoordinator: {message}")
        self._update_status(message)
        
    def _on_ltr_processing_failed(self, data: dict) -> None:
        """Handle LTR processing failed event."""
        import os
        file_path = data.get("file_path", "未知文件")
        error = data.get("error", "未知错误")
        message = f"LTR申请单处理失败: {os.path.basename(file_path)}"
        logger.debug(f"LTRStatusCoordinator: {message} - {error}")
        self._update_status(message)
        
    def _on_ltr_application_confirmed(self, data: dict) -> None:
        """Handle LTR application confirmed event."""
        dl_number = data.get("dl_number")
        message = f"确认LTR申请单: {dl_number}"
        logger.debug(f"LTRStatusCoordinator: {message}")
        self._update_status(message)
        
    def cleanup(self) -> None:
        """Unsubscribe from all events."""
        if not self._bound:
            return
            
        from src.core.event_dispatcher import event_dispatcher, EventTopics
        
        event_dispatcher.unsubscribe(EventTopics.LTR_PROCESSING_STARTED, self._on_ltr_processing_started)
        event_dispatcher.unsubscribe(EventTopics.LTR_PROCESSING_COMPLETED, self._on_ltr_processing_completed)
        event_dispatcher.unsubscribe(EventTopics.LTR_PROCESSING_FAILED, self._on_ltr_processing_failed)
        event_dispatcher.unsubscribe(EventTopics.LTR_APPLICATION_CONFIRMED, self._on_ltr_application_confirmed)
        
        self._bound = False
        logger.info("LTRStatusCoordinator: Unsubscribed from LTR events")
