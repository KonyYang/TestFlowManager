import os
from typing import Optional

from src.core.logger import logger
from src.core.project_context import ProjectContext


class MatrixExportService:
    """负责 Matrix Excel 导出相关逻辑。"""

    def __init__(self, matrix_service):
        self.matrix_service = matrix_service

    def export_matrix_excel(self, file_path, export_type="matrix_excel"):
        self.matrix_service._sync_table_to_model()
        self.matrix_service._parse_and_structure_matrix_data()
        return self.matrix_service.export_to_excel(file_path, export_type)

    def export_matrix_excel_with_result(self, file_path, export_type="matrix_excel"):
        success = self.export_matrix_excel(file_path, export_type)
        if success:
            return {"success": True, "error_kind": None}

        return {
            "success": False,
            "error_kind": self.classify_export_failure(file_path),
        }

    def auto_export_to_project(self, project_context: Optional[ProjectContext], sync_callback=None):
        current_project = project_context.project_path if project_context else None
        logger.info(f"开始自动导出Matrix数据，当前项目路径: {current_project}")

        if not current_project or not os.path.exists(current_project):
            logger.debug("没有获取到有效的项目目录，跳过Matrix数据自动保存")
            return True

        matrix_file_path = self.resolve_project_matrix_file_path(project_context)
        if sync_callback:
            sync_callback()

        success = self.matrix_service.export_controller.export_by_type(matrix_file_path, "matrix_excel")
        if success:
            logger.info(f"成功自动导出Matrix数据到: {matrix_file_path}")
            return True

        logger.error(f"自动导出Matrix数据失败: {matrix_file_path}")
        return False

    def export_record_data(self, export_type: str, sync_callback=None) -> bool:
        if sync_callback:
            sync_callback()

        self.matrix_service.export_controller.update_data_model(self.matrix_service.data_model)
        return self.matrix_service.export_controller.export_by_type(None, export_type)

    def build_default_export_filename(self, project_context: Optional[ProjectContext]) -> str:
        matrix_file_path = self.resolve_project_matrix_file_path(project_context)
        if matrix_file_path:
            return matrix_file_path
        return "matrix.xlsx"

    @staticmethod
    def classify_export_failure(file_path: str) -> str:
        try:
            with open(file_path, 'r+b') as _:
                pass
            return "general"
        except PermissionError:
            return "permission"
        except FileNotFoundError:
            return "missing_path"
        except Exception:
            return "unknown"

    @staticmethod
    def resolve_project_matrix_file_path(project_context: Optional[ProjectContext]) -> Optional[str]:
        if not project_context:
            return None

        current_project = project_context.project_path
        if not current_project:
            return None

        path_parts = current_project.replace('/', '\\').split('\\')
        path_parts = [part for part in path_parts if part]

        if project_context.matrix_file_path and len(path_parts) != 5:
            return project_context.matrix_file_path
        if len(path_parts) == 5:
            return os.path.join(os.path.dirname(current_project), "matrix.xlsx")
        return os.path.join(current_project, "matrix.xlsx")
