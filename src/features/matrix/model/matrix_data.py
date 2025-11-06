# src/features/matrix/model/matrix_data.py
class MatrixData:
    """Matrix数据模型 - Model层"""

    def __init__(self):
        self.headers = ["Test Item", "PARA", "Test Method", "Condition", "Requirement", "Remark"]
        self.rows = [
            ["1", "", "", "", "", ""],  # 默认第一行
            ["", "", "", "", "", ""]    # 默认第二行（空白行）
        ]
        self.column_count = 6  # 初始列数
        self.protected_columns = 5  # 保护的默认列数
        self.protected_rows = [0, -1]  # 保护的行索引（第一行和最后一行）
        
        # 设置最后一行首列内容为"Sample size"
        self.rows[-1][0] = "Sample size"

    def add_column(self, column_name="", position=None):
        """添加新列 - Model层业务规则"""
        if not column_name:
            column_name = f"Column {self.column_count + 1}"
        
        # 如果没有指定位置，则添加到末尾（但确保在"Remark"列之前）
        if position is None:
            # 在"Remark"列前插入新列
            position = len(self.headers) - 1
            self.headers.insert(position, column_name)
            for row in self.rows:
                row.insert(position, "")
        else:
            # 检查位置是否有效
            if position < self.protected_columns:
                position = self.protected_columns  # 至少在保护列之后
            # 确保不在"Remark"列之后插入
            if position >= len(self.headers):
                position = len(self.headers) - 1
                
            self.headers.insert(position, column_name)
            for row in self.rows:
                row.insert(position, "")
                
        self.column_count += 1
        return True

    def move_column(self, from_index, to_index):
        """移动列 - Model层业务规则"""
        # 检查索引是否有效
        if (from_index < self.protected_columns or to_index < self.protected_columns or
            from_index >= len(self.headers) or to_index >= len(self.headers) or
            from_index < 0 or to_index < 0 or
            from_index == len(self.headers) - 1 or to_index == len(self.headers) - 1):  # 不能移动"Remark"列
            return False
            
        # 移动表头
        column_header = self.headers.pop(from_index)
        self.headers.insert(to_index, column_header)
        
        # 移动每一行的数据
        for row in self.rows:
            cell_value = row.pop(from_index)
            row.insert(to_index, cell_value)
            
        return True

    def remove_column(self, column_index):
        """删除指定列 - Model层业务规则"""
        # 防止删除受保护的默认列和"Remark"列
        if column_index < self.protected_columns or column_index == len(self.headers) - 1:
            return False
        if column_index < len(self.headers) and column_index >= 0:
            self.headers.pop(column_index)
            for row in self.rows:
                if column_index < len(row):
                    row.pop(column_index)
            self.column_count -= 1
            return True
        return False

    def add_row(self, row_data=None):
        """添加新行 - Model层业务规则"""
        # 确保不添加在第一行之前或最后一行之后
        if row_data is None:
            row_data = [""] * len(self.headers)
        # 插入到倒数第二行位置（在最后一行之前）
        self.rows.insert(-1, row_data) if len(self.rows) > 0 else self.rows.append(row_data)
        # 确保最后一行首列始终是"Sample size"
        self.rows[-1][0] = "Sample size"
        return True

    def insert_row(self, row_index, row_data=None):
        """在指定位置插入新行 - Model层业务规则"""
        # 检查行索引是否有效
        if row_index < 0 or row_index >= len(self.rows):
            return False
            
        # 防止在受保护的行位置插入（第一行和最后一行）
        if row_index == 0 or row_index == len(self.rows) - 1:
            return False
            
        if row_data is None:
            row_data = [""] * len(self.headers)
            
        # 在指定位置插入新行
        self.rows.insert(row_index, row_data)
        # 确保最后一行首列始终是"Sample size"
        self.rows[-1][0] = "Sample size"
        return True

    def remove_row(self, row_index):
        """删除指定行 - Model层业务规则"""
        # 防止删除受保护的行（第一行和最后一行）
        if row_index in self.protected_rows or row_index == len(self.rows) - 1 or row_index < 0:
            return False
        if row_index < len(self.rows):
            self.rows.pop(row_index)
            # 确保最后一行首列始终是"Sample size"
            self.rows[-1][0] = "Sample size"
            return True
        return False

    def move_row(self, from_index, to_index):
        """移动行 - Model层业务规则"""
        # 检查索引是否有效
        if (from_index <= 0 or from_index >= len(self.rows) - 1 or 
            to_index <= 0 or to_index >= len(self.rows) - 1 or
            from_index < 0 or to_index < 0):
            return False
            
        # 移动行数据
        row_data = self.rows.pop(from_index)
        self.rows.insert(to_index, row_data)
        
        # 确保最后一行首列始终是"Sample size"
        self.rows[-1][0] = "Sample size"
        return True

    def copy_row(self, row_index):
        """复制行 - Model层业务规则"""
        # 检查索引是否有效
        if row_index < 0 or row_index >= len(self.rows):
            return None
            
        # 返回行数据的副本（包括第一列序号）
        row_data = self.rows[row_index][:]
        # 不再清空第一列（序号列）的值
        # row_data[0] = ""
        return row_data

    def paste_row(self, row_index, row_data):
        """粘贴行 - Model层业务规则"""
        # 检查索引是否有效
        if row_index < 0 or row_index >= len(self.rows):
            return False
            
        # 检查数据是否有效
        if row_data is None or len(row_data) != len(self.headers):
            return False
            
        # 保护行不能被粘贴覆盖
        if row_index == 0 or row_index == len(self.rows) - 1:
            return False
            
        # 更新行数据
        for i in range(len(row_data)):
            self.rows[row_index][i] = row_data[i]
            
        # 确保最后一行首列始终是"Sample size"
        self.rows[-1][0] = "Sample size"
        return True

    def copy_column(self, col_index):
        """复制列 - Model层业务规则"""
        # 检查索引是否有效
        if col_index < 0 or col_index >= len(self.headers):
            return None
            
        # 返回列数据的副本
        column_data = []
        for row in self.rows:
            column_data.append(row[col_index])
        return column_data

    def paste_column(self, col_index, column_data):
        """粘贴列 - Model层业务规则"""
        # 检查索引是否有效
        if col_index < 0 or col_index >= len(self.headers):
            return False
            
        # 检查数据是否有效
        if column_data is None or len(column_data) != len(self.rows):
            return False
            
        # 保护列不能被粘贴覆盖（前5列和最后一列）
        if col_index < 5 or col_index == len(self.headers) - 1:
            return False
            
        # 更新列数据
        for i in range(len(column_data)):
            self.rows[i][col_index] = column_data[i]
            
        # 确保最后一行首列始终是"Sample size"
        self.rows[-1][0] = "Sample size"
        return True

    def get_cell_value(self, row_index, col_index):
        """获取单元格值 - Model层数据访问"""
        if row_index < len(self.rows) and col_index < len(self.rows[row_index]):
            return self.rows[row_index][col_index]
        return ""

    def set_cell_value(self, row_index, col_index, value):
        """设置单元格值 - Model层数据修改"""
        if row_index < len(self.rows) and col_index < len(self.rows[row_index]):
            self.rows[row_index][col_index] = value
            # 确保最后一行首列始终是"Sample size"
            if row_index == len(self.rows) - 1 and col_index == 0:
                self.rows[-1][0] = "Sample size" if not value else value
            return True
        return False

    def find_by_content(self, search_text):
        """通过内容查找单元格 - Model层查询功能"""
        results = []
        for row_idx, row in enumerate(self.rows):
            for col_idx, cell_value in enumerate(row):
                if search_text.lower() in cell_value.lower():
                    results.append({
                        'row': row_idx,
                        'column': col_idx,
                        'value': cell_value,
                        'header': self.headers[col_idx] if col_idx < len(self.headers) else ''
                    })
        return results

    def set_sample_size_row(self):
        """设置最后一行的首列内容为'Sample size'"""
        if len(self.rows) > 0:
            # 确保有足够的行
            while len(self.rows) < 3:  # 至少要有3行才能有专门的sample size行
                self.add_row()
                
            # 设置最后一行首列为"Sample size"
            self.rows[-1][0] = "Sample size"