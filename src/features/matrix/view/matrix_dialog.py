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
# 导入Test Record生成控制器
from src.features.test_record_generator.controller.test_record_controller import TestRecordController


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
        self.standardize_and_fill_btn = QPushButton("标准化填充Matrix")
        self.find_btn = QPushButton("查找")
        self.export_btn = QPushButton("导出Excel")
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
                f"确定要删除第 {col+1} 列 ({self.service.data_model.headers[col]}) 吗？", 
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
        logger.debug("更新表格显示")
        
        # 清空表格
        self.table_widget.clear()
        
        # 设置表头
        self.table_widget.setColumnCount(len(self.service.data_model.headers))
        self.table_widget.setHorizontalHeaderLabels(self.service.data_model.headers)
        
        # 设置行数
        self.table_widget.setRowCount(len(self.service.data_model.rows))
        
        # 填充数据
        for row_idx, row_data in enumerate(self.service.data_model.rows):
            for col_idx, cell_data in enumerate(row_data):
                if col_idx < len(self.service.data_model.headers):
                    item = QTableWidgetItem(str(cell_data))
                    self.table_widget.setItem(row_idx, col_idx, item)
        
        # 应用合并单元格信息
        for merge_info in self.service.data_model.merged_cells_info:
            top_row = merge_info['top_row']
            left_col = merge_info['left_col']
            row_count = merge_info['row_count']
            col_count = merge_info['col_count']
            
            # 检查边界，确保不会超出表格范围
            if (top_row + row_count <= self.table_widget.rowCount() and 
                left_col + col_count <= self.table_widget.columnCount()):
                self.table_widget.setSpan(top_row, left_col, row_count, col_count)
                logger.debug(f"设置合并单元格: 行{top_row}-{top_row+row_count-1}, 列{left_col}-{left_col+col_count-1}")
            else:
                logger.warning(f"合并单元格信息超出表格范围: {merge_info}")

    def _sync_table_to_model(self):
        """同步表格数据到数据模型 - View层数据同步"""
        logger.debug("同步表格数据到数据模型")
        
        # 清空现有数据
        self.service.data_model.rows = []
        
        # 从表格中读取数据
        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            self.service.data_model.rows.append(row_data)
        
        # 更新表头（如果需要）
        # 注意：在当前实现中，表头是固定的，不会从表格中读取

    def _import_from_spec(self):
        """从Spec导入数据 - View层事件触发"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择规格书文件", "", "Documents (*.pdf *.doc *.docx *.xls *.xlsx)"
        )
        if file_path:
            # 弹出输入对话框让用户选择页码
            page_number, ok = QInputDialog.getInt(
                self, "输入页码", "请输入要提取的页码(从1开始，0表示全部页面):", 0, 0, 10000)
            if not ok:
                return
                
            # 弹出输入对话框让用户输入关键字
            keyword, ok = QInputDialog.getText(
                self, "输入关键字", "请输入筛选关键字(留空表示不过滤):")
            if not ok:
                return
                
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 触发Controller层处理
            success = self.service.import_from_spec(file_path, page_number if page_number > 0 else None, 
                                                  keyword if keyword else None)
            if success:
                # 更新表格显示
                self._update_table()
                QMessageBox.information(self, "成功", "数据导入成功")
            else:
                QMessageBox.warning(self, "失败", "数据导入失败")

    def _standardize_and_fill_matrix(self):
        """标准化填充Matrix - 集成功能，执行标准化Matrix、填充测试规格和更新标准版本"""
        try:
            logger.info("开始执行标准化填充Matrix集成功能")
            
            # 1. 标准化Matrix
            logger.info("步骤1: 执行标准化Matrix")
            self._sync_table_to_model()
            if not self.service.initialize_matrix():
                QMessageBox.warning(self, "失败", "Matrix标准化失败")
                logger.warning("Matrix标准化失败")
                return
            self._update_table()
            
            # 2. 填充测试规格
            logger.info("步骤2: 执行填充测试规格")
            self._sync_table_to_model()
            success = self.service.extract_test_methods_from_spec()
            if not success:
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
                return
            self._update_table()
            
            # 3. 更新标准版本
            logger.info("步骤3: 执行更新标准版本")
            self._sync_table_to_model()
            result = self.service.update_standard_versions()
            if result["success"]:
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
                    msg_box.setIcon(QMessageBox.Information)
                    # 设置消息框宽度，以便完整显示更新信息
                    msg_box.setStyleSheet("QLabel{min-width: 600px;}")
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
            
            # 全部完成
            logger.info("标准化填充Matrix集成功能执行完成")
            # 集成操作成功时不弹出提示窗口
            # QMessageBox.information(self, "完成", "标准化填充Matrix集成功能执行完成")
            
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
            results = self.service.find_content(search_text)
            if results:
                # 显示查找结果
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
        logger.debug(f"保存了 {len(merged_cells_info)} 个合并单元格信息")

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
                                               for detail in details])
                    msg = f"标准版本号更新完成，共更新{result['updated_count']}项:\n{details_msg}"
                    # 创建自定义消息框以支持更宽的窗口
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("成功")
                    msg_box.setText(msg)
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.setIcon(QMessageBox.Information)
                    # 设置消息框宽度，以便完整显示更新信息
                    msg_box.setStyleSheet("QLabel{min-width: 600px;}")
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
                QMessageBox.information(self, "成功", "Test Record文档已生成到 D:\\outfile\\testrecord.docx")
                logger.info("Test Record文档生成成功")
            else:
                # 错误信息已经在controller中处理过了，这里不需要额外提示
                logger.warning("Test Record文档生成失败或被取消")
        except Exception as e:
            logger.error(f"生成Test Record时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"生成Test Record时出错: {str(e)}")
