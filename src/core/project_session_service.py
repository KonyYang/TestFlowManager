from typing import Optional

from src.core.event_dispatcher import event_dispatcher, EventTopics
from src.core.project_context import ProjectContext
from src.core.state_manager import state_manager


class ProjectSessionService:
    """统一管理项目会话状态写入与打开事件派发。"""

    def open_project(self, project_path: str, dl_number: Optional[str] = None) -> ProjectContext:
        project_context = ProjectContext.from_project_path(project_path, dl_number)
        state_manager.set_state("current_project_context", project_context)
        event_dispatcher.dispatch(EventTopics.PROJECT_OPENED, project_context.to_event_data())
        return project_context

    def apply_project_context(self, project_context: ProjectContext) -> ProjectContext:
        state_manager.set_state("current_project_context", project_context)
        event_dispatcher.dispatch(EventTopics.PROJECT_OPENED, project_context.to_event_data())
        return project_context


project_session_service = ProjectSessionService()
