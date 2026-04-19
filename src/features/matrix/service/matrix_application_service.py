from typing import Optional

from src.core.project_context import ProjectContext
from src.features.matrix.service.matrix_export_service import MatrixExportService


class MatrixApplicationService:
    """负责 Matrix 页面与服务之间的应用层编排。"""

    def __init__(self, matrix_service):
        self.matrix_service = matrix_service
        self.export_service = MatrixExportService(matrix_service)

    def initialize_matrix(self):
        return self.matrix_service.initializer.initialize_matrix()

    def import_from_excel(self, file_path: str) -> bool:
        return self.matrix_service.import_service.import_from_excel(file_path)

    def export_to_excel(self, file_path, export_type="matrix_excel"):
        return self.export_service.export_matrix_excel(file_path, export_type)

    def export_to_excel_with_result(self, file_path, export_type="matrix_excel"):
        return self.export_service.export_matrix_excel_with_result(file_path, export_type)

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """
        从Spec导入数据 - 应用层工作流编排

        直接使用 MatrixImportService，不经过 MatrixService 转发
        """
        # 直接使用 import_service 执行导入
        raw_result = self.matrix_service.import_service.import_from_spec(
            file_path, page_number, keyword
        )
        return self._build_spec_import_result(raw_result)

    def auto_import_from_project(self, project_context: Optional[ProjectContext]) -> bool:
        return self.matrix_service.import_service.import_from_project(
            project_context=project_context
        )

    def auto_export_to_project(self, project_context: Optional[ProjectContext], sync_callback=None):
        return self.export_service.auto_export_to_project(project_context, sync_callback=sync_callback)

    def resolve_project_matrix_file_path(self, project_context: Optional[ProjectContext]) -> Optional[str]:
        return self.export_service.resolve_project_matrix_file_path(project_context)

    def build_default_export_filename(self, project_context: Optional[ProjectContext]) -> str:
        return self.export_service.build_default_export_filename(project_context)

    def export_llcr(self, sync_callback=None) -> bool:
        return self.export_service.export_record_data("llcr", sync_callback=sync_callback)

    def export_cr(self, sync_callback=None) -> bool:
        return self.export_service.export_record_data("cr", sync_callback=sync_callback)

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        self.matrix_service.export_controller.set_project_context(project_context)

    def set_ltr_data(self, ltr_data) -> None:
        """设置LTR数据到导出控制器"""
        # 将LTR数据设置到导出控制器中
        self.matrix_service.export_controller.set_ltr_data(ltr_data)

    def initialize_with_ltr_data(self, ltr_integration_service) -> bool:
        if not ltr_integration_service or not ltr_integration_service.is_project_loaded():
            return False

        ltr_data = ltr_integration_service.get_ltr_data()
        if not ltr_data:
            return False

        self.initialize_matrix()
        ltr_integration_service.get_test_info()
        return True

    def extract_test_methods_from_spec(self):
        """
        从已导入的规格书中提取测试方法标准并填充到Matrix中

        Returns:
            bool: 是否成功提取并填充测试方法
        """
        # 直接使用 spec_processing_service，不经过 MatrixService 转发
        return self.matrix_service.spec_processing_service.extract_test_methods_from_spec()

    def update_standard_versions(self):
        """
        更新测试方法的标准版本号

        Returns:
            dict: 更新结果，包含是否成功更新以及更新详情
        """
        # 直接使用 spec_processing_service，不经过 MatrixService 转发
        result = self.matrix_service.spec_processing_service.update_standard_versions()
        if result.get("success"):
            # 成功后解析并结构化数据
            self._parse_and_structure_matrix_data()
        return result

    def _parse_and_structure_matrix_data(self):
        """
        解析Matrix原始数据并构造成结构化数据
        """
        self.matrix_service.data_structure_service.parse_and_structure_matrix_data()

    def standardize_and_fill(self):
        """执行 Matrix 标准化填充主流程。"""
        init_result = self.initialize_matrix()
        if not init_result:
            return {
                "success": False,
                "initialized": False,
                "extract_result": False,
                "update_result": {"success": False},
            }

        # 使用本类方法，不再经过 MatrixService
        extract_result = self.extract_test_methods_from_spec()
        update_result = self.update_standard_versions()

        return {
            "success": bool(extract_result or update_result.get("success", False)),
            "initialized": True,
            "extract_result": extract_result,
            "update_result": update_result,
        }

    @staticmethod
    def _build_spec_import_result(raw_result):
        success = bool(raw_result and raw_result.get("success", False))
        error = raw_result.get("error") if isinstance(raw_result, dict) else None

        result = {
            "success": success,
            "error": error,
            "post_action": "refresh_only" if success else "none",
            "should_refresh": success,
            "should_initialize": False,
            "should_parse": False,
        }
        if isinstance(raw_result, dict):
            result.update(raw_result)
        return result
