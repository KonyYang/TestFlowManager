from dataclasses import dataclass
from typing import Optional

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.domain.project.project_document_context import ProjectDocumentContext
from src.app.composition.project_session_application_service import project_session_app_service


@dataclass(frozen=True)
class ProjectCreationSessionResult:
    project_context: ProjectContext
    dl_number: str
    ltr_project_loaded: bool


class ProjectCreationApplicationService:
    """统一处理项目创建完成后的项目会话建立与Matrix/LTR同步。"""

    def __init__(self, ltr_integration_service, matrix_project_controller):
        self.ltr_integration_service = ltr_integration_service
        self.matrix_project_controller = matrix_project_controller

    def open_created_project(
        self,
        project_path: str,
        dl_number: Optional[str] = None,
    ) -> Optional[ProjectCreationSessionResult]:
        if not project_path:
            logger.warning("Project creation session skipped: no project_path provided")
            return None

        if not dl_number:
            document_context = ProjectDocumentContext.from_project_context(
                ProjectContext.from_project_path(project_path)
            )
            dl_number = document_context.dl_number
            logger.debug(f"Resolved dl_number from ProjectDocumentContext: {dl_number}")

        if not dl_number:
            logger.warning("Project creation session skipped: no dl_number resolved")
            return None

        # Trigger-side unification: build context + activate via ProjectSessionApplicationService.
        # All UI/Matrix side effects run through the single entry (S1-2).
        project_context = ProjectContext.from_project_path(project_path, dl_number)
        project_session_app_service.activate_existing_context(
            project_context,
            trigger_matrix_auto_import=False,  # Matrix import handled by caller or event consumer
        )

        ltr_project_loaded = False
        loaded_data = self.ltr_integration_service.load_ltr_project(project_path)
        ltr_project_loaded = loaded_data is not None
        logger.info(f"Loaded LTR project data result: {ltr_project_loaded}")
        project_json_path = None
        if hasattr(self.ltr_integration_service, "get_project_json_path"):
            project_json_path = self.ltr_integration_service.get_project_json_path()
        else:
            project_json_path = getattr(self.ltr_integration_service, "project_json_path", None)
        logger.info(f"Project JSON path from LTR service: {project_json_path}")

        if self.matrix_project_controller.ltr_integration_service != self.ltr_integration_service:
            self.matrix_project_controller.set_ltr_integration_service(self.ltr_integration_service)
        # ProjectContext application and Matrix initialization are orchestrated by the caller
        # (MainWindow via ProjectSessionCoordinator, or local controller for isolated pilot sessions).

        return ProjectCreationSessionResult(
            project_context=project_context,
            dl_number=dl_number,
            ltr_project_loaded=ltr_project_loaded,
        )
