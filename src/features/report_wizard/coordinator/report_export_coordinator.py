from importlib import import_module
from typing import Any, Optional


def _load_symbol(module_path: str, symbol_name: str):
    """Load heavy collaborators lazily to keep the feature entry edge surface narrow."""
    module = import_module(module_path)
    return getattr(module, symbol_name)


class ReportExportCoordinator:
    def __init__(
        self,
        generation_service: Optional[Any] = None,
        updater_service: Optional[Any] = None,
    ):
        if generation_service is None:
            ReportGenerationService = _load_symbol(
                "src.features.report_wizard.service.report_generation_service",
                "ReportGenerationService",
            )
            generation_service = ReportGenerationService()
        if updater_service is None:
            ReportUpdaterService = _load_symbol(
                "src.features.report_updater.service.report_updater_service",
                "ReportUpdaterService",
            )
            updater_service = ReportUpdaterService()
        self.generation_service = generation_service
        self.updater_service = updater_service
        self.project_context: Optional[Any] = None

    def set_project_context(self, project_context: Optional[Any]) -> None:
        from src.core.logger import logger
        logger.info(f"ReportExportCoordinator: set_project_context called with project_context={project_context is not None}")
        if project_context:
            logger.info(f"ReportExportCoordinator: project_context.project_path={project_context.project_path}")
        self.project_context = project_context
        self.updater_service.set_project_context(project_context)

    def load_header_data(self) -> Optional[Any]:
        if not self.project_context:
            return None
        return self.generation_service.load_project_data(self.project_context)

    def create_report_from_template(
        self,
        header_data: Any,
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
