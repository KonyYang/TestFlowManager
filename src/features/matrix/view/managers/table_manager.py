# src/features/matrix/view/managers/table_manager.py
from PyQt5.QtWidgets import QTableWidgetItem, QInputDialog, QMessageBox
from src.core.logger import logger


class TableManager:
    """表格管理器 - 处理表格相关的操作"""
    
    def __init__(self, view, command_bridge=None):
        """初始化表格管理器。
        
        Args:
            view: MatrixPage 实例，用于获取表格控件和数据模型
            command_bridge: MatrixTableCommandBridge 实例，用于行列命令转发。
                            如果为 None，则回退到 view 的旧方法（兼容性）。
        """
        self.view = view
        self._command_bridge = command_bridge
        
    def update_table(self):
        """更新表格显示"""
        table_widget = self.view.get_table_widget()
        data_model = self.view.get_data_model()
        # 断开信号连接以避免在更新过程中触发事件
        try:
            table_widget.itemChanged.disconnect(self.view.handle_item_changed)
        except TypeError:
            # 如果信号尚未连接，则忽略错误
            pass
        
        try:
            # 清空现有内容
            table_widget.clear()
            
            # 设置表头
            table_widget.setColumnCount(len(data_model.headers))
            table_widget.setHorizontalHeaderLabels(data_model.headers)
            
            # 设置行数和数据
            table_widget.setRowCount(len(data_model.rows))
            for row_idx, row_data in enumerate(data_model.rows):
                for col_idx, cell_value in enumerate(row_data):
                    if col_idx < len(row_data):  # 确保不越界
                        item = QTableWidgetItem(str(cell_value))
                        table_widget.setItem(row_idx, col_idx, item)
            
            # 应用合并单元格（如果有）
            self.apply_merged_cells()
        finally:
            # 重新连接信号
            table_widget.itemChanged.connect(self.view.handle_item_changed)
            
    def apply_merged_cells(self):
        """应用合并单元格"""
        table_widget = self.view.get_table_widget()
        # 清除现有的合并单元格
        for row in range(table_widget.rowCount()):
            for col in range(table_widget.columnCount()):
                table_widget.setSpan(row, col, 1, 1)
        
        # 应用存储的合并单元格信息
        for merge_info in self.view.get_data_model().merged_cells_info:
            top_row = merge_info['top_row']
            left_col = merge_info['left_col']
            row_count = merge_info['row_count']
            col_count = merge_info['col_count']
            
            # 检查边界
            if (top_row + row_count <= table_widget.rowCount() and
                left_col + col_count <= table_widget.columnCount()):
                table_widget.setSpan(top_row, left_col, row_count, col_count)
                
    def add_row(self):
        """添加行"""
        self._bridge_append_row()
        self.update_table()

    def insert_row(self, row):
        """插入行"""
        self._bridge_insert_row(row)
        self.update_table()

    def remove_row(self, row):
        """删除行"""
        reply = QMessageBox.question(
            self.view, 
            "确认删除", 
            f"确定要删除第 {row+1} 行吗？", 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._bridge_remove_row(row)
            self.update_table()

    def move_row(self, row):
        """移动行"""
        if row >= 0:
            new_position, ok = QInputDialog.getInt(
                self.view, "移动行", "请输入目标行位置(从0开始):", 
                row, 0, len(self.view.get_data_model().rows)-1)

            if ok and new_position != row:
                if self._bridge_move_row(row, new_position):
                    self.update_table()
                    return True
                else:
                    QMessageBox.warning(self.view, "操作失败", "行移动失败")
        else:
            QMessageBox.warning(self.view, "操作失败", "请选择一行")
        return False

    def copy_row(self, row):
        """复制行"""
        if row >= 0:
            copied_row_data = self._bridge_copy_row(row)
            self._bridge_set_copied_row_data(copied_row_data)
        return self._bridge_get_copied_row_data()

    def paste_row(self, row):
        """粘贴行"""
        copied_row_data = self._bridge_get_copied_row_data()
        if row >= 0 and copied_row_data is not None:
            result = self._bridge_paste_row(row, copied_row_data)
            if result:
                self.update_table()
            return result
        return False

    def add_column(self):
        """添加列"""
        self._bridge_append_column()
        self.update_table()

    def insert_column(self, col):
        """插入列"""
        self._bridge_insert_column(col)
        self.update_table()

    def remove_column(self, col):
        """删除列"""
        reply = QMessageBox.question(
            self.view, 
            "确认删除", 
            f"确定要删除第 {col+1} 列吗？", 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._bridge_remove_column(col)
            self.update_table()

    def move_column(self, col):
        """移动列"""
        if col >= 0:
            new_position, ok = QInputDialog.getInt(
                self.view, "移动列", "请输入目标列位置(从0开始):", 
                col, 0, len(self.view.get_data_model().headers)-1)

            if ok and new_position != col:
                if self._bridge_move_column(col, new_position):
                    self.update_table()
                    return True
                else:
                    QMessageBox.warning(self.view, "操作失败", "列移动失败")
        else:
            QMessageBox.warning(self.view, "操作失败", "请选择一列")
        return False

    def copy_column(self, col):
        """复制列"""
        if col >= 0:
            copied_col_data = self._bridge_copy_column(col)
            self._bridge_set_copied_col_data(copied_col_data)
        return self._bridge_get_copied_col_data()

    def paste_column(self, col):
        """粘贴列"""
        copied_col_data = self._bridge_get_copied_col_data()
        if col >= 0 and copied_col_data is not None:
            result = self._bridge_paste_column(col, copied_col_data)
            if result:
                self.update_table()
            return result
        return False

    # ==================== Bridge delegation helpers ====================
    # 这些方法封装了到 CommandBridge（优先）或 view 旧方法（兼容回退）的转发

    def _bridge_append_row(self):
        if self._command_bridge:
            self._command_bridge.append_row()
        else:
            self.view.append_row_to_model()

    def _bridge_insert_row(self, row):
        if self._command_bridge:
            self._command_bridge.insert_row(row)
        else:
            self.view.insert_row_to_model(row)

    def _bridge_remove_row(self, row):
        if self._command_bridge:
            self._command_bridge.remove_row(row)
        else:
            self.view.remove_row_from_model(row)

    def _bridge_move_row(self, row, new_position):
        if self._command_bridge:
            return self._command_bridge.move_row(row, new_position)
        return self.view.move_row_in_model(row, new_position)

    def _bridge_copy_row(self, row):
        if self._command_bridge:
            return self._command_bridge.copy_row(row)
        return self.view.copy_row_from_model(row)

    def _bridge_paste_row(self, row, copied_row_data):
        if self._command_bridge:
            return self._command_bridge.paste_row(row, copied_row_data)
        return self.view.paste_row_to_model(row, copied_row_data)

    def _bridge_get_copied_row_data(self):
        if self._command_bridge:
            return self._command_bridge.get_copied_row_data()
        return self.view.get_copied_row_data()

    def _bridge_set_copied_row_data(self, data):
        if self._command_bridge:
            self._command_bridge.set_copied_row_data(data)
        else:
            self.view.set_copied_row_data(data)

    def _bridge_append_column(self):
        if self._command_bridge:
            self._command_bridge.append_column()
        else:
            self.view.append_column_to_model()

    def _bridge_insert_column(self, col):
        if self._command_bridge:
            self._command_bridge.insert_column(col)
        else:
            self.view.insert_column_to_model(col)

    def _bridge_remove_column(self, col):
        if self._command_bridge:
            self._command_bridge.remove_column(col)
        else:
            self.view.remove_column_from_model(col)

    def _bridge_move_column(self, col, new_position):
        if self._command_bridge:
            return self._command_bridge.move_column(col, new_position)
        return self.view.move_column_in_model(col, new_position)

    def _bridge_copy_column(self, col):
        if self._command_bridge:
            return self._command_bridge.copy_column(col)
        return self.view.copy_column_from_model(col)

    def _bridge_paste_column(self, col, copied_col_data):
        if self._command_bridge:
            return self._command_bridge.paste_column(col, copied_col_data)
        return self.view.paste_column_to_model(col, copied_col_data)

    def _bridge_get_copied_col_data(self):
        if self._command_bridge:
            return self._command_bridge.get_copied_col_data()
        return self.view.get_copied_col_data()

    def _bridge_set_copied_col_data(self, data):
        if self._command_bridge:
            self._command_bridge.set_copied_col_data(data)
        else:
            self.view.set_copied_col_data(data)
