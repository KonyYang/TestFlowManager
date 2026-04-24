"""
Report wizard controller.
"""

from importlib import import_module
from typing import Any, Optional


def _load_symbol(module_path: str, symbol_name: str):
    """Load wizard collaborators lazily to keep the controller import surface narrow."""
    module = import_module(module_path)
    return getattr(module, symbol_name)


class ReportWizardController:
    """Coordinates report wizard flow."""

    def __init__(self, parent_window=None, report_export_coordinator: Optional[Any] = None):
        self.parent_window = parent_window
        self.view = None
        if report_export_coordinator is None:
            ReportExportCoordinator = _load_symbol(
                "src.features.report_wizard.coordinator.report_export_coordinator",
                "ReportExportCoordinator",
            )
            report_export_coordinator = ReportExportCoordinator()
        self.export_coordinator = report_export_coordinator
        self.project_context: Optional[Any] = None
        self.matrix_provider: Optional[Any] = None

    def set_project_context(self, project_context: Optional[Any]) -> None:
        from src.core.logger import logger
        logger.info(f"ReportWizardController: set_project_context called with project_context={project_context is not None}")
        if project_context:
            logger.info(f"ReportWizardController: project_context.project_path={project_context.project_path}")
        self.project_context = project_context
        self.export_coordinator.set_project_context(project_context)

    def set_matrix_provider(self, matrix_provider: Optional[Any]) -> None:
        self.matrix_provider = matrix_provider

    def set_matrix_controller(self, matrix_controller) -> None:
        self.set_matrix_provider(matrix_controller)

    def show_wizard(self):
        ReportWizardDialog = _load_symbol(
            "src.features.report_wizard.view.report_wizard_dialog",
            "ReportWizardDialog",
        )
        self.view = ReportWizardDialog(
            self.parent_window,
            project_context=self.project_context,
            matrix_provider=self.matrix_provider,
            create_report_callback=self._create_report,
        )

        if self.matrix_provider:
            self.view.set_matrix_provider(self.matrix_provider)
        
        if self.project_context:
            self.view.set_project_context(self.project_context)

        project_data = self.export_coordinator.load_header_data()
        if project_data:
            header_page = self.view.pages[0]
            header_page.set_header_data(project_data)

        self.view.finished.connect(self.on_wizard_finished)
        self.view.exec_()

    def on_wizard_finished(self, result):
        ReportWizardDialog = _load_symbol(
            "src.features.report_wizard.view.report_wizard_dialog",
            "ReportWizardDialog",
        )
        if result != ReportWizardDialog.Accepted:
            return

        all_data = self.view.get_all_data()
        if "header_data" not in all_data:
            return

        header_data = all_data["header_data"]
        try:
            body_content_page = self.view.pages[1]
            document_path = body_content_page.get_document_path()

            if document_path:
                output_path = document_path
            else:
                output_path = self.export_coordinator.create_report_from_template(
                    header_data,
                )

            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(self.view, "成功", f"报告已成功生成:\n{output_path}")
        except Exception as exc:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.critical(self.view, "错误", f"生成报告时出错: {exc}")

    def _create_report(self, header_data: Any) -> str:
        return self.export_coordinator.create_report_from_template(header_data)
