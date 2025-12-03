from src.features.matrix.service.export.matrix_export_service import MatrixEditorExcelExportService
from src.features.matrix.service.export.test_status_export_service import TestStatusExportService
from src.core.logger import logger


class ExportController:
    """导出控制器 - Controller层"""
    
    def __init__(self, data_model, ltr_data=None):
        self.data_model = data_model
        self.ltr_data = ltr_data
        self.excel_export_service = MatrixEditorExcelExportService(data_model)
        self.test_status_export_service = TestStatusExportService(data_model, ltr_data)
        logger.debug(f"ExportController 初始化完成，ltr_data: {ltr_data}")
        
    def export_by_type(self, file_path, export_type):
        """
        根据导出类型执行导出操作
        
        Args:
            file_path: 导出文件路径
            export_type: 导出类型
            
        Returns:
            bool: 是否导出成功
        """
        try:
            logger.info(f"开始导出操作，类型: {export_type}，路径: {file_path}")
            
            if export_type == "matrix_excel":
                logger.debug("调用 matrix_excel 导出服务")
                return self.excel_export_service.export_matrix_to_excel(file_path)
            elif export_type == "test_status":
                logger.debug("调用 test_status 导出服务")
                return self.test_status_export_service.export_test_status_to_excel(file_path)
            elif export_type in ["llcr", "cr", "mating_unmating", "ir_dwv"]:
                # 这些类型将使用相同的基础Excel导出服务，但可能有不同的处理逻辑
                logger.debug(f"调用基础Excel导出服务，类型: {export_type}")
                return self.excel_export_service.export_matrix_to_excel(file_path)
            else:
                logger.warning(f"不支持的导出类型: {export_type}")
                return False
        except Exception as e:
            logger.error(f"导出过程中出错: {e}", exc_info=True)
            return False
            
    def set_ltr_data(self, ltr_data):
        """
        设置LTR数据
        
        Args:
            ltr_data: LTR申请单数据
        """
        logger.debug(f"设置LTR数据: {ltr_data}")
        self.ltr_data = ltr_data
        # 更新TestStatusExportService中的ltr_data
        self.test_status_export_service = TestStatusExportService(self.data_model, ltr_data)