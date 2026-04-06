# src/features/matrix/view/managers/data_sync_manager.py
from src.core.logger import logger


class DataSyncManager:
    """数据同步管理器 - 处理视图与数据模型之间的数据同步"""
    
    def __init__(self, view, controller):
        self.view = view
        self.controller = controller
        
    def sync_table_to_model(self):
        """同步表格数据到数据模型"""
        try:
            logger.debug("开始同步表格数据到模型")
            # 同步表头
            headers = []
            for col in range(self.view.matrix_table_widget.columnCount()):
                header_item = self.view.matrix_table_widget.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"Column {col}")
            self.controller.data_model.headers = headers
            
            # 同步数据行
            rows = []
            for row in range(self.view.matrix_table_widget.rowCount()):
                row_data = []
                for col in range(self.view.matrix_table_widget.columnCount()):
                    item = self.view.matrix_table_widget.item(row, col)
                    row_data.append(item.text() if item else "")
                rows.append(row_data)
            self.controller.data_model.rows = rows
            
            # 同步合并单元格信息
            self.save_merged_cells_info()
            
            # 确保导出数据模型也是最新的
            self.controller._sync_table_to_model()
            
            # 添加调试信息，显示同步后的数据概况
            try:
                rows = self.controller.data_model.rows
                headers = self.controller.data_model.headers
                logger.debug(f"同步后数据概况 - 表头数量: {len(headers)}, 行数: {len(rows)}")
                if headers:
                    logger.debug(f"表头内容: {headers}")
                if rows:
                    logger.debug(f"同步后第一行数据: {rows[0][:5] if len(rows[0]) > 5 else rows[0]}")  # 只显示前5个元素
                    logger.debug(f"同步后前3行:")
                    for i, row in enumerate(rows[:3]):
                        logger.debug(f"  第{i+1}行: {row}")
                    if len(rows) > 3:
                        logger.debug(f"  ... (还有{len(rows)-3}行)")
            except Exception as e:
                logger.error(f"打印数据模型摘要时出错: {e}")
        except Exception as e:
            logger.error(f"同步表格数据到模型时出错: {e}", exc_info=True)

    def save_merged_cells_info(self):
        """
        保存合并单元格信息到数据模型中，以便导出时能够恢复
        """
        # 收集所有合并单元格的信息
        merged_cells_info = []
        processed_cells = set()  # 记录已处理的单元格，避免重复
        
        # 遍历表格中的所有单元格
        for row in range(self.view.matrix_table_widget.rowCount()):
            for col in range(self.view.matrix_table_widget.columnCount()):
                # 检查是否已经处理过这个单元格
                if (row, col) in processed_cells:
                    continue
                    
                row_span = self.view.matrix_table_widget.rowSpan(row, col)
                col_span = self.view.matrix_table_widget.columnSpan(row, col)
                
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
        self.controller.data_model.merged_cells_info = merged_cells_info
        # 移除合并单元格信息保存的详细日志
