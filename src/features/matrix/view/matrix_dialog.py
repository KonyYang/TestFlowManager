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
        # 禁用单元格的右键菜单，只保留行头和列头的右键菜单
        self.table_widget.setContextMenuPolicy(Qt.NoContextMenu)
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

    def _show_context_menu(self, position):
        """显示右键菜单"""
        # 移除此方法，因为我们不再需要单元格的右键菜单
        pass

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
        
        # 根据行位置启用/禁用某些菜单项
        if row == 0 or row == len(self.service.data_model.rows) - 1:  # 标题行或最后一行
            remove_row_action.setEnabled(False)
            move_row_action.setEnabled(False)
            
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
        
        # 根据列位置启用/禁用某些菜单项
        if col < 5:  # 前5列是保护列
            remove_col_action.setEnabled(False)
        elif col == len(self.service.data_model.headers) - 1:  # 最后一列是Remark列
            remove_col_action.setEnabled(False)
            
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
                self.table_widget.setItem(row_idx, col_idx, item)
                
        # 显示前几行的数据用于调试
        if len(self.service.data_model.rows) > 0 and len(self.service.data_model.headers) > 0:
            print(f"表头: {self.service.data_model.headers[:5]}...")
            for i, row in enumerate(self.service.data_model.rows[:3]):  # 只显示前3行
                print(f"第{i+1}行: {row[:5] if len(row) > 5 else row}...")

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
                # 在当前选中列之后插入新列（但不能在保护列之前，也不能在Remark列之后）
                insert_position = max(5, current_col + 1)
                # 确保不在Remark列之后插入
                if insert_position >= len(self.service.data_model.headers) - 1:
                    insert_position = len(self.service.data_model.headers) - 1
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
            # 检查列是否可以重命名
            if col < 5 or col == len(self.service.data_model.headers) - 1:
                QMessageBox.warning(self, "操作失败", "无法重命名保护列")
                return
                
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
                if column_index < 5:  # 保护的列无法删除
                    QMessageBox.warning(self, "操作失败", "无法删除默认列，请删除用户自定义列")
                elif column_index == len(self.service.data_model.headers) - 1:  # Remark列
                    QMessageBox.warning(self, "操作失败", "无法删除Remark列")
                else:
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
            # 移除对第一行和最后一行的限制，允许在任何位置插入
            # 检查是否是有效的位置
            if current_row < 0 or current_row >= len(self.service.data_model.rows):
                QMessageBox.warning(self, "操作失败", "无法在选定位置插入新行")
            else:
                # 触发Controller层处理
                result = self.service.insert_row(current_row)
                if result:
                    self._update_table()
                    # 不再弹出成功提醒
                    # QMessageBox.information(self, "成功", "行插入成功")
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
            # 检查是否是受保护的行
            if row_index == 0:  # 第一行
                QMessageBox.warning(self, "操作失败", "无法删除第一行")
            elif row_index == len(self.service.data_model.rows) - 1:  # 最后一行
                QMessageBox.warning(self, "操作失败", "无法删除最后一行")
            else:
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
                QMessageBox.information(self, "成功", "数据已成功导入")
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