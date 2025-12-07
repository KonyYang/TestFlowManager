# src/features/matrix/view/matrix_dialog.py
from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QMenu, QAction,
    QDialog
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
# 导入工具栏组件
from src.features.matrix.view.components.matrix_toolbar import MatrixToolbar
# 导入上下文菜单组件
from src.features.matrix.view.components.matrix_context_menus import MatrixContextMenus
# 导入表格管理器
from src.features.matrix.view.managers.table_manager import TableManager
# 导入数据同步管理器
from src.features.matrix.view.managers.data_sync_manager import DataSyncManager
# 导入导入/导出管理器
from src.features.matrix.view.managers.import_export_manager import ImportExportManager
# 导入事件处理器
from src.features.matrix.view.handlers.matrix_event_handlers import MatrixEventHandlers
import os


class MatrixDialog(QWidget):
    """Matrix视图 - View层（嵌入式版本）"""

    def __init__(self, parent=None, service=None, ltr_number=None):
        super().__init__(parent)
        self.ltr_number = ltr_number
        if ltr_number:
            self.setWindowTitle(f"Matrix编辑器 - LTR: {ltr_number}")
        else:
            self.setWindowTitle("Matrix编辑器")
        
        # 复制行/列的数据缓存
        self.copied_row_data = None
        self.copied_col_data = None

        if service is None:
            self.service = MatrixService()
        else:
            self.service = service

        # 初始化组件
        self._init_components()
        
        self._setup_ui()
        
        # 在初始化后自动导入项目中的matrix.xlsx文件（如果存在）
        self.import_export_manager.auto_import_matrix_from_project()

    def _init_components(self):
        """初始化各个组件"""
        # 初始化表格管理器
        self.table_manager = TableManager(self, self.service)
        
        # 初始化数据同步管理器
        self.data_sync_manager = DataSyncManager(self, self.service)
        
        # 初始化导入/导出管理器
        self.import_export_manager = ImportExportManager(self, self.service)
        
        # 初始化事件处理器
        self.event_handlers = MatrixEventHandlers(self, self.service)
        
        # 初始化上下文菜单
        self.context_menus = MatrixContextMenus(self, self.service)

    # 添加exec_方法以兼容QDialog的使用方式
    def exec_(self):
        """
        兼容QDialog的exec_方法
        对于QWidget，显示窗口并返回Accepted
        """
        self.show()
        return QDialog.Accepted

    def _setup_ui(self):
        """设置用户界面 - View层渲染"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 使用外部工具栏组件
        self.toolbar = MatrixToolbar(self.service, self)
        layout.addLayout(self.toolbar.layout())
        
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
        self.table_widget.customContextMenuRequested.connect(self.context_menus.show_cell_context_menu)
        # 连接行头和列头的右键菜单事件
        self.table_widget.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.verticalHeader().customContextMenuRequested.connect(self.context_menus.show_row_context_menu)
        self.table_widget.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.horizontalHeader().customContextMenuRequested.connect(self.context_menus.show_col_context_menu)
        # 连接选择变化信号以更新菜单状态
        self.table_widget.itemSelectionChanged.connect(self._on_item_selection_changed)
        # 设置选择模式为连续选择
        self.table_widget.setSelectionMode(QTableWidget.ContiguousSelection)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectItems)

        # 设置表格初始状态
        self.table_manager.update_table()

        # 连接信号到事件处理器
        self.toolbar.connect_signals(self.event_handlers)

        layout.addWidget(self.table_widget)
        
        # 存储菜单项引用以便动态更新
        self.merge_or_split_action = None

    def _on_item_selection_changed(self):
        """当选择项改变时更新菜单状态"""
        logger.debug("选择项发生变化")
        # 如果菜单项存在，则更新它们的状态
        if self.merge_or_split_action:
            self.context_menus.update_cell_menu_actions()

    def _undo_cell_operation(self):
        """撤销单元格操作"""
        logger.debug("执行撤销单元格操作")
        self.service.undo_cell_operation()

    def _redo_cell_operation(self):
        """重做单元格操作"""
        logger.debug("执行重做单元格操作")
        self.service.redo_cell_operation()

    def _merge_or_split_cells(self):
        """根据选中单元格的状态执行合并或拆分操作"""
        logger.debug("执行合并或拆分单元格操作")
        self.service.merge_or_split_cells(self.table_widget)

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
        """同步表格数据到模型 - View层数据同步"""
        self.data_sync_manager.sync_table_to_model()

    def _update_table(self):
        """更新表格显示"""
        self.table_manager.update_table()

    def _save_merged_cells_info(self):
        """保存合并单元格信息"""
        self.data_sync_manager.save_merged_cells_info()

    def _add_row(self):
        """添加行"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 使用表格管理器添加行
        self.table_manager.add_row()

    def _insert_row(self):
        """插入行"""
        # 获取当前选中行
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 使用表格管理器插入行
            self.table_manager.insert_row(row)
        else:
            QMessageBox.warning(self, "操作失败", "请选择一行")

    def _move_row_at(self, row):
        """移动行"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 使用表格管理器移动行
        self.table_manager.move_row(row)

    def _copy_row(self, row):
        """复制行"""
        # 使用表格管理器复制行
        self.copied_row_data = self.table_manager.copy_row(row)

    def _paste_row(self, row):
        """粘贴行"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 使用表格管理器粘贴行
        self.table_manager.paste_row(row)

    def _remove_row(self):
        """删除行"""
        # 获取当前选中行
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 使用表格管理器删除行
            self.table_manager.remove_row(row)
        else:
            QMessageBox.warning(self, "操作失败", "请选择一行")

    def _add_column(self):
        """添加列"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 使用表格管理器添加列
        self.table_manager.add_column()

    def _insert_column(self):
        """插入列"""
        # 获取当前选中列
        selected_cols = self.table_widget.selectionModel().selectedColumns()
        if selected_cols:
            col = selected_cols[0].column()
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 使用表格管理器插入列
            self.table_manager.insert_column(col)
        else:
            QMessageBox.warning(self, "操作失败", "请选择一列")

    def _move_column(self, col):
        """移动列"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 使用表格管理器移动列
        self.table_manager.move_column(col)

    def _copy_column(self, col):
        """复制列"""
        # 使用表格管理器复制列
        self.copied_col_data = self.table_manager.copy_column(col)

    def _paste_column(self, col):
        """粘贴列"""
        # 同步表格数据到模型
        self._sync_table_to_model()
        # 使用表格管理器粘贴列
        self.table_manager.paste_column(col)

    def _remove_column(self):
        """删除列"""
        # 获取当前选中列
        selected_cols = self.table_widget.selectionModel().selectedColumns()
        if selected_cols:
            col = selected_cols[0].column()
            # 同步表格数据到模型
            self._sync_table_to_model()
            # 使用表格管理器删除列
            self.table_manager.remove_column(col)
        else:
            QMessageBox.warning(self, "操作失败", "请选择一列")

    def _import_from_spec(self):
        """从Spec导入数据 - View层事件触发"""
        self.event_handlers.on_import_clicked()

    def _standardize_and_fill_matrix(self):
        """标准化填充Matrix - View层事件触发"""
        self.event_handlers.on_standardize_and_fill_clicked()

    def _show_basic_info_dialog(self):
        """显示基本信息对话框 - View层事件触发"""
        self.event_handlers.on_show_basic_info_dialog()

    def _generate_test_status(self):
        """生成Test Status表 - View层事件触发"""
        self.event_handlers.on_export_clicked()

    def _update_standard_versions(self):
        """更新标准版本号 - View层事件触发"""
        self.event_handlers.on_update_standards_clicked()

    def _generate_test_record(self):
        """生成Test Record文档 - View层事件触发"""
        self.event_handlers.on_generate_test_record_clicked()

    def _auto_import_matrix_from_project(self):
        """
        从项目文件夹自动导入matrix.xlsx文件
        """
        self.import_export_manager.auto_import_matrix_from_project()
