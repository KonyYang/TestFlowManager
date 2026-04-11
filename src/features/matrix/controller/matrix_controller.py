from PyQt5.QtWidgets import QFileDialog, QMessageBox

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.features.matrix.service.matrix_application_service import MatrixApplicationService


class MatrixController:
    """Core matrix controller."""

    def __init__(self, parent=None, matrix_service=None, application_service=None):
        self.parent = parent
        self.parent_view = parent
        if matrix_service is None:
            raise ValueError(
                "matrix_service is required. Construct MatrixController via MatrixSessionFactory "
                "or pass an explicit matrix_service instance."
            )
        self.service = matrix_service
        self.application_service = (
            application_service or MatrixApplicationService(self.service)
        )
        self.ltr_integration_service = None
        self.project_context = None
        self.ltr_number = None

    def activate_matrix_workspace(self):
        try:
            if (
                self.parent_view
                and hasattr(self.parent_view, "activate_matrix_workspace")
                and hasattr(self.parent_view, "has_matrix_workspace")
                and self.parent_view.has_matrix_workspace()
            ):
                activated = self.parent_view.activate_matrix_workspace()
                if activated:
                    logger.info("Activated Matrix workspace in main window")
                    return True
            logger.warning("Matrix workspace unavailable in current parent view")
            return False
        except Exception as e:
            logger.error(f"Error showing matrix dialog: {e}", exc_info=True)
            raise

    def get_matrix_data(self):
        return self.service.data_model

    def sync_table_to_model(self):
        self.service._sync_table_to_model()

    def initialize_matrix(self):
        return self.service.initialize_matrix()

    def extract_test_methods_from_spec(self):
        return self.service.extract_test_methods_from_spec()

    def update_standard_versions(self):
        return self.service.update_standard_versions()

    def standardize_and_fill_matrix(self):
        return self.application_service.standardize_and_fill()

    def get_undo_cell_operation_text(self):
        return self.service.get_undo_cell_operation_text()

    def get_redo_cell_operation_text(self):
        return self.service.get_redo_cell_operation_text()

    def add_row(self):
        self.service.add_row()

    def insert_row(self, row):
        self.service.insert_row(row)

    def remove_row(self, row):
        self.service.remove_row(row)

    def move_row(self, row, new_position):
        return self.service.move_row(row, new_position)

    def copy_row(self, row):
        return self.service.copy_row(row)

    def paste_row(self, row, copied_row_data):
        return self.service.paste_row(row, copied_row_data)

    def add_column(self):
        self.service.add_column()

    def insert_column(self, col):
        self.service.insert_column(col)

    def remove_column(self, col):
        self.service.remove_column(col)

    def move_column(self, col, new_position):
        return self.service.move_column(col, new_position)

    def copy_column(self, col):
        return self.service.copy_column(col)

    def paste_column(self, col, copied_col_data):
        return self.service.paste_column(col, copied_col_data)

    def set_cell_value(self, row, col, value):
        return self.service.set_cell_value(row, col, value)

    def export_to_excel(self, file_path, export_type="matrix_excel"):
        return self.application_service.export_to_excel(file_path, export_type)

    def import_from_excel(self, file_path):
        return self.application_service.import_from_excel(file_path)

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        return self.application_service.import_from_spec(file_path, page_number, keyword)

    def auto_import_from_project(self, project_context: ProjectContext = None):
        return self.application_service.auto_import_from_project(
            project_context or self.get_project_context()
        )

    def merge_or_split_cells(self, table_widget):
        return self.service.merge_or_split_cells(table_widget)

    def can_undo_cell_operation(self):
        return self.service.can_undo_cell_operation()

    def can_redo_cell_operation(self):
        return self.service.can_redo_cell_operation()

    def undo_cell_operation(self):
        return self.service.undo_cell_operation()

    def redo_cell_operation(self):
        return self.service.redo_cell_operation()

    def show_test_group_selector(self):
        pass

    def set_ltr_integration_service(self, ltr_integration_service):
        if self.ltr_integration_service != ltr_integration_service:
            logger.debug("MatrixController: Setting LTR integration service")
            self.ltr_integration_service = ltr_integration_service
        else:
            logger.debug(
                "MatrixController: LTR integration service unchanged, skipping update"
            )

    def set_ltr_data(self, ltr_data):
        self.application_service.set_ltr_data(ltr_data)

    def set_project_context(self, project_context: ProjectContext):
        self.project_context = project_context
        self.application_service.set_project_context(project_context)

    def get_project_context(self):
        return self.project_context

    def get_matrix_headers(self):
        if hasattr(self.service.data_model, "headers"):
            return self.service.data_model.headers
        return []

    def get_matrix_rows(self):
        if hasattr(self.service.data_model, "rows"):
            return self.service.data_model.rows
        return []

    def initialize_with_ltr_data(self):
        return self.application_service.initialize_with_ltr_data(
            self.ltr_integration_service
        )

    def set_ltr_number(self, ltr_number):
        self.ltr_number = ltr_number

    def auto_export_matrix_data_on_shutdown(self):
        try:
            project_context = self.get_project_context()
            sync_callback = (
                self.parent.sync_to_model
                if self.parent and hasattr(self.parent, "sync_to_model")
                else None
            )
            return self.application_service.auto_export_to_project(
                project_context,
                sync_callback=sync_callback,
            )
        except Exception as e:
            logger.error(f"自动导出Matrix数据时出错: {e}", exc_info=True)
            return False

    def handle_export_matrix_to_excel(self):
        try:
            if self.parent and hasattr(self.parent, "sync_to_model"):
                self.parent.sync_to_model()

            project_context = self.get_project_context()
            default_filename = self.application_service.build_default_export_filename(
                project_context
            )
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent if self.parent else None,
                "导出窗口矩阵",
                default_filename,
                "Excel Files (*.xlsx)",
            )

            if not file_path:
                return {"success": False, "message": None, "cancelled": True}

            result = self.application_service.export_to_excel_with_result(
                file_path,
                "matrix_excel",
            )
            if result["success"]:
                return {"success": True, "message": None}

            error_kind = result["error_kind"]
            if error_kind == "permission":
                return {
                    "success": False,
                    "message": "导出失败，文件已被其他程序占用（可能已在Excel中打开），请关闭文件后重试",
                }
            if error_kind == "missing_path":
                return {"success": False, "message": "导出失败，请检查文件路径是否正确"}
            if error_kind == "general":
                return {"success": False, "message": "导出失败，请检查文件路径或权限"}
            return {"success": False, "message": "导出失败，发生未知错误"}
        except Exception as e:
            logger.error(f"导出窗口矩阵时出错: {e}", exc_info=True)
            return {"success": False, "message": f"导出过程中发生异常: {str(e)}"}

    def handle_export_llcr(self):
        try:
            sync_callback = (
                self.parent.sync_to_model
                if self.parent and hasattr(self.parent, "sync_to_model")
                else None
            )
            return self.application_service.export_llcr(sync_callback=sync_callback)
        except Exception as e:
            logger.error(f"导出LLCR时出错: {e}", exc_info=True)
            QMessageBox.warning(
                self.parent if self.parent else None,
                "错误",
                f"导出LLCR过程中发生异常: {str(e)}",
            )
            return False

    def handle_export_cr(self):
        try:
            sync_callback = (
                self.parent.sync_to_model
                if self.parent and hasattr(self.parent, "sync_to_model")
                else None
            )
            return self.application_service.export_cr(sync_callback=sync_callback)
        except Exception as e:
            logger.error(f"导出CR时出错: {e}", exc_info=True)
            QMessageBox.warning(
                self.parent if self.parent else None,
                "错误",
                f"导出CR过程中发生异常: {str(e)}",
            )
            return False
