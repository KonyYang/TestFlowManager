import os
from typing import Optional

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.features.matrix.service.document_parsers.excel_parser import ExcelParser


class MatrixImportService:
    """负责 Matrix Excel 导入相关逻辑。"""

    def __init__(self, data_model=None, parser: Optional[ExcelParser] = None, spec_processing_service=None):
        self.data_model = data_model
        self.parser = parser or ExcelParser()
        self.spec_processing_service = spec_processing_service

    def import_from_project(self, data_model=None, project_context: Optional[ProjectContext] = None) -> bool:
        """从项目目录中的 matrix.xlsx 导入数据。"""
        data_model = data_model or self.data_model
        if data_model is None:
            logger.error("导入Matrix项目文件时缺少 data_model")
            return False

        matrix_file_path = self._resolve_matrix_file_path(project_context)
        if not matrix_file_path:
            logger.debug("没有当前项目，跳过自动导入")
            return False

        if not os.path.exists(matrix_file_path):
            logger.debug(f"项目中没有matrix.xlsx文件: {matrix_file_path}")
            return False

        logger.info(f"发现项目中的matrix.xlsx文件: {matrix_file_path}")
        return self.import_from_excel(matrix_file_path, data_model=data_model)

    def import_from_excel(self, file_path: str, data_model=None) -> bool:
        """从 Excel 文件导入数据到 data_model。"""
        data_model = data_model or self.data_model
        if data_model is None:
            logger.error("导入Matrix Excel文件时缺少 data_model")
            return False

        try:
            result = self.parser.parse(file_path)
            if not result or "data" not in result or not result["data"]:
                logger.warning("matrix.xlsx文件中没有有效数据")
                return False

            self._apply_result_to_data_model(data_model, result)
            logger.info(f"成功导入Matrix Excel文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"导入Matrix Excel文件时出错: {e}")
            return False

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """从规格书导入数据到 Matrix。"""
        if not self.spec_processing_service:
            logger.error("导入Spec时缺少 spec_processing_service")
            return {"success": False, "error": "spec_processing_service unavailable"}

        logger.debug(
            f"MatrixImportService.import_from_spec 被调用，参数: "
            f"file_path={file_path}, page_number={page_number}, keyword={keyword}"
        )
        result = self.spec_processing_service.import_from_spec(file_path, page_number, keyword)
        logger.debug(f"MatrixImportService.import_from_spec 完成，返回结果: {result}")
        return result

    @staticmethod
    def _resolve_matrix_file_path(project_context: Optional[ProjectContext]) -> Optional[str]:
        if not project_context:
            return None
        return project_context.matrix_file_path or os.path.join(project_context.project_path, "matrix.xlsx")

    @staticmethod
    def _apply_result_to_data_model(data_model, result: dict) -> None:
        data_model.rows = result["data"]

        if "headers" in result and result["headers"]:
            data_model.headers = result["headers"]
        else:
            data_model.headers = [
                data_model._column_index_to_letter(i)
                for i in range(len(result["data"][0]) if result["data"] else 7)
            ]

        if "merged_cells" in result:
            data_model.merged_cells_info = result["merged_cells"]
