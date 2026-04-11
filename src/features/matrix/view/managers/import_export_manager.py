# src/features/matrix/view/managers/import_export_manager.py
from typing import Optional

from src.core.logger import logger
from src.core.project_context import ProjectContext


class ImportExportManager:
    """导入/导出管理器 - 处理Matrix视图的导入和导出操作"""
    
    def __init__(self, view, matrix_controller=None):
        self.view = view
        self.matrix_controller = matrix_controller or getattr(view, "matrix_controller", None)
        self.project_context: Optional[ProjectContext] = None

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        self.project_context = project_context

    def _get_active_project_context(self) -> Optional[ProjectContext]:
        return self.project_context

    def auto_import_matrix_from_project(self):
        """
        从项目文件夹自动导入matrix.xlsx文件
        """
        try:
            logger.debug("尝试从项目文件夹自动导入matrix.xlsx")
            project_context = self._get_active_project_context()
            if self.matrix_controller and self.matrix_controller.auto_import_from_project(project_context):
                self.view.refresh_table()
                logger.info("成功自动导入项目中的matrix.xlsx文件")
        except Exception as e:
            logger.error(f"自动导入matrix.xlsx文件时出错: {e}")
