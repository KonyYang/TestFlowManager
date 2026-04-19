from PyQt5.QtWidgets import QFileDialog, QMessageBox

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.features.matrix.controller.runtime.matrix_export_runtime_coordinator import (
    MatrixExportRuntimeCoordinator,
)
from src.features.matrix.service.matrix_application_service import MatrixApplicationService


class MatrixController:
    """
    Matrix页面运行时控制器

    职责边界：
    - 页面运行时行为
    - 表格操作（行/列/单元格）
    - 运行时编辑/更新/刷新命令
    - 导入/导出运行时入口方法
    - 页面级上下文访问器

    注意：此控制器不处理项目/工作区级别的入口编排，
    该类职责由MatrixProjectController负责。
    """

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
        self.export_runtime_coordinator = MatrixExportRuntimeCoordinator()
        self.ltr_integration_service = None
        self.project_context = None
        self.ltr_number = None
        
        # 注册清理钩子
        from src.core.shutdown_registry import shutdown_registry
        shutdown_registry.register(
            name="MatrixController.auto_export",
            cleanup_fn=self.auto_export_matrix_data_on_shutdown,
            priority=40
        )

    def _activate_matrix_workspace_runtime(self):
        """
        运行时层工作区激活 - 内部委托方法

        警告：此方法不是项目/工作区入口！
        外部调用者应使用 MatrixProjectController.open_matrix_workspace() 作为唯一入口。

        此方法仅作为 page/runtime 层对 parent view 的激活委托存在，
        由 MatrixProjectController 在编排完成后调用。

        Returns:
            bool: 是否成功激活
        """
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

    # 兼容性保留：旧方法名作为转发器
    def activate_matrix_workspace(self):
        """
        [兼容性保留] 请使用 _activate_matrix_workspace_runtime()

        此方法保留用于兼容性，内部调用 _activate_matrix_workspace_runtime()。
        外部新代码不应直接调用此方法。
        """
        return self._activate_matrix_workspace_runtime()

    def get_matrix_data(self):
        return self.service.data_model

    def sync_table_to_model(self):
        """同步表格数据到模型 - 委托给应用服务层"""
        # 通过应用服务层进行同步，避免直接访问服务私有方法
        self.application_service.export_service.sync_table_to_model()

    def initialize_matrix(self):
        return self.application_service.initialize_matrix()

    def extract_test_methods_from_spec(self):
        """从规格书提取测试方法 - 委托给应用服务层"""
        return self.application_service.extract_test_methods_from_spec()

    def update_standard_versions(self):
        """更新标准版本 - 委托给应用服务层"""
        return self.application_service.update_standard_versions()

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
        """
        显示测试组选择器 - 占位符方法

        TODO: 如果此功能不再需要，应在后续重构中移除
        如果需要实现，应在页面层完成而非控制器层
        """
        logger.debug("show_test_group_selector called but not implemented")
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
            return self.export_runtime_coordinator.auto_export_on_shutdown(
                self.application_service,
                self.get_project_context(),
                self.parent,
            )
        except Exception as e:
            logger.error(f"自动导出Matrix数据时出错: {e}", exc_info=True)
            return False

    def handle_export_matrix_to_excel(self):
        try:
            return self.export_runtime_coordinator.handle_export_matrix_to_excel(
                self.application_service,
                self.get_project_context(),
                self.parent,
            )
        except Exception as e:
            logger.error(f"导出窗口矩阵时出错: {e}", exc_info=True)
            return {"success": False, "message": f"导出过程中发生异常: {str(e)}"}

    def handle_export_llcr(self):
        try:
            return self.export_runtime_coordinator.handle_export_llcr(
                self.application_service,
                self.parent,
            )
        except Exception as e:
            logger.error(f"导出LLCR时出错: {e}", exc_info=True)
            self.export_runtime_coordinator.show_export_warning(
                self.parent,
                "错误",
                f"导出LLCR过程中发生异常: {str(e)}",
            )
            return False

    def handle_export_cr(self):
        try:
            return self.export_runtime_coordinator.handle_export_cr(
                self.application_service,
                self.parent,
            )
        except Exception as e:
            logger.error(f"导出CR时出错: {e}", exc_info=True)
            self.export_runtime_coordinator.show_export_warning(
                self.parent,
                "错误",
                f"导出CR过程中发生异常: {str(e)}",
            )
            return False
