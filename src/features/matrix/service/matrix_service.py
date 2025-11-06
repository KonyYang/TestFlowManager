# src/features/matrix/service/matrix_service.py
from src.core import logger
from src.features.matrix.model.matrix_data import MatrixData
from src.utils.excel_utils import save_to_excel

class MatrixService:
    """Matrix服务层 - Service层"""

    def __init__(self):
        self.data_model = MatrixData()

    def add_column(self, column_name="", position=None):
        """添加新列 - Service层业务逻辑"""
        return self.data_model.add_column(column_name, position)

    def move_column(self, from_index, to_index):
        """移动列 - Service层业务逻辑"""
        return self.data_model.move_column(from_index, to_index)

    def remove_column(self, column_index):
        """删除指定列 - Service层业务逻辑"""
        return self.data_model.remove_column(column_index)

    def add_row(self, row_data=None):
        """添加新行 - Service层业务逻辑"""
        result = self.data_model.add_row(row_data)
        # 确保最后一行首列始终是"Sample size"
        if len(self.data_model.rows) > 0:
            self.data_model.rows[-1][0] = "Sample size"
        return result

    def insert_row(self, row_index, row_data=None):
        """在指定位置插入新行 - Service层业务逻辑"""
        result = self.data_model.insert_row(row_index, row_data)
        # 确保最后一行首列始终是"Sample size"
        if len(self.data_model.rows) > 0:
            self.data_model.rows[-1][0] = "Sample size"
        return result

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

    def export_to_excel(self, file_path):
        """导出到Excel - Service层持久化功能"""
        try:
            # 使用现有的excel_utils工具
            data = []
            # 添加表头
            data.append(self.data_model.headers)
            # 添加数据行
            for row in self.data_model.rows:
                data.append(row)

            return save_to_excel(file_path, data)
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return False

    def import_from_excel(self, file_path):
        """从Excel导入数据 - Service层持久化功能"""
        try:
            from openpyxl import load_workbook
            wb = load_workbook(file_path)
            ws = wb.active

            # 清空现有数据
            self.data_model.headers = []
            self.data_model.rows = []

            # 读取表头
            for cell in ws[1]:
                self.data_model.headers.append(cell.value)

            # 读取数据行
            for row in ws.iter_rows(min_row=2, values_only=True):
                self.data_model.rows.append(list(row))

            # 确保前5列是默认列
            default_headers = ["Test Item", "PARA", "Test Method", "Condition", "Requirement"]
            for i in range(min(5, len(self.data_model.headers))):
                self.data_model.headers[i] = default_headers[i]
            
            # 确保有"Remark"列作为最后一列
            if len(self.data_model.headers) <= 5:
                self.data_model.headers.append("Remark")
            elif self.data_model.headers[-1] != "Remark":
                self.data_model.headers.append("Remark")
            
            # 确保有默认行
            if len(self.data_model.rows) == 0:
                # 添加默认的第一行和第二行
                self.data_model.rows.append(["1", "", "", "", "", ""])
                self.data_model.rows.append(["", "", "", "", "", ""])
            
            # 确保最后一行首列是"Sample size"
            if len(self.data_model.rows) > 0:
                while len(self.data_model.rows) < 3:  # 确保至少有3行
                    self.data_model.rows.insert(-1, [""] * len(self.data_model.headers))
                self.data_model.rows[-1][0] = "Sample size"

            return True
        except Exception as e:
            logger.error(f"导入Excel失败: {e}")
            return False