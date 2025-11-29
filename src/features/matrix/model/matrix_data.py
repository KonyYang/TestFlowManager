class MatrixData:
    """Matrix数据模型 - Model层"""

    def __init__(self):
        self.merged_cells_info = []
        # 使用字母标识作为列标题
        self.headers = []
        for i in range(7):  # 7列使用字母标识A-G
            self.headers.append(self._column_index_to_letter(i))
        
        # 数据行，第一行是原来的表头内容
        self.rows = [
            ["Test Item", "Section", "Test Method", "Condition", "Requirement", "1", "Notes"],  # 表头行
            ["Visual Examination", "", "EIA-364-18B", "10x min magnification", "No detrimental condition", "1", ""],  # 数据行1
            ["Sample size", "", "", "", "", "5", ""],    # 数据行2
            ["Time", "", "", "", "", "", ""],  # Time行
            ["Fee", "", "", "", "", "", ""],   # Fee行
        ]
        self.column_count = 7  # 初始列数为7列
        self.protected_columns = 0  # 没有保护列
        self.protected_rows = []  # 没有保护行

    def _column_index_to_letter(self, index):
        """将列索引转换为字母标识"""
        # A-Z: 0-25
        if index < 26:
            return chr(ord('A') + index)
        # AA-AZ: 26-51
        elif index < 702:  # 26 + 26*26
            return chr(ord('A') + (index // 26) - 1) + chr(ord('A') + (index % 26))
        # AAA等更长的标识暂不考虑
        else:
            return f"Col{index}"

    def _reorder_all_columns(self):
        """重新排列所有列的标签"""
        # 重新计算所有列的标签（A, B, C, ...）
        for i in range(len(self.headers)):
            self.headers[i] = self._column_index_to_letter(i)

    def add_column(self, column_name="", position=None):
        """添加新列 - Model层业务规则"""
        if not column_name:
            # 使用字母标识作为默认列名
            column_name = self._column_index_to_letter(len(self.headers))
        
        # 如果没有指定位置，则添加到末尾
        if position is None:
            position = len(self.headers)
            self.headers.append(column_name)
            for row in self.rows:
                row.append("")
        else:
            # 检查位置是否有效
            if position < 0:
                position = 0
            elif position > len(self.headers):
                position = len(self.headers)
                
            self.headers.insert(position, column_name)
            for row in self.rows:
                row.insert(position, "")
                
        self.column_count += 1
        # 重新排列所有列标签
        self._reorder_all_columns()
        return True

    def insert_column(self, column_index, column_name=""):
        """在指定位置插入新列 - Model层业务规则"""
        return self.add_column(column_name, column_index)

    def move_column(self, from_index, to_index):
        """移动列 - Model层业务规则"""
        # 检查索引是否有效
        if (from_index >= len(self.headers) or to_index >= len(self.headers) or
            from_index < 0 or to_index < 0):
            return False
            
        # 移动表头
        column_header = self.headers.pop(from_index)
        self.headers.insert(to_index, column_header)
        
        # 移动每一行的数据
        for row in self.rows:
            cell_value = row.pop(from_index)
            row.insert(to_index, cell_value)
            
        # 重新排列所有列标签
        self._reorder_all_columns()
        return True

    def remove_column(self, column_index):
        """删除指定列 - Model层业务规则"""
        if column_index < len(self.headers) and column_index >= 0:
            self.headers.pop(column_index)
            for row in self.rows:
                if column_index < len(row):
                    row.pop(column_index)
            self.column_count -= 1
            # 重新排列所有列标签
            self._reorder_all_columns()
            return True
        return False

    def add_row(self, row_data=None):
        """添加新行 - Model层业务规则"""
        if row_data is None:
            row_data = [""] * len(self.headers)
        # 添加到末尾
        self.rows.append(row_data)
        return True

    def insert_row(self, row_index, row_data=None):
        """在指定位置插入新行 - Model层业务规则"""
        # 检查行索引是否有效
        if row_index < 0 or row_index > len(self.rows):
            return False
            
        if row_data is None:
            row_data = [""] * len(self.headers)
        self.rows.insert(row_index, row_data)
        return True

    def remove_row(self, row_index):
        """删除指定行 - Model层业务规则"""
        if row_index < len(self.rows) and row_index >= 0:
            # 删除行
            self.rows.pop(row_index)
            return True
        return False

    def adjust_spans_for_row_removal(self, removed_row_index):
        """
        调整由于行删除而受影响的单元格跨度
        """
        # 这个方法将在视图层处理，因为需要访问QTableWidget的特定方法
        pass

    def move_row(self, from_index, to_index):
        """移动行 - Model层业务规则"""
        # 检查索引是否有效
        if (from_index >= len(self.rows) or to_index >= len(self.rows) or
            from_index < 0 or to_index < 0):
            return False
            
        # 移动行数据
        row_data = self.rows.pop(from_index)
        self.rows.insert(to_index, row_data)
        return True

    def copy_row(self, row_index):
        """复制行 - Model层业务规则"""
        # 检查索引是否有效
        if row_index < 0 or row_index >= len(self.rows):
            return None
            
        # 返回行数据的副本
        row_data = self.rows[row_index][:]
        return row_data

    def paste_row(self, row_index, row_data):
        """粘贴行 - Model层业务规则"""
        # 检查索引是否有效
        if row_index < 0 or row_index >= len(self.rows):
            return False
            
        # 检查数据是否有效
        if row_data is None or len(row_data) != len(self.headers):
            return False
            
        # 更新行数据
        for i in range(len(row_data)):
            self.rows[row_index][i] = row_data[i]
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
            
        # 更新列数据
        for i in range(len(column_data)):
            self.rows[i][col_index] = column_data[i]
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