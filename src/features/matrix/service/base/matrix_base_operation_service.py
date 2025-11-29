from src.features.matrix.model.matrix_data import MatrixData
from src.core.logger import logger


class MatrixBaseOperationService:
    """Matrix基本操作服务 - 处理基本的行列操作"""

    def __init__(self, data_model: MatrixData):
        self.data_model = data_model

    def add_column(self, column_name="", position=None):
        """添加新列 - Service层业务逻辑"""
        return self.data_model.add_column(column_name, position)

    def insert_column(self, column_index, column_name=""):
        """在指定位置插入新列 - Service层业务逻辑"""
        return self.data_model.insert_column(column_index, column_name)

    def move_column(self, from_index, to_index):
        """移动列 - Service层业务逻辑"""
        return self.data_model.move_column(from_index, to_index)

    def remove_column(self, column_index):
        """删除指定列 - Service层业务逻辑"""
        return self.data_model.remove_column(column_index)

    def add_row(self, row_data=None):
        """添加新行 - Service层业务逻辑"""
        return self.data_model.add_row(row_data)

    def insert_row(self, row_index, row_data=None):
        """在指定位置插入新行 - Service层业务逻辑"""
        return self.data_model.insert_row(row_index, row_data)

    def remove_row(self, row_index):
        """删除指定行 - Service层业务逻辑"""
        return self.data_model.remove_row(row_index)

    def move_row(self, from_index, to_index):
        """移动行 - Service层业务逻辑"""
        return self.data_model.move_row(from_index, to_index)

    def copy_row(self, row_index):
        """复制行 - Service层业务逻辑"""
        return self.data_model.copy_row(row_index)

    def paste_row(self, row_index, row_data):
        """粘贴行 - Service层业务逻辑"""
        return self.data_model.paste_row(row_index, row_data)

    def copy_column(self, col_index):
        """复制列 - Service层业务逻辑"""
        return self.data_model.copy_column(col_index)

    def paste_column(self, col_index, column_data):
        """粘贴列 - Service层业务逻辑"""
        return self.data_model.paste_column(col_index, column_data)

    def get_cell_value(self, row_index, col_index):
        """获取单元格值 - Service层数据访问"""
        return self.data_model.get_cell_value(row_index, col_index)

    def set_cell_value(self, row_index, col_index, value):
        """设置单元格值 - Service层数据修改"""
        return self.data_model.set_cell_value(row_index, col_index, value)

    def find_by_content(self, search_text):
        """通过内容查找单元格 - Service层查询功能"""
        return self.data_model.find_by_content(search_text)