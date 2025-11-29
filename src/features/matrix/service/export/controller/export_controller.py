from src.features.matrix.service.export.matrix_export_service import MatrixEditorExcelExportService
from src.core.logger import logger


class ExportController:
    """导出控制器 - Controller层"""
    
    def __init__(self, data_model):
        self.data_model = data_model
        self.excel_export_service = MatrixEditorExcelExportService(data_model)
        
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
                return self.excel_export_service.export_matrix_to_excel(file_path)
            elif export_type in ["llcr", "cr", "mating_unmating", "ir_dwv"]:
                # 这些类型将使用相同的基础Excel导出服务，但可能有不同的处理逻辑
                return self.excel_export_service.export_matrix_to_excel(file_path)
            else:
                logger.warning(f"不支持的导出类型: {export_type}")
                return False
        except Exception as e:
            logger.error(f"导出过程中出错: {e}")
            return False