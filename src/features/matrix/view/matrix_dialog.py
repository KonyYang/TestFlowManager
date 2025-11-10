# src/features/matrix/view/matrix_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from src.features.matrix.service.matrix_service import MatrixService


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
        self.find_btn = QPushButton("查找")
        self.export_btn = QPushButton("导出Excel")
        self.import_btn = QPushButton("导入Spec")

        button_layout.addWidget(self.find_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.import_btn)

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

        # 设置表格初始状态
        self._update_table()

        # 连接信号
        self.find_btn.clicked.connect(self._find_content)
        self.export_btn.clicked.connect(self._export_to_excel)
        self.import_btn.clicked.connect(self._import_from_spec)

        layout.addLayout(button_layout)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

    def _show_cell_context_menu(self, position):
        """显示单元格右键菜单"""
        # 获取点击的单元格位置
        cell_pos = self.table_widget.itemAt(position)
        
        # 创建单元格菜单
        menu = QMenu()
        
        # 添加单元格相关菜单项
        merge_cells_action = QAction("合并单元格", self)
        split_cell_action = QAction("拆分单元格", self)
        
        # 连接动作到处理函数
        merge_cells_action.triggered.connect(self._merge_cells)
        split_cell_action.triggered.connect(self._split_cell)
        
        # 检查是否可以合并单元格（必须选中多个单元格）
        selected_ranges = self.table_widget.selectedRanges()
        if len(selected_ranges) == 0 or (selected_ranges[0].rowCount() == 1 and selected_ranges[0].columnCount() == 1):
            merge_cells_action.setEnabled(False)
            
        # 检查是否可以拆分单元格（必须选中单个单元格且该单元格是合并的）
        if len(selected_ranges) == 1:
            range_ = selected_ranges[0]
            if range_.rowCount() == 1 and range_.columnCount() == 1:
                # 检查单元格是否是合并的
                row = range_.topRow()
                col = range_.leftColumn()
                # 简单检查：如果单元格跨度大于1，则认为是合并的
                # 注意：QTableWidget的单元格合并检查比较复杂，这里简化处理
                pass
            else:
                split_cell_action.setEnabled(False)
        else:
            split_cell_action.setEnabled(False)
        
        # 添加动作到菜单
        menu.addAction(merge_cells_action)
        menu.addAction(split_cell_action)
        
        # 在鼠标位置显示菜单
        menu.exec_(QCursor.pos())

    def _merge_cells(self):
        """合并选中的单元格"""
        selected_ranges = self.table_widget.selectedRanges()
        if len(selected_ranges) > 0:
            range_ = selected_ranges[0]
            # 获取选中区域的行数和列数
            row_count = range_.rowCount()
            col_count = range_.columnCount()
            
            if row_count > 1 or col_count > 1:
                # 合并单元格
                top_row = range_.topRow()
                left_col = range_.leftColumn()
                bottom_row = range_.bottomRow()
                right_col = range_.rightColumn()
                
                # 获取合并区域第一个单元格的文本
                first_cell_text = ""
                first_item = self.table_widget.item(top_row, left_col)
                if first_item:
                    first_cell_text = first_item.text()
                
                # 设置第一个单元格的跨度
                self.table_widget.setSpan(top_row, left_col, row_count, col_count)
                
                # 更新第一个单元格的文本
                if first_item:
                    first_item.setText(first_cell_text)
                    first_item.setTextAlignment(Qt.AlignCenter)
                
                # 清除其他单元格的内容（这些单元格在视觉上被合并了，但实际仍存在）
                for row in range(top_row, bottom_row + 1):
                    for col in range(left_col, right_col + 1):
                        if row != top_row or col != left_col:
                            item = self.table_widget.item(row, col)
                            if item:
                                item.setText("")
                
                QMessageBox.information(self, "成功", f"成功合并 {row_count}x{col_count} 区域")
            else:
                QMessageBox.warning(self, "操作失败", "请选择多个单元格进行合并")

    def _split_cell(self):
        """拆分合并的单元格"""
        selected_ranges = self.table_widget.selectedRanges()
        if len(selected_ranges) > 0:
            range_ = selected_ranges[0]
            row = range_.topRow()
            col = range_.leftColumn()
            
            # 获取当前单元格的跨度
            row_span = self.table_widget.rowSpan(row, col)
            col_span = self.table_widget.columnSpan(row, col)
            
            if row_span > 1 or col_span > 1:
                # 拆分单元格
                self.table_widget.setSpan(row, col, 1, 1)
                QMessageBox.information(self, "成功", "成功拆分单元格")
            else:
                QMessageBox.warning(self, "操作失败", "选中的单元格未被合并")

    def _show_row_context_menu(self, position):
        """显示行右键菜单"""
        # 获取点击的行索引
        row = self.table_widget.verticalHeader().logicalIndexAt(position)
        
        # 如果没有点击到有效行，直接返回
        if row < 0:
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
        # 获取点击的列索引
        col = self.table_widget.horizontalHeader().logicalIndexAt(position)
        
        # 如果没有点击到有效列，直接返回
        if col < 0:
            return
            
        # 不再自动选中当前列，保留当前选中状态
        # self.table_widget.selectColumn(col)
        
        # 创建列菜单
        menu = QMenu()
        
        # 添加列相关菜单项
        add_col_action = QAction("添加列", self)
        insert_col_action = QAction("插入列", self)
        move_col_action = QAction("移动列", self)
        rename_col_action = QAction("重命名列", self)
        copy_col_action = QAction("复制列", self)
        paste_col_action = QAction("粘贴列", self)
        remove_col_action = QAction("删除列", self)
        
        # 连接动作到处理函数
        add_col_action.triggered.connect(self._add_column)
        insert_col_action.triggered.connect(self._insert_column)
        move_col_action.triggered.connect(lambda: self._move_column_at(col))
        rename_col_action.triggered.connect(lambda: self._rename_column(col))
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
        menu.addAction(rename_col_action)
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
        
        # 添加日志信息
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
            print(f"表头: {self.service.data_model.headers[:5]}...")
            for i, row in enumerate(self.service.data_model.rows[:3]):  # 只显示前3行
                print(f"第{i+1}行: {row[:5] if len(row) > 5 else row}...")
        
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

    def _add_column(self):
        """添加列 - View层事件触发"""
        column_name, ok = QInputDialog.getText(self, "添加列", "请输入列名:")
        if ok and column_name:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            self.service.add_column(column_name)
            self._update_table()

    def _insert_column(self):
        """插入列 - View层事件触发"""
        current_col = self.table_widget.currentColumn()
        if current_col >= 0:
            column_name, ok = QInputDialog.getText(self, "插入列", "请输入列名:")
            if ok and column_name:
                # 同步表格数据到模型
                self._sync_table_to_model()
                # 在当前选中列之后插入新列
                insert_position = current_col + 1
                self.service.add_column(column_name, insert_position)
                self._update_table()
        else:
            QMessageBox.warning(self, "操作失败", "请先选择一列")

    def _move_column(self):
        """移动列 - View层事件触发"""
        current_col = self.table_widget.currentColumn()
        if current_col >= 0:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 询问要移动到的位置
            new_position, ok = QInputDialog.getInt(
                self, "移动列", "请输入目标列位置(从0开始):", 
                current_col, 0, len(self.service.data_model.headers)-1)
            if ok and new_position != current_col:
                if self.service.move_column(current_col, new_position):
                    self._update_table()
                    QMessageBox.information(self, "成功", "列移动成功")
                else:
                    QMessageBox.warning(self, "操作失败", "列移动失败")
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
                    QMessageBox.information(self, "成功", "列移动成功")
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

    def _rename_column(self, col):
        """重命名列 - View层事件触发"""
        if col >= 0:
            # 获取新列名
            current_name = self.service.data_model.headers[col]
            new_name, ok = QInputDialog.getText(self, "重命名列", "请输入新列名:", text=current_name)
            if ok and new_name:
                # 同步表格数据到模型
                self._sync_table_to_model()
                # 调用服务层重命名列
                result = self.service.rename_column(col, new_name)
                if result:
                    self._update_table()
                else:
                    QMessageBox.warning(self, "操作失败", "列重命名失败")
        else:
            QMessageBox.warning(self, "操作失败", "请选择要重命名的列")

    def _remove_column(self):
        """删除列 - View层事件触发"""
        column_index = self.table_widget.currentColumn()
        if column_index >= 0:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            result = self.service.remove_column(column_index)
            if not result:
                QMessageBox.warning(self, "操作失败", "删除列失败")
            self._update_table()
        else:
            QMessageBox.warning(self, "操作失败", "请选择要删除的列")

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

    def _move_row(self):
        """移动行 - View层事件触发"""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 询问要移动到的位置
            new_position, ok = QInputDialog.getInt(
                self, "移动行", "请输入目标行位置(从0开始):", 
                current_row, 0, len(self.service.data_model.rows)-1)
            if ok and new_position != current_row:
                if self.service.move_row(current_row, new_position):
                    self._update_table()
                    QMessageBox.information(self, "成功", "行移动成功")
                else:
                    QMessageBox.warning(self, "操作失败", "行移动失败")
        else:
            QMessageBox.warning(self, "操作失败", "请先选择一行")

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
                    QMessageBox.information(self, "成功", "行移动成功")
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
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            result = self.service.remove_row(row_index)
            if not result:
                QMessageBox.warning(self, "操作失败", "删除行失败")
            self._update_table()
        else:
            QMessageBox.warning(self, "操作失败", "请选择要删除的行")

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
            # 触发Controller层处理
            if self.service.export_to_excel(file_path):
                QMessageBox.information(self, "成功", "数据已成功导出到Excel")
            else:
                QMessageBox.warning(self, "错误", "导出失败")

    def _import_from_spec(self):
        """从Spec导入数据 - View层事件触发"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Spec文件", "", "Spec Files (*.pdf *.doc *.docx *.xls *.xlsx)"
        )
        if file_path:
            print(f"选择的文件路径: {file_path}")
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            print("开始导入Spec数据...")
            if self.service.import_from_spec(file_path):
                print("Spec数据导入成功")
                # 静默更新，不显示成功消息框
                self._update_table()
            else:
                print("Spec数据导入失败")
                QMessageBox.warning(self, "错误", "导入失败")

    def _import_from_excel(self):
        """从Excel导入数据 - View层事件触发"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            if self.service.import_from_excel(file_path):
                QMessageBox.information(self, "成功", "数据已成功导入")
                self._update_table()
            else:
                QMessageBox.warning(self, "错误", "导入失败")