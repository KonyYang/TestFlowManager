from typing import Optional

from src.core.project_context import ProjectContext
from src.features.report_wizard.model.header_data import HeaderData
from src.features.report_wizard.service.report_generation_service import ReportGenerationService
from src.features.report_updater.service.report_updater_service import ReportUpdaterService


class ReportExportCoordinator:
    def __init__(
        self,
        generation_service: Optional[ReportGenerationService] = None,
        updater_service: Optional[ReportUpdaterService] = None,
    ):
        self.generation_service = generation_service or ReportGenerationService()
        self.updater_service = updater_service or ReportUpdaterService()
        self.project_context: Optional[ProjectContext] = None

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        from src.core.logger import logger
        logger.info(f"ReportExportCoordinator: set_project_context called with project_context={project_context is not None}")
        if project_context:
            logger.info(f"ReportExportCoordinator: project_context.project_path={project_context.project_path}")
        self.project_context = project_context
        self.updater_service.set_project_context(project_context)

    def load_header_data(self) -> Optional[HeaderData]:
        if not self.project_context:
            return None
        return self.generation_service.load_project_data(self.project_context)

    def create_report_from_template(
        self,
        header_data: HeaderData,
        *,
        output_dir: Optional[str] = None,
    ) -> str:
        from src.core.logger import logger
        logger.info(f"ReportExportCoordinator: create_report_from_template - project_context={self.project_context is not None}")
        if not self.project_context:
            raise ValueError("ProjectContext is required to generate a report.")
        return self.generation_service.create_report_from_template(
            header_data,
            output_dir=output_dir,
            project_context=self.project_context,
        )

    def update_equipment_list(self, report_path: str) -> bool:
        return self.updater_service.update_equipment_list(report_path)
