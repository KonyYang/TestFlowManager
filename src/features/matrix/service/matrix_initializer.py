# src/features/matrix/service/matrix_initializer.py
from src.core import logger


class MatrixInitializer:
    """Matrix初始化器 - 处理Matrix的初始化逻辑"""

    def __init__(self, data_model):
        self.data_model = data_model

    def initialize_matrix(self, extract_data=False):
        """初始化Matrix - 插入指定的列和行"""
        try:
            # 检查是否需要处理列
            first_row = self.data_model.rows[0] if self.data_model.rows else []
            
            # 查找现有的"Test Method", "Condition", "Requirement"列
            test_method_col = -1
            condition_col = -1
            requirement_col = -1
            
            for i, cell in enumerate(first_row):
                if cell == "Test Method":
                    test_method_col = i
                elif cell == "Condition":
                    condition_col = i
                elif cell == "Requirement":
                    requirement_col = i
            
            # 检查是否已经在正确位置(2,3,4)
            correctly_positioned = (test_method_col == 2 and 
                                  condition_col == 3 and 
                                  requirement_col == 4)
            
            # 如果没有在正确位置，则需要移动或插入
            if not correctly_positioned:
                # 收集要移动的列数据
                test_method_data = None
                condition_data = None
                requirement_data = None
                
                # 提取现有列数据
                if test_method_col >= 0:
                    test_method_data = []
                    for row in self.data_model.rows:
                        if test_method_col < len(row):
                            test_method_data.append(row[test_method_col])
                
                if condition_col >= 0:
                    condition_data = []
                    for row in self.data_model.rows:
                        if condition_col < len(row):
                            condition_data.append(row[condition_col])
                
                if requirement_col >= 0:
                    requirement_data = []
                    for row in self.data_model.rows:
                        if requirement_col < len(row):
                            requirement_data.append(row[requirement_col])
                
                # 从后往前删除现有列，避免索引变化影响
                cols_to_remove = sorted([test_method_col, condition_col, requirement_col], reverse=True)
                for col_idx in cols_to_remove:
                    if col_idx >= 0 and col_idx < len(self.data_model.headers):
                        self.data_model.headers.pop(col_idx)
                        for row in self.data_model.rows:
                            if col_idx < len(row):
                                row.pop(col_idx)
                        # 调整剩余列索引
                        if test_method_col > col_idx:
                            test_method_col -= 1
                        if condition_col > col_idx:
                            condition_col -= 1
                        if requirement_col > col_idx:
                            requirement_col -= 1
                
                # 在位置2,3,4插入缺失的列
                # 先确保有足够的列
                while len(self.data_model.headers) < 2:
                    self.data_model.headers.append("")
                    for row in self.data_model.rows:
                        row.append("")
                
                # 插入缺失的列
                if test_method_data is None:
                    # 创建新的Test Method列
                    self.data_model.headers.insert(2, "Test Method")
                    for row_idx, row in enumerate(self.data_model.rows):
                        if row_idx == 0:
                            row.insert(2, "Test Method")
                        else:
                            row.insert(2, "")
                else:
                    # 插入已有的Test Method列
                    self.data_model.headers.insert(2, "Test Method")
                    for row_idx, (row, data) in enumerate(zip(self.data_model.rows, test_method_data)):
                        row.insert(2, data)
                
                if condition_data is None:
                    # 创建新的Condition列
                    self.data_model.headers.insert(3, "Condition")
                    for row_idx, row in enumerate(self.data_model.rows):
                        if row_idx == 0:
                            row.insert(3, "Condition")
                        else:
                            row.insert(3, "")
                else:
                    # 插入已有的Condition列
                    self.data_model.headers.insert(3, "Condition")
                    for row_idx, (row, data) in enumerate(zip(self.data_model.rows, condition_data)):
                        row.insert(3, data)
                
                if requirement_data is None:
                    # 创建新的Requirement列
                    self.data_model.headers.insert(4, "Requirement")
                    for row_idx, row in enumerate(self.data_model.rows):
                        if row_idx == 0:
                            row.insert(4, "Requirement")
                        else:
                            row.insert(4, "")
                else:
                    # 插入已有的Requirement列
                    self.data_model.headers.insert(4, "Requirement")
                    for row_idx, (row, data) in enumerate(zip(self.data_model.rows, requirement_data)):
                        row.insert(4, data)
            
            # 检查是否已经存在Notes列（检查第一行的最后一列）
            has_remark = False
            if len(first_row) > 0 and first_row[-1] == "Notes":
                has_remark = True
            
            # 只有当Notes列不存在时才添加
            if not has_remark:
                # 添加"Notes"列到末尾
                self.data_model.headers.append("Notes")
                for row_idx, row in enumerate(self.data_model.rows):
                    if row_idx == 0:  # 首行填充列名
                        row.append("Notes")
                    else:  # 其他行插入空值
                        row.append("")
            
            # 处理"Time"和"Fee"行，确保它们在正确的位置
            # 查找现有的"Time"和"Fee"行
            time_row_index = -1
            fee_row_index = -1
            
            for i, row in enumerate(self.data_model.rows):
                if row and row[0] == "Time":
                    time_row_index = i
                elif row and row[0] == "Fee":
                    fee_row_index = i
            
            # 确保Time行在倒数第二行，Fee行在最后一行
            time_row_data = None
            fee_row_data = None
            
            # 提取现有的Time和Fee行数据
            if time_row_index >= 0:
                time_row_data = self.data_model.rows[time_row_index]
            
            if fee_row_index >= 0:
                fee_row_data = self.data_model.rows[fee_row_index]
            
            # 删除现有的Time和Fee行
            rows_to_remove = sorted([time_row_index, fee_row_index], reverse=True)
            for row_idx in rows_to_remove:
                if row_idx >= 0 and row_idx < len(self.data_model.rows):
                    self.data_model.rows.pop(row_idx)
            
            # 确保有Time和Fee行数据
            if time_row_data is None:
                time_row_data = [""] * len(self.data_model.headers)
                time_row_data[0] = "Time"
            
            if fee_row_data is None:
                fee_row_data = [""] * len(self.data_model.headers)
                fee_row_data[0] = "Fee"
            
            # 在正确位置添加Time和Fee行（倒数第二行和最后一行）
            self.data_model.rows.append(time_row_data)  # 倒数第一行（在添加Fee之前）
            self.data_model.rows.append(fee_row_data)   # 最后一行
            
            # 重新排列所有列的标签（使用字母标识）
            # 从第1列开始重新编号为数据列（A, B, C...）
            for i in range(len(self.data_model.headers)):
                self.data_model.headers[i] = self.data_model._column_index_to_letter(i)
            
            # 如果需要提取数据，则进行提取
            if extract_data:
                self._extract_and_store_data()
            
            return True
        except Exception as e:
            logger.error(f"初始化Matrix失败: {e}")
            return False