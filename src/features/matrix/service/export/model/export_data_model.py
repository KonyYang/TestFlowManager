from src.features.matrix.model.matrix_data import MatrixData
from src.core.logger import logger


class ExportDataModel:
    """导出数据模型 - Model层"""
    
    def __init__(self, data_model: MatrixData):
        self.data_model = data_model
        self.merged_cells_info = []

    def get_headers(self):
        """获取表头数据"""
        return self.data_model.headers

    def get_rows(self):
        """获取行数据"""
        return self.data_model.rows

    def get_cell_value(self, row_index, col_index):
        """获取单元格值"""
        if row_index < len(self.data_model.rows) and col_index < len(self.data_model.rows[row_index]):
            return self.data_model.rows[row_index][col_index]
        return ""