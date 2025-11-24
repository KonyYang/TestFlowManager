# src/features/matrix/view/matrix_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel
from PyQt5.QtGui import QCursor

from src.features.matrix.service.matrix_service import MatrixService
from src.core.logger import logger
# 导入筛选对话框
from src.features.matrix.view.matrix_filter_dialog import MatrixFilterDialog


class MatrixDialog(QDialog):
    """Matrix视图 - View层"""

    def __init__(self, parent=None, service=None):
        super().__init__(parent)
        self.setWindowTitle("Matrix编辑器")
        # 设置窗口标志，允许窗口最大化和调整大小
        self.setWindowFlags(Qt.Window)
        # 设置默认为最大化状态
        self.setWindowState(Qt.WindowMaximized)
        self.resize(800, 600)  # 设置默认尺寸（在非最大化状态下使用）
        
        # 设置窗口最小尺寸
        self.setMinimumSize(400, 300)
        
        # 复制行/列的数据缓存
        self.copied_row_data = None
        self.copied_col_data = None

        if service is None:
            self.service = MatrixService()
        else:
            self.service = service

        self._setup_ui()

    def _setup_ui(self):
        """设置用户界面 - View层渲染"""
        layout = QVBoxLayout()

        # 添加按钮区域
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入Matrix")
        self.init_btn = QPushButton("标准化Matrix")
        self.find_btn = QPushButton("查找")
        self.export_btn = QPushButton("导出Excel")
        self.extract_test_methods_btn = QPushButton("填充测试规格")
        # 添加更新标准版本按钮
        self.update_standard_versions_btn = QPushButton("更新标准版本")

        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.init_btn)
        button_layout.addWidget(self.find_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.extract_test_methods_btn)
        button_layout.addWidget(self.update_standard_versions_btn)

        # 表格区域
        self.table_widget = QTableWidget()
        # 设置水平表头可以手动调整列宽
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 设置垂直表头可以手动调整行高
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_widget.verticalHeader().setVisible(True)  # 显示行号
        self.table_widget.setAlternatingRowColors(True)  # 交替行颜色
        # 启用单元格的右键菜单
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self._show_cell_context_menu)
        # 连接行头和列头的右键菜单事件
        self.table_widget.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.verticalHeader().customContextMenuRequested.connect(self._show_row_context_menu)
        self.table_widget.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.horizontalHeader().customContextMenuRequested.connect(self._show_col_context_menu)
        # 连接选择变化信号以更新菜单状态
        self.table_widget.itemSelectionChanged.connect(self._on_item_selection_changed)
        # 设置选择模式为连续选择
        self.table_widget.setSelectionMode(QTableWidget.ContiguousSelection)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectItems)

        # 设置表格初始状态
        self._update_table()

        # 连接信号
        self.init_btn.clicked.connect(self._initialize_matrix)
        self.find_btn.clicked.connect(self._find_content)
        self.export_btn.clicked.connect(self._export_to_excel)
        self.import_btn.clicked.connect(self._import_from_spec)
        self.extract_test_methods_btn.clicked.connect(self._extract_test_methods_from_spec)
        # 连接更新标准版本按钮
        self.update_standard_versions_btn.clicked.connect(self._update_standard_versions)

        layout.addLayout(button_layout)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)
        
        # 存储菜单项引用以便动态更新
        self.merge_or_split_action = None

    def _on_item_selection_changed(self):
        """当选择项改变时更新菜单状态"""
        logger.debug("选择项发生变化")
        # 如果菜单项存在，则更新它们的状态
        if self.merge_or_split_action:
            self._update_cell_menu_actions()

    def _update_cell_menu_actions(self):
        """更新单元格菜单项状态"""
        selected_ranges = self.table_widget.selectedRanges()
        logger.debug(f"更新菜单状态，当前选中区域数: {len(selected_ranges)}")
        
        # 调试：打印所有选中区域的详细信息
        for i, range_ in enumerate(selected_ranges):
            logger.debug(f"选中区域 {i}: {range_.rowCount()}x{range_.columnCount()} "
                        f"从({range_.topRow()},{range_.leftColumn()})到({range_.bottomRow()},{range_.rightColumn()})")
        
        # 更新合并或拆分菜单项状态
        if self.merge_or_split_action:
            self.merge_or_split_action.setEnabled(len(selected_ranges) > 0)

    def _show_cell_context_menu(self, position):
        """显示单元格右键菜单"""
        logger.debug(f"显示单元格右键菜单，位置: {position}")
        
        # 创建单元格菜单
        menu = QMenu()
        
        # 添加单元格相关菜单项
        merge_or_split_action = QAction("合并或拆分单元格", self)
        
        # 如果可以撤销或重做，添加相应的菜单项
        if self.service.can_undo_cell_operation():
            undo_action = QAction(f"撤销 {self.service.get_undo_cell_operation_text()}", self)
            undo_action.triggered.connect(self._undo_cell_operation)
            menu.addAction(undo_action)
            
        if self.service.can_redo_cell_operation():
            redo_action = QAction(f"重做 {self.service.get_redo_cell_operation_text()}", self)
            redo_action.triggered.connect(self._redo_cell_operation)
            menu.addAction(redo_action)
            
        if self.service.can_undo_cell_operation() or self.service.can_redo_cell_operation():
            menu.addSeparator()
        
        # 连接动作到处理函数
        merge_or_split_action.triggered.connect(self._merge_or_split_cells)
        
        # 保存菜单项引用以便动态更新
        self.merge_or_split_action = merge_or_split_action
        
        # 添加动作到菜单
        menu.addAction(merge_or_split_action)
        
        # 在鼠标位置显示菜单
        menu.exec_(QCursor.pos())

    def _merge_or_split_cells(self):
        """根据选中单元格的状态执行合并或拆分操作"""
        logger.debug("执行合并或拆分单元格操作")
        self.service.merge_or_split_cells(self.table_widget)

    def _undo_cell_operation(self):
        """撤销单元格操作"""
        logger.debug("执行撤销单元格操作")
        self.service.undo_cell_operation()

    def _redo_cell_operation(self):
        """重做单元格操作"""
        logger.debug("执行重做单元格操作")
        self.service.redo_cell_operation()

    def _show_row_context_menu(self, position):
        """显示行右键菜单"""
        logger.debug(f"显示行右键菜单，位置: {position}")
        # 获取点击的行索引
        row = self.table_widget.verticalHeader().logicalIndexAt(position)
        
        # 如果没有点击到有效行，直接返回
        if row < 0:
            logger.debug("未点击到有效行")
            return
            
        # 不再自动选中当前行，保留当前选中状态
        # self.table_widget.selectRow(row)
        
        # 创建行菜单
        menu = QMenu()
        
        # 添加行相关菜单项
        add_row_action = QAction("添加行", self)
        insert_row_action = QAction("插入行", self)
        move_row_action = QAction("移动行", self)
        copy_row_action = QAction("复制行", self)
        paste_row_action = QAction("粘贴行", self)
        remove_row_action = QAction("删除行", self)
        
        # 连接动作到处理函数
        add_row_action.triggered.connect(self._add_row)
        insert_row_action.triggered.connect(self._insert_row)
        move_row_action.triggered.connect(lambda: self._move_row_at(row))
        copy_row_action.triggered.connect(lambda: self._copy_row(row))
        paste_row_action.triggered.connect(lambda: self._paste_row(row))
        remove_row_action.triggered.connect(self._remove_row)
        
        # 如果没有复制的数据，禁用粘贴功能
        if self.copied_row_data is None:
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

    def _show_col_context_menu(self, position):
        """显示列右键菜单"""
        logger.debug(f"显示列右键菜单，位置: {position}")
        # 获取点击的列索引
        col = self.table_widget.horizontalHeader().logicalIndexAt(position)
        
        # 如果没有点击到有效列，直接返回
        if col < 0:
            logger.debug("未点击到有效列")
            return
            
        # 不再自动选中当前列，保留当前选中状态
        # self.table_widget.selectColumn(col)
        
        # 创建列菜单
        menu = QMenu()
        
        # 添加列相关菜单项（移除了重命名列）
        add_col_action = QAction("添加列", self)
        insert_col_action = QAction("插入列", self)
        move_col_action = QAction("移动列", self)
        copy_col_action = QAction("复制列", self)
        paste_col_action = QAction("粘贴列", self)
        remove_col_action = QAction("删除列", self)
        
        # 连接动作到处理函数
        add_col_action.triggered.connect(self._add_column)
        insert_col_action.triggered.connect(lambda: self._insert_column_at(col))
        move_col_action.triggered.connect(lambda: self._move_column_at(col))
        copy_col_action.triggered.connect(lambda: self._copy_column(col))
        paste_col_action.triggered.connect(lambda: self._paste_column(col))
        remove_col_action.triggered.connect(self._remove_column)
        
        # 如果没有复制的数据，禁用粘贴功能
        if self.copied_col_data is None:
            paste_col_action.setEnabled(False)
        
        # 添加动作到菜单
        menu.addAction(add_col_action)
        menu.addAction(insert_col_action)
        menu.addAction(move_col_action)
        menu.addAction(copy_col_action)
        menu.addAction(paste_col_action)
        menu.addAction(remove_col_action)
        
        # 在鼠标位置显示菜单
        menu.exec_(QCursor.pos())

    def _update_table(self):
        """更新表格显示 - View层渲染"""
        self.table_widget.clear()
        self.table_widget.setRowCount(len(self.service.data_model.rows))
        self.table_widget.setColumnCount(len(self.service.data_model.headers))
        self.table_widget.setHorizontalHeaderLabels(self.service.data_model.headers)
        
        # 设置表头样式 - 灰色背景
        header_style = "QHeaderView::section { background-color: lightgray; }"
        self.table_widget.horizontalHeader().setStyleSheet(header_style)
        self.table_widget.verticalHeader().setStyleSheet(header_style)
        
        # 添加日志信息
        logger.debug(f"更新表格显示: {len(self.service.data_model.rows)} 行, {len(self.service.data_model.headers)} 列")
        print(f"更新表格显示: {len(self.service.data_model.rows)} 行, {len(self.service.data_model.headers)} 列")

        for row_idx, row_data in enumerate(self.service.data_model.rows):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(cell_value)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                # 设置单元格内容水平和垂直居中
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row_idx, col_idx, item)
                
        # 显示前几行的数据用于调试
        if len(self.service.data_model.rows) > 0 and len(self.service.data_model.headers) > 0:
            logger.debug(f"表头: {self.service.data_model.headers[:5]}...")
            print(f"表头: {self.service.data_model.headers[:5]}...")
            for i, row in enumerate(self.service.data_model.rows[:3]):  # 只显示前3行
                logger.debug(f"第{i+1}行: {row[:5] if len(row) > 5 else row}...")
                print(f"第{i+1}行: {row[:5] if len(row) > 5 else row}...")
        
        # 应用合并单元格信息（如果存在）
        if hasattr(self.service, 'merged_cells_info') and self.service.merged_cells_info:
            for merge_info in self.service.merged_cells_info:
                top_row = merge_info['top_row']
                left_col = merge_info['left_col']
                row_count = merge_info['row_count']
                col_count = merge_info['col_count']
                
                # 确保合并范围在有效范围内
                if (top_row >= 0 and left_col >= 0 and 
                    top_row + row_count <= self.table_widget.rowCount() and 
                    left_col + col_count <= self.table_widget.columnCount()):
                    self.table_widget.setSpan(top_row, left_col, row_count, col_count)
        
        # 根据内容自动调整行高
        self.table_widget.resizeRowsToContents()

    def _sync_table_to_model(self):
        """将表格数据同步到数据模型 - View层数据同步"""
        for row_idx in range(self.table_widget.rowCount()):
            if row_idx < len(self.service.data_model.rows):
                for col_idx in range(self.table_widget.columnCount()):
                    if col_idx < len(self.service.data_model.rows[row_idx]):
                        item = self.table_widget.item(row_idx, col_idx)
                        if item:
                            self.service.data_model.rows[row_idx][col_idx] = item.text()

    def _initialize_matrix(self):
        """初始化Matrix - View层事件触发"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 调用服务层初始化Matrix
        if self.service.initialize_matrix():
            self._update_table()
            QMessageBox.information(self, "成功", "Matrix初始化完成")
        else:
            QMessageBox.warning(self, "失败", "Matrix初始化失败")

    def _add_column(self):
        """添加列 - View层事件触发"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 触发Controller层处理，不使用输入的列名
        self.service.add_column()
        self._update_table()

    def _insert_column_at(self, col):
        """在指定位置插入列 - View层事件触发"""
        if col >= 0:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 在当前选中列之后插入新列
            insert_position = col + 1
            self.service.add_column(position=insert_position)
            self._update_table()
        else:
            QMessageBox.warning(self, "操作失败", "请先选择一列")

    def _move_column_at(self, col):
        """在指定列移动列 - View层事件触发"""
        if col >= 0:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 询问要移动到的位置
            new_position, ok = QInputDialog.getInt(
                self, "移动列", "请输入目标列位置(从0开始):", 
                col, 0, len(self.service.data_model.headers)-1)
            if ok and new_position != col:
                if self.service.move_column(col, new_position):
                    self._update_table()
                    # 移除了成功消息框
                else:
                    QMessageBox.warning(self, "操作失败", "列移动失败")
        else:
            QMessageBox.warning(self, "操作失败", "请选择一列")

    def _copy_column(self, col):
        """复制列 - View层事件触发"""
        if col >= 0:
            # 调用服务层复制列
            self.copied_col_data = self.service.copy_column(col)
        # 不再弹出提醒菜单

    def _paste_column(self, col):
        """粘贴列 - View层事件触发"""
        if col >= 0:
            # 检查是否有复制的数据
            if self.copied_col_data is None:
                return
                
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 调用服务层粘贴列
            result = self.service.paste_column(col, self.copied_col_data)
            if result:
                self._update_table()
        # 不再弹出提醒菜单

    def _remove_column(self):
        """删除列 - View层事件触发"""
        column_index = self.table_widget.currentColumn()
        if column_index >= 0:
            # 在删除列之前，先处理可能影响的合并单元格
            self._handle_spans_before_column_removal(column_index)
            
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            result = self.service.remove_column(column_index)
            if not result:
                QMessageBox.warning(self, "操作失败", "删除列失败")
            self._update_table()
        else:
            QMessageBox.warning(self, "操作失败", "请选择要删除的列")
            
    def _handle_spans_before_column_removal(self, col_index):
        """
        在删除列之前处理可能受影响的合并单元格
        """
        # 使用服务层的方法来清理与合并单元格相关的跨度信息
        # 这里我们直接操作table_widget，因为这是视图层特定的逻辑
        self.service.cell_service.clear_spans_for_column(self.table_widget, col_index)

    def _add_row(self):
        """添加行 - View层事件触发"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 触发Controller层处理
        self.service.add_row()
        self._update_table()

    def _insert_row(self):
        """插入行 - View层事件触发"""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            result = self.service.insert_row(current_row)
            if result:
                self._update_table()
            else:
                QMessageBox.warning(self, "操作失败", "行插入失败")
        else:
            QMessageBox.warning(self, "操作失败", "请选择要在其前插入新行的位置")

    def _move_row_at(self, row):
        """在指定行移动行 - View层事件触发"""
        if row >= 0:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 询问要移动到的位置
            new_position, ok = QInputDialog.getInt(
                self, "移动行", "请输入目标行位置(从0开始):", 
                row, 0, len(self.service.data_model.rows)-1)
            if ok and new_position != row:
                if self.service.move_row(row, new_position):
                    self._update_table()
                    # 移除了成功消息框
                else:
                    QMessageBox.warning(self, "操作失败", "行移动失败")
        else:
            QMessageBox.warning(self, "操作失败", "请选择一行")

    def _copy_row(self, row):
        """复制行 - View层事件触发"""
        if row >= 0:
            # 调用服务层复制行
            self.copied_row_data = self.service.copy_row(row)
        # 不再弹出提醒菜单

    def _paste_row(self, row):
        """粘贴行 - View层事件触发"""
        if row >= 0:
            # 检查是否有复制的数据
            if self.copied_row_data is None:
                return
                
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 调用服务层粘贴行
            result = self.service.paste_row(row, self.copied_row_data)
            if result:
                self._update_table()
        # 不再弹出提醒菜单

    def _remove_row(self):
        """删除行 - View层事件触发"""
        row_index = self.table_widget.currentRow()
        if row_index >= 0:
            # 在删除行之前，先处理可能影响的合并单元格
            self._handle_spans_before_row_removal(row_index)
            
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            result = self.service.remove_row(row_index)
            if not result:
                QMessageBox.warning(self, "操作失败", "删除行失败")
            self._update_table()
        else:
            QMessageBox.warning(self, "操作失败", "请选择要删除的行")
            
    def _handle_spans_before_row_removal(self, row_index):
        """
        在删除行之前处理可能受影响的合并单元格
        """
        # 使用服务层的方法来清理与合并单元格相关的跨度信息
        # 这里我们直接操作table_widget，因为这是视图层特定的逻辑
        self.service.cell_service.clear_spans_for_row(self.table_widget, row_index)

    def _find_content(self):
        """查找内容 - View层事件触发"""
        search_text, ok = QInputDialog.getText(self, "查找", "请输入要查找的内容:")
        if ok and search_text:
            results = self.service.find_by_content(search_text)
            if results:
                msg = f"找到 {len(results)} 个匹配项:\n"
                for result in results:
                    msg += f"第{result['row']+1}行, {result['header']}列: {result['value']}\n"
                QMessageBox.information(self, "查找结果", msg)
            else:
                QMessageBox.information(self, "查找结果", "未找到匹配项")

    def _export_to_excel(self):
        """导出到Excel - View层事件触发"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 导出前先保存合并单元格信息
            self._save_merged_cells_info()
            # 触发Controller层处理
            if self.service.export_to_excel(file_path):
                QMessageBox.information(self, "成功", "数据已成功导出到Excel")
            else:
                # 检查文件是否被占用
                import os
                try:
                    # 尝试以独占模式打开文件
                    with open(file_path, 'r+b') as f:
                        pass
                    # 如果能打开，说明是其他问题
                    QMessageBox.warning(self, "错误", "导出失败，请检查文件路径或权限")
                except PermissionError:
                    # 文件被其他程序占用
                    QMessageBox.warning(self, "错误", "导出失败，文件已被其他程序占用（可能已在Excel中打开），请关闭文件后重试")
                except FileNotFoundError:
                    # 文件不存在，应该是其他问题
                    QMessageBox.warning(self, "错误", "导出失败，请检查文件路径是否正确")
                except Exception:
                    # 其他未知错误
                    QMessageBox.warning(self, "错误", "导出失败，发生未知错误")
                
    def _save_merged_cells_info(self):
        """
        保存合并单元格信息到数据模型中，以便导出时能够恢复
        """
        # 收集所有合并单元格的信息
        merged_cells_info = []
        processed_cells = set()  # 记录已处理的单元格，避免重复
        
        # 遍历表格中的所有单元格
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                # 检查是否已经处理过这个单元格
                if (row, col) in processed_cells:
                    continue
                    
                row_span = self.table_widget.rowSpan(row, col)
                col_span = self.table_widget.columnSpan(row, col)
                
                # 如果这是一个合并单元格的起始点
                if row_span > 1 or col_span > 1:
                    merged_cells_info.append({
                        'top_row': row,
                        'left_col': col,
                        'row_count': row_span,
                        'col_count': col_span
                    })
                    logger.debug(f"收集合并单元格信息: row={row}, col={col}, row_span={row_span}, col_span={col_span}")
                    
                    # 标记这个合并区域内的所有单元格为已处理
                    for r in range(row, row + row_span):
                        for c in range(col, col + col_span):
                            processed_cells.add((r, c))
        
        logger.debug(f"总共收集到 {len(merged_cells_info)} 个合并单元格信息")
        # 将合并单元格信息保存到服务层或模型中
        # 这里我们可以通过某种方式将信息传递给导出功能
        # 由于当前架构限制，我们暂时将信息保存在服务层的一个临时属性中
        self.service.merged_cells_info = merged_cells_info

    def _import_from_spec(self):
        """从Spec导入数据 - View层事件触发"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Spec文件", "", "Spec Files (*.pdf *.doc *.docx *.xls *.xlsx)"
        )
        if file_path:
            # 弹出筛选对话框
            filter_dialog = MatrixFilterDialog(self)
            if filter_dialog.exec_() == QDialog.Accepted:
                # 获取筛选参数
                filter_params = filter_dialog.get_filter_params()
                page_number = filter_params['page']
                keyword = filter_params['keyword']
                
                try:
                    logger.info(f"开始从Spec导入数据: {file_path}")
                    logger.info(f"筛选参数: 页码={page_number}, 关键字='{keyword}'")
                    
                    # 调用服务层导入数据
                    success = self.service.import_from_spec(file_path, page_number, keyword)
                    
                    if success:
                        # 更新表格显示
                        self._update_table()
                    else:
                        logger.error("Spec数据导入失败")
                        # 显示错误消息框，提醒用户导入失败
                        QMessageBox.warning(self, "导入失败", "从Spec文件导入数据失败，请检查页码或内容。")
                except Exception as e:
                    logger.error(f"导入Spec时出错: {e}", exc_info=True)
                    QMessageBox.warning(self, "错误", f"导入Spec时出错: {str(e)}")

    def _extract_test_methods_from_spec(self):
        """从规格书提取测试方法 - View层事件触发"""
        try:
            logger.info("开始提取测试方法")
            
            # 检查是否有导入的规格书文件
            if not self.service.last_imported_spec_path:
                # 如果没有已导入的规格书文件，提示用户选择文件
                reply = QMessageBox.question(
                    self, 
                    "选择规格书文件", 
                    "未检测到已导入的规格书文件，是否现在选择文件进行测试方法提取？", 
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 弹出文件选择对话框
                    file_path, _ = QFileDialog.getOpenFileName(
                        self, 
                        "选择规格书文件", 
                        "", 
                        "Spec Files (*.pdf *.doc *.docx *.xls *.xlsx)"
                    )
                    
                    if file_path:
                        # 保存文件路径
                        self.service.last_imported_spec_path = file_path
                        logger.info(f"用户选择的规格书文件: {file_path}")
                    else:
                        # 用户取消了文件选择
                        logger.info("用户取消了文件选择")
                        return
                else:
                    # 用户选择不选择文件
                    logger.info("用户选择不选择文件")
                    return
            
            # 同步表格数据到模型
            self._sync_table_to_model()
            
            # 调用服务层提取测试方法
            success = self.service.extract_test_methods_from_spec()
            
            if success:
                # 更新表格显示
                self._update_table()
                QMessageBox.information(self, "成功", "测试方法提取完成")
                logger.info("测试方法提取完成")
            else:
                # 检查是否是因为表头结构不正确导致的失败
                if (len(self.service.data_model.rows) > 0 and len(self.service.data_model.rows[0]) > 4 and 
                    (self.service.data_model.rows[0][2] != "Test Method" or 
                     self.service.data_model.rows[0][3] != "Condition" or 
                     self.service.data_model.rows[0][4] != "Requirement")):
                    QMessageBox.warning(self, "表头结构错误", 
                        "表头结构不正确，第3、4、5列应分别为'Test Method'、'Condition'、'Requirement'，请添加或移动到正确位置后再试。")
                else:
                    QMessageBox.warning(self, "失败", "测试方法提取失败或未找到匹配项")
                logger.warning("测试方法提取失败或未找到匹配项")
                # 添加更多调试信息
                logger.info(f"当前Matrix数据行数: {len(self.service.data_model.rows)}")
                if len(self.service.data_model.rows) > 0:
                    logger.info(f"Matrix表头: {self.service.data_model.headers}")
                    logger.info(f"第一行数据: {self.service.data_model.rows[0]}")
                
        except Exception as e:
            logger.error(f"提取测试方法时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"提取测试方法时出错: {str(e)}")
        finally:
            pass  # 占位符，确保try语句正确闭合

    def _update_standard_versions(self):
        """
        更新标准版本号 - View层事件触发
        """
        try:
            logger.info("开始更新标准版本号")
            
            # 同步表格数据到模型
            self._sync_table_to_model()
            
            # 调用服务层更新标准版本号
            result = self.service.update_standard_versions()
            
            if result["success"]:
                # 更新表格显示
                self._update_table()
                
                # 显示更新详情
                details = result["details"]
                if details:
                    details_msg = "\n".join([f"第{detail['row']}行: {detail['old_method']} -> {detail['new_method']}" 
                                               for detail in details[:10]])  # 只显示前10个
                    if len(details) > 10:
                        details_msg += f"\n...还有{len(details) - 10}个更新"
                    QMessageBox.information(self, "成功", 
                                      f"标准版本号更新完成，共更新{result['updated_count']}项:\n{details_msg}")
                else:
                    # 没有需要更新的项，但不是失败
                    QMessageBox.information(self, "成功", "标准版本号更新完成，没有需要更新的项")
                    logger.info("标准版本号更新完成")
            else:
                # 失败情况，只有在真正失败时才显示错误消息
                if "error" in result:
                    QMessageBox.warning(self, "失败", f"标准版本号更新出错: {result['error']}")
                    logger.error(f"标准版本号更新出错: {result['error']}")
                else:
                    # 没有找到需要更新的项，但不是错误
                    QMessageBox.information(self, "成功", "标准版本号更新完成，没有需要更新的项")
                    logger.info("标准版本号更新完成，没有需要更新的项")
        except Exception as e:
            logger.error(f"更新标准版本号时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"更新标准版本号时出错: {str(e)}")
