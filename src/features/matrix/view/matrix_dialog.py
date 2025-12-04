# src/features/matrix/view/matrix_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel, QTimer
from PyQt5.QtGui import QCursor

from src.features.matrix.service.matrix_service import MatrixService
from src.core.logger import logger
# 导入筛选对话框
from src.features.matrix.view.matrix_filter_dialog import MatrixFilterDialog
# 导入Test Record生成控制器
from src.features.test_record_generator.controller.test_record_controller import TestRecordController
# 导入导出对话框
from src.features.matrix.service.export.view.export_dialog import ExportDialog
# 导入状态管理器
from src.core.state_manager import state_manager
import os


class MatrixDialog(QDialog):
    """Matrix视图 - View层"""

    def __init__(self, parent=None, service=None, ltr_number=None):
        super().__init__(parent)
        self.ltr_number = ltr_number
        if ltr_number:
            self.setWindowTitle(f"Matrix编辑器 - LTR: {ltr_number}")
        else:
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
        
        # 在初始化后自动导入项目中的matrix.xlsx文件（如果存在）
        self._auto_import_matrix_from_project()

    def _setup_ui(self):
        """设置用户界面 - View层渲染"""
        layout = QVBoxLayout()

        # 添加按钮区域
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入Matrix")
        self.standardize_and_fill_btn = QPushButton("标准化填充Matrix")
        self.find_btn = QPushButton("查找")
        self.export_btn = QPushButton("生成TestStatus表")
        # 添加更新标准版本按钮
        self.update_standard_versions_btn = QPushButton("更新标准版本")
        # 添加生成Test Record按钮
        self.generate_test_record_btn = QPushButton("生成Test Record")

        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.standardize_and_fill_btn)
        button_layout.addWidget(self.find_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.update_standard_versions_btn)
        button_layout.addWidget(self.generate_test_record_btn)

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
        self.import_btn.clicked.connect(self._import_from_spec)
        self.standardize_and_fill_btn.clicked.connect(self._standardize_and_fill_matrix)
        self.find_btn.clicked.connect(self._find_content)
        self.export_btn.clicked.connect(self._export_to_excel)
        # 连接更新标准版本按钮
        self.update_standard_versions_btn.clicked.connect(self._update_standard_versions)
        # 连接生成Test Record按钮
        self.generate_test_record_btn.clicked.connect(self._generate_test_record)

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
        copy_cells_action = QAction("复制单元格", self)
        paste_cells_action = QAction("粘贴单元格", self)
        
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
        if not hasattr(self, '_copied_cells_data') or self._copied_cells_data is None:
            paste_cells_action.setEnabled(False)
        
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
        
        # 添加列相关菜单项
        add_col_action = QAction("添加列", self)
        insert_col_action = QAction("插入列", self)
        move_col_action = QAction("移动列", self)
        copy_col_action = QAction("复制列", self)
        paste_col_action = QAction("粘贴列", self)
        remove_col_action = QAction("删除列", self)
        
        # 连接动作到处理函数
        add_col_action.triggered.connect(self._add_column)
        insert_col_action.triggered.connect(self._insert_column)
        move_col_action.triggered.connect(lambda: self._move_column(col))
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

    def _add_row(self):
        """添加行 - View层事件触发"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 调用服务层添加行
        self.service.add_row()
        # 更新表格显示
        self._update_table()
        # 移除了成功消息框

    def _insert_row(self):
        """插入行 - View层事件触发"""
        # 获取当前选中行
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 调用服务层插入行
            self.service.insert_row(row)
            # 更新表格显示
            self._update_table()
            # 移除了成功消息框
        else:
            QMessageBox.warning(self, "操作失败", "请选择一行")

    def _move_row_at(self, row):
        """移动行 - View层事件触发"""
        if row >= 0:
            # 弹出行移动对话框
            new_position, ok = QInputDialog.getInt(
                self, "移动行", "请输入目标行位置(从0开始):", 
                row, 0, len(self.service.data_model.rows)-1)

            if ok and new_position != row:
                # 同步表格数据到模型
                self._sync_table_to_model()
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
        # 获取当前选中行
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # 弹出确认对话框
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除第 {row+1} 行吗？", 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 同步表格数据到模型
                self._sync_table_to_model()
                # 调用服务层删除行
                self.service.remove_row(row)
                # 更新表格显示
                self._update_table()
                # 移除了成功消息框
        else:
            QMessageBox.warning(self, "操作失败", "请选择一行")

    def _add_column(self):
        """添加列 - View层事件触发"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 调用服务层添加列
        self.service.add_column()
        # 更新表格显示
        self._update_table()
        # 移除了成功消息框

    def _insert_column(self):
        """插入列 - View层事件触发"""
        # 获取当前选中列
        selected_cols = self.table_widget.selectionModel().selectedColumns()
        if selected_cols:
            col = selected_cols[0].column()
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 调用服务层插入列
            self.service.insert_column(col)
            # 更新表格显示
            self._update_table()
            # 移除了成功消息框
        else:
            QMessageBox.warning(self, "操作失败", "请选择一列")

    def _move_column(self, col):
        """移动列 - View层事件触发"""
        if col >= 0:
            # 弹出列移动对话框
            new_position, ok = QInputDialog.getInt(
                self, "移动列", "请输入目标列位置(从0开始):", 
                col, 0, len(self.service.data_model.headers)-1)

            if ok and new_position != col:
                # 同步表格数据到模型
                self._sync_table_to_model()
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
        # 获取当前选中列
        selected_cols = self.table_widget.selectionModel().selectedColumns()
        if selected_cols:
            col = selected_cols[0].column()
            # 弹出确认对话框
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除第 {col+1} 列吗？", 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 同步表格数据到模型
                self._sync_table_to_model()
                # 调用服务层删除列
                self.service.remove_column(col)
                # 更新表格显示
                self._update_table()
                # 移除了成功消息框
        else:
            QMessageBox.warning(self, "操作失败", "请选择一列")

    def _update_table(self):
        """更新表格显示 - View层渲染"""
        logger.debug("开始更新表格显示")
        # 移除更新表格显示的详细日志
        # 断开信号连接以避免在更新过程中触发事件
        try:
            self.table_widget.itemChanged.disconnect(self._on_item_changed)
        except TypeError:
            # 如果信号尚未连接，则忽略错误
            pass
        
        try:
            # 清空现有内容
            self.table_widget.clear()
            
            # 设置表头
            headers_count = len(self.service.data_model.headers)
            rows_count = len(self.service.data_model.rows)
            logger.debug(f"准备设置表格，表头数: {headers_count}, 行数: {rows_count}")
            
            self.table_widget.setColumnCount(headers_count)
            self.table_widget.setHorizontalHeaderLabels(self.service.data_model.headers)
            
            # 设置行数和数据
            self.table_widget.setRowCount(rows_count)
            logger.debug("开始填充表格数据")
            
            # 分批更新以避免阻塞UI
            for row_idx, row_data in enumerate(self.service.data_model.rows):
                for col_idx, cell_value in enumerate(row_data):
                    if col_idx < len(row_data):  # 确保不越界
                        try:
                            item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
                            self.table_widget.setItem(row_idx, col_idx, item)
                        except Exception as e:
                            logger.error(f"设置单元格[{row_idx},{col_idx}]时出错: {e}")
                            # 使用空字符串作为后备
                            item = QTableWidgetItem("")
                            self.table_widget.setItem(row_idx, col_idx, item)
            
            logger.debug("表格数据填充完成")
            
            # 应用合并单元格（如果有）
            self._apply_merged_cells()
            logger.debug("合并单元格应用完成")
        except Exception as e:
            logger.error(f"更新表格显示时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"更新表格显示时出错: {e}")
        finally:
            # 重新连接信号
            self.table_widget.itemChanged.connect(self._on_item_changed)
            logger.debug("表格更新完成")

    def _apply_merged_cells(self):
        """应用合并单元格"""
        try:
            # 清除现有的合并单元格
            for row in range(self.table_widget.rowCount()):
                for col in range(self.table_widget.columnCount()):
                    self.table_widget.setSpan(row, col, 1, 1)
            
            # 应用存储的合并单元格信息
            for merge_info in self.service.data_model.merged_cells_info:
                top_row = merge_info['top_row']
                left_col = merge_info['left_col']
                row_count = merge_info['row_count']
                col_count = merge_info['col_count']
                
                # 检查边界
                if (top_row + row_count <= self.table_widget.rowCount() and 
                    left_col + col_count <= self.table_widget.columnCount()):
                    self.table_widget.setSpan(top_row, left_col, row_count, col_count)
        except Exception as e:
            logger.error(f"应用合并单元格时出错: {e}", exc_info=True)

    def _on_item_changed(self, item):
        """处理表格项变更事件"""
        try:
            row = item.row()
            col = item.column()
            value = item.text()
            logger.debug(f"表格项变更: [{row},{col}] = '{value}'")
            # 更新数据模型
            self.service.set_cell_value(row, col, value)
        except Exception as e:
            logger.error(f"处理表格项变更时出错: {e}", exc_info=True)

    def _sync_table_to_model(self):
        """同步表格数据到数据模型"""
        try:
            # 移除同步表格数据的详细日志
            for row in range(self.table_widget.rowCount()):
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        self.service.set_cell_value(row, col, item.text())
                    else:
                        self.service.set_cell_value(row, col, "")
        except Exception as e:
            logger.error(f"同步表格数据到模型时出错: {e}", exc_info=True)

    def _import_from_spec(self):
        """从Spec导入数据 - View层事件触发"""
        try:
            logger.debug("开始执行导入Spec操作")
            # 弹出文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择规格书文件", "", "Word Files (*.docx *.doc);;PDF Files (*.pdf);;All Files (*)"
            )
            if file_path:
                logger.debug(f"选择了文件: {file_path}")
                # 检查文件扩展名
                _, ext = os.path.splitext(file_path.lower())
                if ext in ['.pdf']:
                    QMessageBox.warning(self, "不支持的格式", "暂不支持PDF格式文件，请选择Word文档(.docx/.doc)")
                    return
                
                # 显示筛选对话框，获取页码和关键字
                filter_dialog = MatrixFilterDialog(self)
                if filter_dialog.exec_() == QDialog.Accepted:
                    filter_params = filter_dialog.get_filter_params()
                    page_number = filter_params['page']
                    keyword = filter_params['keyword']
                    
                    logger.debug(f"筛选参数 - 页码: {page_number}, 关键字: {keyword}")
                    
                    # 同步表格数据到模型
                    logger.debug("同步表格数据到模型")
                    self._sync_table_to_model()
                    
                    # 触发Controller层处理
                    logger.debug("调用服务层导入方法")
                    result = self.service.import_from_spec(file_path, page_number, keyword)
                    logger.debug(f"服务层导入方法返回结果: {result}")
                    if result and result.get("success", False):
                        logger.debug("导入成功，准备更新表格显示")
                        # 使用定时器延迟更新表格显示，避免阻塞UI线程
                        QTimer.singleShot(100, self._update_table)
                        QMessageBox.information(self, "成功", "数据已成功导入")
                    else:
                        error_msg = result.get("error", "导入失败") if result else "导入失败"
                        QMessageBox.warning(self, "失败", f"数据导入失败: {error_msg}")
        except Exception as e:
            logger.error(f"导入Spec时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"导入过程中发生错误: {e}")

    def _standardize_and_fill_matrix(self):
        """标准化填充Matrix - View层事件触发"""
        try:
            logger.info("开始标准化填充Matrix")
            
            # 同步表格数据到模型
            self._sync_table_to_model()
            
            # 先执行标准化操作
            init_result = self.service.initialize_matrix()
            if not init_result:
                QMessageBox.warning(self, "失败", "Matrix标准化失败")
                return
            
            # 再尝试从已导入的规格书中提取测试方法
            extract_result = self.service.extract_test_methods_from_spec()
            
            # 更新标准版本号
            update_result = self.service.update_standard_versions()
            
            # 更新表格显示
            self._update_table()
            
            # 根据结果给出相应提示
            if extract_result and update_result["success"]:
                QMessageBox.information(self, "成功", "Matrix已标准化、填充测试方法并更新标准版本")
            elif extract_result:
                QMessageBox.information(self, "部分成功", "Matrix已标准化并填充测试方法，但标准版本更新失败")
            elif update_result["success"]:
                QMessageBox.information(self, "部分成功", "Matrix已标准化并更新标准版本，但未从规格书中提取到测试方法")
            else:
                QMessageBox.information(self, "部分成功", "Matrix已标准化，但未提取到测试方法且标准版本更新失败")
                
        except Exception as e:
            logger.error(f"标准化填充Matrix时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"标准化填充Matrix时出错: {str(e)}")

    def _find_content(self):
        """查找内容 - View层事件触发"""
        # 弹出输入对话框让用户输入查找内容
        search_text, ok = QInputDialog.getText(self, "查找", "请输入要查找的内容:")
        if ok and search_text:
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 调用服务层查找
            results = self.service.find_by_content(search_text)
            if results:
                # 显示查找结果
                msg = f"找到 {len(results)} 个匹配项:\n"
                for result in results:
                    msg += f"第{result['row']+1}行, {result['header']}列: {result['value']}\n"
                QMessageBox.information(self, "查找结果", msg)
            else:
                QMessageBox.information(self, "查找结果", "未找到匹配项")

    def _export_to_excel(self):
        """导出Test Status表到Excel - View层事件触发"""
        logger.debug("开始执行导出Test Status表到Excel操作")
        try:
            # 直接设置导出类型为test_status
            export_type = "test_status"
            
            # 使用LTR编号作为文件名的一部分
            if self.ltr_number:
                default_filename = f"{self.ltr_number} test status.xlsx"
            else:
                default_filename = "test status.xlsx"
                
            # 获取当前项目路径作为默认保存路径
            current_project = state_manager.get_state("current_project")
            logger.debug(f"当前项目路径: {current_project}")
            if current_project and os.path.exists(current_project):
                default_path = os.path.join(current_project, default_filename)
                logger.debug(f"构建默认路径: {default_path}")
            else:
                default_path = default_filename
                logger.debug(f"使用默认文件名: {default_path}")
                
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存Test Status表", default_path, "Excel Files (*.xlsx)"
            )
            if file_path:
                logger.debug(f"选择的文件路径: {file_path}")
                # 同步表格数据到模型
                self._sync_table_to_model()
                # 导出前先保存合并单元格信息
                self._save_merged_cells_info()
                # 触发Controller层处理
                logger.debug("开始调用服务层导出方法")
                result = self.service.export_to_excel(file_path, export_type)
                logger.debug(f"服务层导出方法返回结果: {result}")
                if result:
                    QMessageBox.information(self, "成功", "Test Status表已成功导出到Excel")
                else:
                    # 检查文件是否被占用
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
        except Exception as e:
            logger.error(f"导出过程中发生异常: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"导出过程中发生异常: {str(e)}")

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
        self.service.data_model.merged_cells_info = merged_cells_info
        # 移除合并单元格信息保存的详细日志

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
            
            # 检查是否因为标准文件缺失而失败
            if "file_missing" in result and result["file_missing"]:
                # 标准文件不存在，显示详细错误信息
                file_path = result.get("file_path", "未知路径")
                QMessageBox.warning(
                    self, 
                    "标准文件不存在", 
                    f"标准目录文件不存在，请检查文件路径:\n{file_path}"
                )
                logger.warning(f"标准文件不存在: {file_path}")
                return
            
            # 检查是否因为没有找到标准数据而失败
            if "no_standards_found" in result and result["no_standards_found"]:
                # 没有找到需要更新的标准数据，这是一个正常情况，不显示错误
                QMessageBox.information(self, "成功", "标准版本号更新完成，没有需要更新的项")
                logger.info("标准版本号更新完成，没有需要更新的项")
                return
            
            if result["success"]:
                # 更新表格显示
                self._update_table()
                
                # 显示更新详情
                details = result["details"]
                if details:
                    details_msg = "\n".join([f"第{detail['row']}行: {detail['old_method']} -> {detail['new_method']}" 
                                             for detail in details])
                    msg = f"标准版本号更新完成，共更新{result['updated_count']}项:\n{details_msg}"
                    # 创建自定义消息框以支持更宽的窗口
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("成功")
                    msg_box.setText(msg)
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.setIcon(QMessageBox.NoIcon)
                    # 设置消息框宽度和内容靠左显示
                    msg_box.setStyleSheet("QLabel{min-width: 400px; text-align: left;}")
                    msg_box.exec_()
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

    def _generate_test_record(self):
        """生成Test Record文档 - View层事件触发"""
        try:
            logger.info("开始生成Test Record文档")
            
            # 同步表格数据到模型
            self._sync_table_to_model()
            
            # 创建Test Record控制器实例
            controller = TestRecordController(matrix_service=self.service)
            
            # 调用控制器生成Test Record（直接使用固定路径）
            success = controller.generate_test_record(parent=self)
            
            if success:
                logger.info("Test Record文档生成成功")
            else:
                # 错误信息已经在controller中处理过了，这里不需要额外提示
                logger.warning("Test Record文档生成失败或被取消")
        except Exception as e:
            logger.error(f"生成Test Record时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"生成Test Record时出错: {str(e)}")

    def _copy_cells(self):
        """复制选中的单元格"""
        selected_ranges = self.table_widget.selectedRanges()
        if not selected_ranges:
            return
            
        # 只处理第一个选区
        range_ = selected_ranges[0]
        
        # 保存选区的行列数和数据
        self._copied_cells_data = {
            'rows': range_.rowCount(),
            'cols': range_.columnCount(),
            'data': []
        }
        
        # 提取选区数据
        for row in range(range_.rowCount()):
            row_data = []
            for col in range(range_.columnCount()):
                item = self.table_widget.item(range_.topRow() + row, range_.leftColumn() + col)
                row_data.append(item.text() if item else "")
            self._copied_cells_data['data'].append(row_data)
        
        logger.debug(f"已复制 {range_.rowCount()}x{range_.columnCount()} 单元格区域")

    def _paste_cells(self):
        """粘贴单元格数据到当前选区"""
        # 检查是否有复制的数据
        if not hasattr(self, '_copied_cells_data') or self._copied_cells_data is None:
            return
            
        selected_ranges = self.table_widget.selectedRanges()
        if not selected_ranges:
            return
            
        # 只处理第一个选区
        range_ = selected_ranges[0]
        
        # 获取复制的数据
        copied_data = self._copied_cells_data['data']
        copied_rows = self._copied_cells_data['rows']
        copied_cols = self._copied_cells_data['cols']
        
        # 计算实际粘贴范围（要考虑边界限制）
        actual_rows = min(copied_rows, self.table_widget.rowCount() - range_.topRow())
        actual_cols = min(copied_cols, self.table_widget.columnCount() - range_.leftColumn())
        
        # 粘贴数据
        for row in range(actual_rows):
            for col in range(actual_cols):
                item = self.table_widget.item(range_.topRow() + row, range_.leftColumn() + col)
                if item:
                    item.setText(copied_data[row][col])
                else:
                    new_item = QTableWidgetItem(copied_data[row][col])
                    self.table_widget.setItem(range_.topRow() + row, range_.leftColumn() + col, new_item)
        
        logger.debug(f"已粘贴 {actual_rows}x{actual_cols} 单元格区域")

    def _auto_import_matrix_from_project(self):
        """
        从项目文件夹自动导入matrix.xlsx文件
        """
        try:
            logger.debug("尝试从项目文件夹自动导入matrix.xlsx")
            
            # 获取当前项目路径
            current_project = state_manager.get_state("current_project")
            if not current_project:
                logger.debug("没有当前项目，跳过自动导入")
                return
                
            # 构造matrix.xlsx文件路径
            matrix_file_path = os.path.join(current_project, "matrix.xlsx")
            
            # 检查文件是否存在
            if os.path.exists(matrix_file_path):
                logger.info(f"发现项目中的matrix.xlsx文件: {matrix_file_path}")
                
                # 导入文件
                from src.features.matrix.service.document_parsers.excel_parser import ExcelParser
                parser = ExcelParser()
                result = parser.parse(matrix_file_path)
                
                if result and 'data' in result and result['data']:
                    # 更新数据模型
                    self.service.data_model.rows = result['data']
                    if 'headers' in result and result['headers']:
                        self.service.data_model.headers = result['headers']
                    else:
                        # 如果没有提供表头，使用默认的字母标识
                        self.service.data_model.headers = [self.service.data_model._column_index_to_letter(i) 
                                                        for i in range(len(result['data'][0]) if result['data'] else 7)]
                    
                    # 更新合并单元格信息
                    if 'merged_cells' in result:
                        self.service.data_model.merged_cells_info = result['merged_cells']
                        
                    # 更新表格显示
                    self._update_table()
                    logger.info("成功自动导入项目中的matrix.xlsx文件")
                else:
                    logger.warning("matrix.xlsx文件中没有有效数据")
            else:
                logger.debug(f"项目中没有matrix.xlsx文件: {matrix_file_path}")
        except Exception as e:
            logger.error(f"自动导入matrix.xlsx文件时出错: {e}")

    def closeEvent(self, event):
        """
        处理窗口关闭事件，自动导出数据到项目文件夹
        """
        try:
            logger.debug("Matrix窗口正在关闭，准备自动导出数据")
            
            # 获取当前项目路径
            current_project = state_manager.get_state("current_project")
            if current_project:
                # 构造matrix.xlsx文件路径
                matrix_file_path = os.path.join(current_project, "matrix.xlsx")
                
                # 同步表格数据到模型
                self._sync_table_to_model()
                
                # 导出前先保存合并单元格信息
                self._save_merged_cells_info()
                
                # 自动导出到项目文件夹
                if self.service.export_to_excel(matrix_file_path):
                    logger.info(f"Matrix数据已自动导出到: {matrix_file_path}")
                else:
                    logger.error(f"自动导出Matrix数据失败: {matrix_file_path}")
            else:
                logger.debug("没有当前项目，跳过自动导出")
        except Exception as e:
            logger.error(f"自动导出Matrix数据时出错: {e}")
            
        # 调用父类的closeEvent以确保窗口正常关闭
        super().closeEvent(event)