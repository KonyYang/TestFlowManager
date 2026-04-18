import os
from typing import Optional

from src.core.logger import logger
from src.core.project_context import ProjectContext


class MatrixExportService:
    """负责 Matrix Excel 导出相关逻辑。"""

    def __init__(self, matrix_service):
        self.matrix_service = matrix_service

    def sync_table_to_model(self):
        self._sync_table_to_model()

    def _sync_table_to_model(self):
        """
        同步表格数据到模型 - 导出前数据准备
        """
        # 更新导出控制器中的数据模型
        self.matrix_service.export_controller.update_data_model(self.matrix_service.data_model)

    def export_matrix_excel(self, file_path, export_type="matrix_excel"):
        """导出Matrix到Excel - 完整的导出流程控制"""
        # 同步数据到模型
        self._sync_table_to_model()
        # 解析并结构化数据（直接使用 data_structure_service，不经过 MatrixService 兼容层）
        self.matrix_service.data_structure_service.parse_and_structure_matrix_data()
        # 执行导出
        return self._export_to_excel(file_path, export_type)

    def _export_to_excel(self, file_path, export_type="matrix_excel"):
        """
        执行实际的Excel导出 - 导出执行核心
        注意：调用此方法前应已执行 _sync_table_to_model()
        """
        # 添加调试信息
        try:
            rows = self.matrix_service.data_model.rows
            headers = self.matrix_service.data_model.headers
            logger.debug(f"导出前数据概况 - 表头数量: {len(headers)}, 行数: {len(rows)}")
            if headers:
                logger.debug(f"表头内容: {headers}")
            if rows:
                logger.debug(f"导出前第一行数据: {rows[0][:5] if len(rows[0]) > 5 else rows[0]}")
                logger.debug(f"导出前前3行:")
                for i, row in enumerate(rows[:3]):
                    logger.debug(f"  第{i+1}行: {row}")
                if len(rows) > 3:
                    logger.debug(f"  ... (还有{len(rows)-3}行)")
        except Exception as e:
            logger.error(f"获取导出前数据信息时出错: {e}")

        # 使用导出控制器执行导出
        return self.matrix_service.export_controller.export_by_type(file_path, export_type)

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
