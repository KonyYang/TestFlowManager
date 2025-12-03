# src/features/matrix/view/managers/table_manager.py
from PyQt5.QtWidgets import QTableWidgetItem
from src.core.logger import logger


class TableManager:
    """表格管理器 - 处理表格相关的操作"""
    
    def __init__(self, view, controller):
        self.view = view
        self.controller = controller
        
    def update_table(self):
        """更新表格显示"""
        # 移除更新表格显示的详细日志
        # 断开信号连接以避免在更新过程中触发事件
        try:
            self.view.table_widget.itemChanged.disconnect(self.view._on_item_changed)
        except TypeError:
            # 如果信号尚未连接，则忽略错误
            pass
        
        try:
            # 清空现有内容
            self.view.table_widget.clear()
            
            # 设置表头
            self.view.table_widget.setColumnCount(len(self.controller.service.data_model.headers))
            self.view.table_widget.setHorizontalHeaderLabels(self.controller.service.data_model.headers)
            
            # 设置行数和数据
            self.view.table_widget.setRowCount(len(self.controller.service.data_model.rows))
            for row_idx, row_data in enumerate(self.controller.service.data_model.rows):
                for col_idx, cell_value in enumerate(row_data):
                    if col_idx < len(row_data):  # 确保不越界
                        item = QTableWidgetItem(str(cell_value))
                        self.view.table_widget.setItem(row_idx, col_idx, item)
            
            # 应用合并单元格（如果有）
            self.apply_merged_cells()
        finally:
            # 重新连接信号
            self.view.table_widget.itemChanged.connect(self.view._on_item_changed)
            
    def apply_merged_cells(self):
        """应用合并单元格"""
        # 清除现有的合并单元格
        for row in range(self.view.table_widget.rowCount()):
            for col in range(self.view.table_widget.columnCount()):
                self.view.table_widget.setSpan(row, col, 1, 1)
        
        # 应用存储的合并单元格信息
        for merge_info in self.controller.service.data_model.merged_cells_info:
            top_row = merge_info['top_row']
            left_col = merge_info['left_col']
            row_count = merge_info['row_count']
            col_count = merge_info['col_count']
            
            # 检查边界
            if (top_row + row_count <= self.view.table_widget.rowCount() and 
                left_col + col_count <= self.view.table_widget.columnCount()):
                self.view.table_widget.setSpan(top_row, left_col, row_count, col_count)