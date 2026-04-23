# src/features/matrix/view/components/matrix_context_menus.py
from PyQt5.QtWidgets import QMenu, QAction, QTableWidgetItem
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtGui import QCursor
from src.core.logger import logger


class MatrixContextMenus:
    """Matrix上下文菜单组件 - 处理所有右键菜单"""
    
    def __init__(self, view):
        self.view = view
        self.merge_or_split_action = None

    def _get_table_widget(self):
        return self.view.get_table_widget() if self.view else None
        
    def show_cell_context_menu(self, position):
        """显示单元格右键菜单"""
        logger.debug(f"显示单元格右键菜单，位置: {position}")
        
        # 防御性检查：确保view和表格控件仍然有效
        table_widget = self._get_table_widget()
        if not self.view or not table_widget:
            logger.warning("视图或表格控件已销毁，取消显示单元格菜单")
            return
        
        try:
            # 创建单元格菜单
            menu = QMenu()
            
            # 添加单元格相关菜单项
            merge_or_split_action = QAction("合并或拆分单元格", self.view)
            copy_cells_action = QAction("复制单元格", self.view)
            paste_cells_action = QAction("粘贴单元格", self.view)
            
            # 如果可以撤销或重做，添加相应的菜单项
            if self.view.can_undo_cell_operation():
                undo_action = QAction(f"撤销 {self.view.get_undo_cell_operation_text()}", self.view)
                undo_action.triggered.connect(self.view.undo_cell_operation)
                menu.addAction(undo_action)
                
            if self.view.can_redo_cell_operation():
                redo_action = QAction(f"重做 {self.view.get_redo_cell_operation_text()}", self.view)
                redo_action.triggered.connect(self.view.redo_cell_operation)
                menu.addAction(redo_action)
                
            if self.view.can_undo_cell_operation() or self.view.can_redo_cell_operation():
                menu.addSeparator()
            
            # 连接动作到处理函数
            merge_or_split_action.triggered.connect(self.view.merge_or_split_cells)
            copy_cells_action.triggered.connect(self._copy_cells)
            paste_cells_action.triggered.connect(self._paste_cells)
            
            # 保存菜单项引用以便动态更新
            self.merge_or_split_action = merge_or_split_action
            
            # 添加动作到菜单
            menu.addAction(merge_or_split_action)
            menu.addSeparator()
            menu.addAction(copy_cells_action)
            menu.addAction(paste_cells_action)
            
            # 检查是否有复制的数据，如果没有则禁用粘贴功能
            if self.view.get_copied_cells_data() is None:
                paste_cells_action.setEnabled(False)
            
            # 在鼠标位置显示菜单
            menu.exec_(QCursor.pos())
            
        except RuntimeError as e:
            logger.error(f"显示单元格菜单时发生运行时错误（可能是对象已销毁）: {e}")
        except Exception as e:
            logger.error(f"显示单元格菜单时发生未知错误: {e}", exc_info=True)

    def _copy_cells(self):
        """复制选中的单元格"""
        table_widget = self._get_table_widget()
        selected_ranges = table_widget.selectedRanges()
        if not selected_ranges:
            return
            
        # 只处理第一个选区
        range_ = selected_ranges[0]
        
        # 保存选区的行列数和数据
        self.view.set_copied_cells_data({
            'rows': range_.rowCount(),
            'cols': range_.columnCount(),
            'data': []
        })
        
        # 提取选区数据
        for row in range(range_.rowCount()):
            row_data = []
            for col in range(range_.columnCount()):
                item = table_widget.item(range_.topRow() + row, range_.leftColumn() + col)
                row_data.append(item.text() if item else "")
            self.view.get_copied_cells_data()['data'].append(row_data)
        
        logger.debug(f"已复制 {range_.rowCount()}x{range_.columnCount()} 单元格区域")

    def _paste_cells(self):
        """粘贴单元格数据到当前选区"""
        # 检查是否有复制的数据
        copied_cells_data = self.view.get_copied_cells_data()
        if copied_cells_data is None:
            return

        table_widget = self._get_table_widget()
        selected_ranges = table_widget.selectedRanges()
        if not selected_ranges:
            return
            
        # 只处理第一个选区
        range_ = selected_ranges[0]
        
        # 获取复制的数据
        copied_data = copied_cells_data['data']
        copied_rows = copied_cells_data['rows']
        copied_cols = copied_cells_data['cols']
        
        # 计算实际粘贴范围（要考虑边界限制）
        actual_rows = min(copied_rows, table_widget.rowCount() - range_.topRow())
        actual_cols = min(copied_cols, table_widget.columnCount() - range_.leftColumn())
        
        # 粘贴数据
        for row in range(actual_rows):
            for col in range(actual_cols):
                item = table_widget.item(range_.topRow() + row, range_.leftColumn() + col)
                if item:
                    item.setText(copied_data[row][col])
                else:
                    new_item = QTableWidgetItem(copied_data[row][col])
                    table_widget.setItem(range_.topRow() + row, range_.leftColumn() + col, new_item)
        
        logger.debug(f"已粘贴 {actual_rows}x{actual_cols} 单元格区域")

    def show_row_context_menu(self, position):
        """显示行右键菜单"""
        logger.debug(f"显示行右键菜单，位置: {position}")
        
        # 防御性检查：确保view和表格控件仍然有效
        table_widget = self._get_table_widget()
        if not self.view or not table_widget:
            logger.warning("视图或表格控件已销毁，取消显示行菜单")
            return
        
        try:
            # 获取点击的行索引
            row = table_widget.verticalHeader().logicalIndexAt(position)
            
            # 如果没有点击到有效行，直接返回
            if row < 0 or row >= table_widget.rowCount():
                logger.debug(f"未点击到有效行 (row={row}, total_rows={table_widget.rowCount()})")
                return
                
            # 创建行菜单
            menu = QMenu()
            
            # 添加行相关菜单项
            add_row_action = QAction("添加行", self.view)
            insert_row_action = QAction("插入行", self.view)
            move_row_action = QAction("移动行", self.view)
            copy_row_action = QAction("复制行", self.view)
            paste_row_action = QAction("粘贴行", self.view)
            remove_row_action = QAction("删除行", self.view)
            
            # 连接动作到处理函数
            add_row_action.triggered.connect(self.view.add_row)
            insert_row_action.triggered.connect(self.view.insert_row)
            move_row_action.triggered.connect(lambda: self.view.move_row_at(row))
            copy_row_action.triggered.connect(lambda: self.view.copy_row(row))
            paste_row_action.triggered.connect(lambda: self.view.paste_row(row))
            remove_row_action.triggered.connect(self.view.remove_row)
            
            # 如果没有复制的数据，禁用粘贴功能
            if self.view.get_copied_row_data() is None:
                paste_row_action.setEnabled(False)
            
            # 添加动作到菜单
            menu.addAction(add_row_action)
            menu.addAction(insert_row_action)
            menu.addAction(move_row_action)
            menu.addAction(copy_row_action)
            menu.addAction(paste_row_action)
            menu.addAction(remove_row_action)
            
            # 在鼠标位置显示菜单
            menu.exec_(QCursor.pos())
            
        except RuntimeError as e:
            logger.error(f"显示行菜单时发生运行时错误（可能是对象已销毁）: {e}")
        except Exception as e:
            logger.error(f"显示行菜单时发生未知错误: {e}", exc_info=True)
        
    def show_col_context_menu(self, position):
        """显示列右键菜单"""
        logger.debug(f"显示列右键菜单，位置: {position}")
        
        # 防御性检查：确保view和表格控件仍然有效
        table_widget = self._get_table_widget()
        if not self.view or not table_widget:
            logger.warning("视图或表格控件已销毁，取消显示列菜单")
            return
        
        try:
            # 获取点击的列索引
            col = table_widget.horizontalHeader().logicalIndexAt(position)
            
            # 如果没有点击到有效列，直接返回
            if col < 0 or col >= table_widget.columnCount():
                logger.debug(f"未点击到有效列 (col={col}, total_cols={table_widget.columnCount()})")
                return
                
            # 创建列菜单
            menu = QMenu()
            
            # 添加列相关菜单项
            add_col_action = QAction("添加列", self.view)
            insert_col_action = QAction("插入列", self.view)
            move_col_action = QAction("移动列", self.view)
            copy_col_action = QAction("复制列", self.view)
            paste_col_action = QAction("粘贴列", self.view)
            remove_col_action = QAction("删除列", self.view)
            
            # 连接动作到处理函数
            add_col_action.triggered.connect(self.view.add_column)
            insert_col_action.triggered.connect(self.view.insert_column)
            move_col_action.triggered.connect(lambda: self.view.move_column(col))
            copy_col_action.triggered.connect(lambda: self.view.copy_column(col))
            paste_col_action.triggered.connect(lambda: self.view.paste_column(col))
            remove_col_action.triggered.connect(self.view.remove_column)
            
            # 如果没有复制的数据，禁用粘贴功能
            if self.view.get_copied_col_data() is None:
                paste_col_action.setEnabled(False)
            
            # 添加动作到菜单
            menu.addAction(add_col_action)
            menu.addAction(insert_col_action)
            menu.addAction(move_col_action)
            menu.addAction(copy_col_action)
            menu.addAction(paste_col_action)
            menu.addAction(remove_col_action)
            
            # 在鼠标位置显示菜单（使用exec_而不是popup，避免异步问题）
            menu.exec_(QCursor.pos())
            
        except RuntimeError as e:
            logger.error(f"显示列菜单时发生运行时错误（可能是对象已销毁）: {e}")
        except Exception as e:
            logger.error(f"显示列菜单时发生未知错误: {e}", exc_info=True)
        
    def update_cell_menu_actions(self):
        """更新单元格菜单项状态"""
        # 防御性检查：确保view和表格控件仍然有效
        table_widget = self._get_table_widget()
        if not self.view or not table_widget:
            return
        
        try:
            selected_ranges = table_widget.selectedRanges()
            logger.debug(f"更新菜单状态，当前选中区域数: {len(selected_ranges)}")
            
            # 更新合并或拆分菜单项状态
            if self.merge_or_split_action:
                self.merge_or_split_action.setEnabled(len(selected_ranges) > 0)
        except RuntimeError as e:
            logger.error(f"更新菜单状态时发生运行时错误（可能是对象已销毁）: {e}")
        except Exception as e:
            logger.error(f"更新菜单状态时发生未知错误: {e}", exc_info=True)
