from src.features.matrix.service.matrix_cell_service import MatrixCellService
from src.core.logger import logger


class MatrixFormattingService:
    """Matrix格式化服务 - 处理格式化相关功能（如单元格合并）"""

    def __init__(self, cell_service: MatrixCellService):
        self.cell_service = cell_service

    def merge_or_split_cells(self, table_widget):
        """合并或拆分单元格 - Service层业务逻辑"""
        return self.cell_service.merge_or_split_cells(table_widget)
        
    def can_undo_cell_operation(self):
        """检查是否可以撤销单元格操作"""
        return self.cell_service.can_undo()
        
    def can_redo_cell_operation(self):
        """检查是否可以重做单元格操作"""
        return self.cell_service.can_redo()
        
    def undo_cell_operation(self):
        """撤销单元格操作"""
        return self.cell_service.undo()
        
    def redo_cell_operation(self):
        """重做单元格操作"""
        return self.cell_service.redo()
        
    def get_undo_cell_operation_text(self):
        """获取撤销单元格操作的文本描述"""
        return self.cell_service.undo_text()
        
    def get_redo_cell_operation_text(self):
        """获取重做单元格操作的文本描述"""
        return self.cell_service.redo_text()