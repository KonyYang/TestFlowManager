# src/features/matrix/service/matrix_cell_service.py
from PyQt5.QtWidgets import QUndoCommand, QUndoStack, QTableWidgetItem
from PyQt5.QtCore import Qt


class MergeCellsCommand(QUndoCommand):
    """合并单元格命令"""
    
    def __init__(self, table_widget, selected_ranges, description="合并单元格"):
        super().__init__(description)
        self.table_widget = table_widget
        self.selected_ranges = [range_ for range_ in selected_ranges]  # 复制选中区域信息
        self.merged_cells_info = []  # 存储合并前的单元格信息
        
        # 记录合并前的信息
        if len(selected_ranges) > 1:
            # 多个选中区域的情况
            min_row = min(range_.topRow() for range_ in selected_ranges)
            max_row = max(range_.bottomRow() for range_ in selected_ranges)
            min_col = min(range_.leftColumn() for range_ in selected_ranges)
            max_col = max(range_.rightColumn() for range_ in selected_ranges)
            
            self.merge_info = {
                'type': 'multi_range',
                'top_row': min_row,
                'left_col': min_col,
                'bottom_row': max_row,
                'right_col': max_col,
                'row_count': max_row - min_row + 1,
                'col_count': max_col - min_col + 1
            }
        elif len(selected_ranges) == 1:
            range_ = selected_ranges[0]
            self.merge_info = {
                'type': 'single_range',
                'top_row': range_.topRow(),
                'left_col': range_.leftColumn(),
                'bottom_row': range_.bottomRow(),
                'right_col': range_.rightColumn(),
                'row_count': range_.rowCount(),
                'col_count': range_.columnCount()
            }
        
        # 记录原始单元格内容
        self.original_contents = {}
        self.original_alignments = {}
        
        # 记录将要被合并区域内的所有单元格的原始信息
        if self.merge_info['type'] == 'multi_range':
            top_row = self.merge_info['top_row']
            left_col = self.merge_info['left_col']
            bottom_row = self.merge_info['bottom_row']
            right_col = self.merge_info['right_col']
        else:
            top_row = self.merge_info['top_row']
            left_col = self.merge_info['left_col']
            bottom_row = self.merge_info['bottom_row']
            right_col = self.merge_info['right_col']
            
        for row in range(top_row, bottom_row + 1):
            for col in range(left_col, right_col + 1):
                item = self.table_widget.item(row, col)
                if item:
                    self.original_contents[(row, col)] = item.text()
                    self.original_alignments[(row, col)] = item.textAlignment()
                else:
                    self.original_contents[(row, col)] = ""
                    self.original_alignments[(row, col)] = 0

    def redo(self):
        """执行合并操作"""
        if self.merge_info['type'] == 'multi_range':
            top_row = self.merge_info['top_row']
            left_col = self.merge_info['left_col']
            row_count = self.merge_info['row_count']
            col_count = self.merge_info['col_count']
        else:
            top_row = self.merge_info['top_row']
            left_col = self.merge_info['left_col']
            row_count = self.merge_info['row_count']
            col_count = self.merge_info['col_count']
            
        # 执行合并
        self.table_widget.setSpan(top_row, left_col, row_count, col_count)
        
        # 保存合并后的单元格信息
        self.merged_cells_info = []
        if self.merge_info['type'] == 'multi_range':
            bottom_row = self.merge_info['bottom_row']
            right_col = self.merge_info['right_col']
        else:
            bottom_row = self.merge_info['bottom_row']
            right_col = self.merge_info['right_col']
            
        for row in range(top_row, bottom_row + 1):
            for col in range(left_col, right_col + 1):
                if row != top_row or col != left_col:
                    item = self.table_widget.item(row, col)
                    if item:
                        self.merged_cells_info.append({
                            'row': row,
                            'col': col,
                            'text': item.text(),
                            'alignment': item.textAlignment()
                        })
                        item.setText("")
        
        # 设置合并后单元格的文本和对齐方式
        first_item = self.table_widget.item(top_row, left_col)
        if first_item:
            # 合并区域第一个单元格保留原有文本
            if (top_row, left_col) in self.original_contents:
                first_item.setText(self.original_contents[(top_row, left_col)])
            first_item.setTextAlignment(Qt.AlignCenter)

    def undo(self):
        """撤销合并操作"""
        if self.merge_info['type'] == 'multi_range':
            top_row = self.merge_info['top_row']
            left_col = self.merge_info['left_col']
            row_count = self.merge_info['row_count']
            col_count = self.merge_info['col_count']
        else:
            top_row = self.merge_info['top_row']
            left_col = self.merge_info['left_col']
            row_count = self.merge_info['row_count']
            col_count = self.merge_info['col_count']
            
        # 拆分单元格
        self.table_widget.setSpan(top_row, left_col, 1, 1)
        
        # 恢复被合并单元格的内容
        for cell_info in self.merged_cells_info:
            row = cell_info['row']
            col = cell_info['col']
            text = cell_info['text']
            alignment = cell_info['alignment']
            
            item = self.table_widget.item(row, col)
            if not item:
                item = QTableWidgetItem()
                self.table_widget.setItem(row, col, item)
            item.setText(text)
            item.setTextAlignment(alignment)
            
        # 恢复原始单元格内容和对齐方式
        if self.merge_info['type'] == 'multi_range':
            bottom_row = self.merge_info['bottom_row']
            right_col = self.merge_info['right_col']
        else:
            bottom_row = self.merge_info['bottom_row']
            right_col = self.merge_info['right_col']
            
        for row in range(top_row, bottom_row + 1):
            for col in range(left_col, right_col + 1):
                item = self.table_widget.item(row, col)
                if not item:
                    item = QTableWidgetItem()
                    self.table_widget.setItem(row, col, item)
                if (row, col) in self.original_contents:
                    item.setText(self.original_contents[(row, col)])
                if (row, col) in self.original_alignments:
                    item.setTextAlignment(self.original_alignments[(row, col)])


class SplitCellsCommand(QUndoCommand):
    """拆分单元格命令"""
    
    def __init__(self, table_widget, selected_ranges, description="拆分单元格"):
        super().__init__(description)
        self.table_widget = table_widget
        self.selected_ranges = [range_ for range_ in selected_ranges]  # 复制选中区域信息
        self.cells_to_split = []  # 存储需要拆分的单元格信息
        
        # 收集所有需要拆分的合并单元格信息
        for range_ in selected_ranges:
            for row in range(range_.topRow(), range_.bottomRow() + 1):
                for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                    row_span = table_widget.rowSpan(row, col)
                    col_span = table_widget.columnSpan(row, col)
                    if row_span > 1 or col_span > 1:
                        # 记录这个合并单元格的信息
                        self.cells_to_split.append({
                            'row': row,
                            'col': col,
                            'row_span': row_span,
                            'col_span': col_span
                        })

    def redo(self):
        """执行拆分操作"""
        for cell_info in self.cells_to_split:
            row = cell_info['row']
            col = cell_info['col']
            self.table_widget.setSpan(row, col, 1, 1)

    def undo(self):
        """撤销拆分操作（恢复合并状态）"""
        for cell_info in self.cells_to_split:
            row = cell_info['row']
            col = cell_info['col']
            row_span = cell_info['row_span']
            col_span = cell_info['col_span']
            self.table_widget.setSpan(row, col, row_span, col_span)


class MatrixCellService:
    """Matrix单元格服务 - 处理单元格合并/拆分相关操作"""
    
    def __init__(self):
        self.undo_stack = QUndoStack()
    
    def merge_or_split_cells(self, table_widget):
        """根据选中单元格的状态执行合并或拆分操作"""
        selected_ranges = table_widget.selectedRanges()
        
        if len(selected_ranges) == 0:
            return False
            
        # 检查选中的区域中是否包含已合并的单元格
        has_merged_cells = False
        
        # 遍历所有选中的区域
        for range_ in selected_ranges:
            # 遍历区域中的每个单元格
            for row in range(range_.topRow(), range_.bottomRow() + 1):
                for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                    # 检查单元格是否是合并的（行跨度或列跨度大于1）
                    row_span = table_widget.rowSpan(row, col)
                    col_span = table_widget.columnSpan(row, col)
                    if row_span > 1 or col_span > 1:
                        has_merged_cells = True
                        break
                if has_merged_cells:
                    break
            if has_merged_cells:
                break
        
        # 如果选中区域中包含已合并的单元格，则执行拆分操作
        if has_merged_cells:
            # 创建拆分命令并添加到撤销堆栈
            split_command = SplitCellsCommand(table_widget, selected_ranges, "拆分单元格")
            self.undo_stack.push(split_command)
        else:
            # 如果选中区域中没有已合并的单元格，则执行合并操作
            # 创建合并命令并添加到撤销堆栈
            merge_command = MergeCellsCommand(table_widget, selected_ranges, "合并单元格")
            self.undo_stack.push(merge_command)
            
        return True
    
    def clear_spans_for_row(self, table_widget, row_index):
        """
        清除指定行的合并单元格信息
        当删除行时调用此方法，确保不会留下无效的合并单元格引用
        """
        if row_index >= table_widget.rowCount():
            return
            
        # 处理被删除行中的合并单元格
        for col in range(table_widget.columnCount()):
            # 如果这个单元格是合并单元格的起始点
            row_span = table_widget.rowSpan(row_index, col)
            col_span = table_widget.columnSpan(row_index, col)
            
            if row_span > 1 or col_span > 1:
                # 拆分这个单元格
                table_widget.setSpan(row_index, col, 1, 1)
            
            # 处理跨越到这一行的合并单元格
            # 向上查找可能影响的合并单元格
            for search_row in range(min(row_index, table_widget.rowCount())):
                search_row_span = table_widget.rowSpan(search_row, col)
                search_col_span = table_widget.columnSpan(search_row, col)
                # 如果找到的起始点的合并范围包含了我们要删除的行
                if search_row + search_row_span > row_index:
                    # 调整行跨度
                    new_row_span = search_row_span - 1
                    if new_row_span >= 1:
                        table_widget.setSpan(search_row, col, new_row_span, search_col_span)
                    else:
                        # 如果行跨度小于1，就完全拆分这个单元格
                        table_widget.setSpan(search_row, col, 1, search_col_span)
    
    def clear_spans_for_column(self, table_widget, col_index):
        """
        清除指定列的合并单元格信息
        当删除列时调用此方法，确保不会留下无效的合并单元格引用
        """
        if col_index >= table_widget.columnCount():
            return
            
        # 处理被删除列中的合并单元格
        for row in range(table_widget.rowCount()):
            # 如果这个单元格是合并单元格的起始点
            row_span = table_widget.rowSpan(row, col_index)
            col_span = table_widget.columnSpan(row, col_index)
            
            if row_span > 1 or col_span > 1:
                # 拆分这个单元格
                table_widget.setSpan(row, col_index, 1, 1)
            
            # 处理跨越到这一列的合并单元格
            # 向左查找可能影响的合并单元格
            for search_col in range(min(col_index, table_widget.columnCount())):
                search_row_span = table_widget.rowSpan(row, search_col)
                search_col_span = table_widget.columnSpan(row, search_col)
                # 如果找到的起始点的合并范围包含了我们要删除的列
                if search_col + search_col_span > col_index:
                    # 调整列跨度
                    new_col_span = search_col_span - 1
                    if new_col_span >= 1:
                        table_widget.setSpan(row, search_col, search_row_span, new_col_span)
                    else:
                        # 如果列跨度小于1，就完全拆分这个单元格
                        table_widget.setSpan(row, search_col, search_row_span, 1)

    def can_undo(self):
        """检查是否可以撤销操作"""
        return self.undo_stack.canUndo()
        
    def can_redo(self):
        """检查是否可以重做操作"""
        return self.undo_stack.canRedo()
        
    def undo(self):
        """撤销操作"""
        if self.undo_stack.canUndo():
            self.undo_stack.undo()
            return True
        return False
        
    def redo(self):
        """重做操作"""
        if self.undo_stack.canRedo():
            self.undo_stack.redo()
            return True
        return False
        
    def undo_text(self):
        """获取撤销操作的文本描述"""
        return self.undo_stack.undoText()
        
    def redo_text(self):
        """获取重做操作的文本描述"""
        return self.undo_stack.redoText()