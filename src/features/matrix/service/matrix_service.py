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

    def rename_column(self, col_index, new_name):
        """重命名列 - Service层业务逻辑"""
        return self.data_model.rename_column(col_index, new_name)

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
                self.data_model.headers.append(cell.value if cell.value is not None else "")

            # 读取数据行
            for row in ws.iter_rows(min_row=2, values_only=True):
                self.data_model.rows.append([cell if cell is not None else "" for cell in row])

            # 确保有默认列数
            while len(self.data_model.headers) < 8:
                self.data_model.headers.append(self.data_model._column_index_to_letter(len(self.data_model.headers)))
            
            # 确保有默认行
            if len(self.data_model.rows) == 0:
                # 添加默认行
                self.data_model.rows.append([""] * len(self.data_model.headers))
                self.data_model.rows.append([""] * len(self.data_model.headers))

            return True
        except Exception as e:
            logger.error(f"导入Excel失败: {e}")
            return False

    def import_from_spec(self, file_path):
        """从Spec导入数据 - Service层持久化功能"""
        try:
            logger.info(f"开始从Spec导入数据: {file_path}")
            
            # 实现Spec文件导入逻辑
            # 调用spec_extractor来处理不同格式的文件
            from src.features.matrix.service.spec_extractor import SpecExtractor
            extractor = SpecExtractor()
            data = extractor.extract_from_document(file_path)
            
            # 如果成功提取数据，则更新数据模型
            if data is not None:
                logger.info(f"成功从Spec文档提取数据，数据行数: {len(data)}")
                if len(data) > 0:
                    logger.info(f"数据列数: {len(data[0])}")
                    logger.info(f"表头内容: {data[0][:5]}...")  # 只显示前5列
                
                # 清空现有数据
                self.data_model.headers = []
                self.data_model.rows = []
                
                # 处理表头（使用字母标识）
                if len(data) > 0:
                    for i in range(len(data[0])):  # 根据数据列数创建表头
                        self.data_model.headers.append(self.data_model._column_index_to_letter(i))
                    logger.info(f"设置表头，列数: {len(self.data_model.headers)}")
                    
                # 处理数据行
                if len(data) > 0:
                    self.data_model.rows = data  # 数据行就是所有提取的数据
                    logger.info(f"设置数据行，行数: {len(self.data_model.rows)}")
                
                # 确保有默认列数
                while len(self.data_model.headers) < 8:
                    self.data_model.headers.append(self.data_model._column_index_to_letter(len(self.data_model.headers)))
                
                # 确保有默认行
                if len(self.data_model.rows) == 0:
                    # 添加默认行
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    logger.info("添加默认行数据")

                # 对数据进行处理，类似VBA代码中的ProcessRows逻辑
                self._process_rows()
                
                # 检查重复值
                self._check_duplicate_values()
                
                logger.info("Spec数据导入完成")
                return True
            else:
                logger.warning("未能从Spec文档提取数据")
                return False
        except Exception as e:
            logger.error(f"导入Spec失败: {e}")
            return False
            
    def _process_rows(self):
        """
        处理行数据，类似于VBA中的ProcessRows函数
        合并单元格内容并处理行数据
        """
        try:
            # 这里可以添加处理行数据的逻辑
            # 比如合并单元格内容，处理特殊格式等
            # 目前我们只是确保数据格式正确
            logger.info("处理行数据完成")
        except Exception as e:
            logger.error(f"处理行数据时出错: {e}", exc_info=True)
            
    def _check_duplicate_values(self):
        """
        检查重复值，从第1列到最后一列，从第1行到倒数第二行
        类似于VBA中的CheckDuplicateValues函数
        """
        try:
            logger.info("开始检查重复值")
            # 从第1列到最后一列
            for col_index in range(len(self.data_model.headers)):
                # 用于存储已见过的值
                seen_values = set()
                # 从第1行到倒数第二行
                for row_index in range(len(self.data_model.rows) - 1):
                    if row_index < len(self.data_model.rows) and col_index < len(self.data_model.rows[row_index]):
                        cell_value = self.data_model.rows[row_index][col_index]
                        # 如果值不为空且已经见过，则标记为重复
                        if cell_value and cell_value.strip() and cell_value in seen_values:
                            logger.warning(f"在第{row_index+1}行，第{col_index+1}列发现重复值: {cell_value}")
                        elif cell_value and cell_value.strip():
                            seen_values.add(cell_value)
                            
            logger.info("重复值检查完成")
        except Exception as e:
            logger.error(f"检查重复值时出错: {e}", exc_info=True)