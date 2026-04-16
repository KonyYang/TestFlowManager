"""
MainWindow Feature Facade - Shell-facing feature controller assembly layer.

Responsibilities:
- Own lazy construction of shell-triggered feature controllers.
- Provide feature action methods for shell use.
- Hide construction details from MainWindow.

This object is a shell-facing assembly and forwarding layer only.
Business logic remains inside feature modules.

> Updated: 2026-04-15
> Scope: Moved from service/ to integration/ for proper architectural placement
"""

from src.core.logger import logger
from src.features.customer_report_generator.controller.customer_report_controller import CustomerReportController
from src.features.report_wizard.controller.report_wizard_controller import ReportWizardController
from src.features.document_parser.controller.document_parser_controller import DocumentParserController
from src.features.report_updater.controller.report_updater_controller import ReportUpdaterController


class MainWindowFeatureFacade:
    """
    Facade for shell-triggered feature controllers.

    MainWindow uses this to avoid directly instantiating or holding
    references to feature-specific controllers.
    """

    def __init__(self, main_window):
        """
        Initialize the facade with a reference to the main window shell.

        Args:
            main_window: The MainWindow instance for UI context access.
        """
        self.main_window = main_window

        # Cached controller instances (lazy loaded)
        self._customer_report_controller = None
        self._report_wizard_controller = None
        self._document_parser_controller = None
        self._report_updater_controller = None

    # --- Lazy Getter Methods ---

    def get_customer_report_controller(self):
        """Lazy load CustomerReportController."""
        if self._customer_report_controller is None:
            logger.debug("Lazy loading CustomerReportController")
            self._customer_report_controller = CustomerReportController(self.main_window)
        return self._customer_report_controller

    def get_report_wizard_controller(self):
        """Lazy load ReportWizardController."""
        if self._report_wizard_controller is None:
            logger.debug("Lazy loading ReportWizardController")
            self._report_wizard_controller = ReportWizardController(self.main_window)
        return self._report_wizard_controller

    def get_document_parser_controller(self):
        """Lazy load DocumentParserController."""
        if self._document_parser_controller is None:
            logger.debug("Lazy loading DocumentParserController")
            self._document_parser_controller = DocumentParserController(self.main_window)
        return self._document_parser_controller

    def get_report_updater_controller(self):
        """Lazy load ReportUpdaterController."""
        if self._report_updater_controller is None:
            logger.debug("Lazy loading ReportUpdaterController")
            self._report_updater_controller = ReportUpdaterController(self.main_window)
        return self._report_updater_controller

    # --- Shell-Facing Action Methods ---

    def run_create_report(self, project_context, matrix_controller):
        """
        Launch report creation wizard.

        Args:
            project_context: Current project context from MainWindowController.
            matrix_controller: Current MatrixController for data access.
        """
        from src.core.logger import logger
        logger.info(f"FeatureFacade.run_create_report: START - project_context={project_context is not None}")
        if project_context:
            logger.info(f"FeatureFacade.run_create_report: project_path={project_context.project_path}")
        else:
            logger.error("FeatureFacade.run_create_report: ERROR - project_context is None!")
        
        controller = self.get_report_wizard_controller()
        logger.info(f"FeatureFacade.run_create_report: Got controller={controller is not None}")
        
        controller.set_project_context(project_context)
        logger.info(f"FeatureFacade.run_create_report: Called set_project_context")
        
        controller.set_matrix_controller(matrix_controller)
        controller.show_wizard()

    def run_update_report(self, project_context):
        """
        Launch report update dialog.

        Args:
            project_context: Current project context from MainWindowController.
        """
        logger.debug("FeatureFacade: run_update_report")
        controller = self.get_report_updater_controller()
        controller.set_project_context(project_context)
        controller.show_report_updater_dialog()

    def run_convert_customer_report(self, project_context) -> bool:
        """
        Generate customer version of the report.

        Args:
            project_context: Current project context from MainWindowController.

        Returns:
            True if conversion succeeded, False otherwise.
        """
        logger.debug("FeatureFacade: run_convert_customer_report")
        controller = self.get_customer_report_controller()
        return controller.handle_generate_customer_report_with_context(project_context)

    def run_edit_body_content(self, file_path: str):
        """
        Open body content editor for a Word document.

        Args:
            file_path: Path to the Word document selected by user.
        """
        logger.debug(f"FeatureFacade: run_edit_body_content -> {file_path}")
        controller = self.get_document_parser_controller()
        controller.show_body_content_editor(file_path)

    def run_encrypt_test_files(self):
        """
        Launch file encryption workflow with folder selection.
        Uses method-local import to avoid startup-time dependency.
        """
        logger.debug("FeatureFacade: run_encrypt_test_files")
        # Method-local import to defer FileEncryptionController loading
        from src.features.file_encryption.controller.file_encryption_controller import FileEncryptionController

        controller = FileEncryptionController(self.main_window)
        folder_path = controller.show_folder_selection()
        if folder_path:
            controller.start_encryption_task(folder_path)
