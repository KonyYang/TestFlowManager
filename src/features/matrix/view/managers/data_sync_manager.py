# src/features/matrix/view/managers/data_sync_manager.py
from src.core.logger import logger


class DataSyncManager:
    """数据同步管理器 - 处理视图与数据模型之间的数据同步"""
    
    def __init__(self, view, controller):
        self.view = view
        self.controller = controller
        
    def sync_table_to_model(self):
        """同步表格数据到数据模型"""
        # 移除同步表格数据的详细日志
        for row in range(self.view.table_widget.rowCount()):
            for col in range(self.view.table_widget.columnCount()):
                item = self.view.table_widget.item(row, col)
                if item:
                    self.controller.set_cell_value(row, col, item.text())
                else:
                    self.controller.set_cell_value(row, col, "")
                    
    def save_merged_cells_info(self):
        """
        保存合并单元格信息到数据模型中，以便导出时能够恢复
        """
        # 收集所有合并单元格的信息
        merged_cells_info = []
        processed_cells = set()  # 记录已处理的单元格，避免重复
        
        # 遍历表格中的所有单元格
        for row in range(self.view.table_widget.rowCount()):
            for col in range(self.view.table_widget.columnCount()):
                # 检查是否已经处理过这个单元格
                if (row, col) in processed_cells:
                    continue
                    
                row_span = self.view.table_widget.rowSpan(row, col)
                col_span = self.view.table_widget.columnSpan(row, col)
                
                # 如果行列跨度都大于1，说明是合并单元格
                if row_span > 1 or col_span > 1:
                    # 记录合并单元格信息
                    merged_cells_info.append({
                        'top_row': row,
                        'left_col': col,
                        'row_count': row_span,
                        'col_count': col_span
                    })
                    
                    # 标记所有涉及的单元格为已处理
                    for r in range(row, row + row_span):
                        for c in range(col, col + col_span):
                            processed_cells.add((r, c))
                            
        # 更新数据模型中的合并单元格信息
        self.controller.service.data_model.merged_cells_info = merged_cells_info
        # 移除合并单元格信息保存的详细日志