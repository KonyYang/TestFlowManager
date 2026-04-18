from typing import Optional

import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QHeaderView, QMessageBox, QTableWidget, QVBoxLayout, QWidget

from src.core.logger import logger
from src.core.project_context import ProjectContext, resolve_project_data_file_path
from src.features.matrix.controller.matrix_controller import MatrixController
from src.features.matrix.view.components.matrix_context_menus import MatrixContextMenus
from src.features.matrix.view.components.matrix_table_styles import MATRIX_TABLE_STYLESHEET
from src.features.matrix.view.components.matrix_toolbar import MatrixToolbar
from src.features.matrix.view.handlers.matrix_event_handlers import MatrixEventHandlers
from src.features.matrix.view.managers.data_sync_manager import DataSyncManager
from src.features.matrix.view.managers.import_export_manager import ImportExportManager
from src.features.matrix.view.managers.table_manager import TableManager


class MatrixPage(QWidget):
    """Matrix 页面视图组件
    
    负责 Matrix 表格的完整 UI 展示和用户交互，包括：
    - 工具栏和表格控件的布局管理
    - 行列操作的委托调用（增删改查、移动、复制粘贴）
    - 数据同步管理（表格与模型之间的双向同步）
    - 导入导出功能的管理
    - 右键菜单和事件处理的协调
    - 项目上下文的传递和管理
    """

    def __init__(self, matrix_controller: MatrixController, parent: Optional[QWidget] = None):
        """初始化 Matrix 页面
        
        Args:
            matrix_controller: Matrix 控制器实例，负责业务逻辑处理
            parent: 父窗口组件
        """
        super().__init__(parent)
        self.matrix_controller = matrix_controller

        # UI 组件管理器
        self.matrix_toolbar: Optional[MatrixToolbar] = None  # 工具栏
        self.matrix_table_widget: Optional[QTableWidget] = None  # 表格控件
        self.matrix_table_manager: Optional[TableManager] = None  # 表格管理器
        self.matrix_data_sync_manager: Optional[DataSyncManager] = None  # 数据同步管理器
        self.matrix_import_export_manager: Optional[ImportExportManager] = None  # 导入导出管理器
        self.matrix_event_handlers: Optional[MatrixEventHandlers] = None  # 事件处理器
        self.matrix_context_menus: Optional[MatrixContextMenus] = None  # 右键菜单管理器

        # 剪贴板数据存储（用于行列复制粘贴操作）
        self.matrix_copied_row_data = None  # 复制的行数据
        self.matrix_copied_col_data = None  # 复制的列数据
        self.copied_row_data = None  # 兼容旧版本的行数据副本
        self.copied_col_data = None  # 兼容旧版本的列数据副本
        self._copied_cells_data = None  # 复制的单元格数据
        self._matrix_table_initialized = False  # 表格是否已初始化标记
        self.project_context: Optional[ProjectContext] = None  # 项目上下文对象
        self.session_id: Optional[str] = None  # 页面绑定的 Matrix session id
        self.session_entry_name: Optional[str] = None  # 页面绑定入口标识

        # 构建 UI 界面
        self._setup_ui()

    @property
    def ltr_number(self):
        """获取 LTR 编号（从控制器中读取）"""
        return getattr(self.matrix_controller, "ltr_number", None)

    def get_table_widget(self) -> Optional[QTableWidget]:
        """获取表格控件实例"""
        return self.matrix_table_widget

    def bind_session(self, session_id: Optional[str], *, entry_name: Optional[str] = None) -> None:
        """绑定页面到显式 Matrix session 元数据。"""
        self.session_id = session_id
        self.session_entry_name = entry_name

    def clear_session_binding(self) -> None:
        """清理页面 session 绑定元数据。"""
        self.bind_session(None, entry_name=None)

    def get_session_binding(self) -> tuple[Optional[str], Optional[str]]:
        """获取页面当前 session 绑定元数据。"""
        return self.session_id, self.session_entry_name

    def has_table_widget(self) -> bool:
        """检查表格控件是否已创建"""
        return self.matrix_table_widget is not None

    def get_copied_cells_data(self):
        """获取复制的单元格数据"""
        return self._copied_cells_data

    def set_copied_cells_data(self, copied_cells_data) -> None:
        """设置复制的单元格数据"""
        self._copied_cells_data = copied_cells_data

    def get_copied_row_data(self):
        """获取复制的行数据"""
        return self.matrix_copied_row_data

    def set_copied_row_data(self, copied_row_data) -> None:
        """设置复制的行数据（同时更新新旧字段以保持兼容）"""
        self.matrix_copied_row_data = copied_row_data
        self.copied_row_data = copied_row_data

    def get_copied_col_data(self):
        """获取复制的列数据"""
        return self.matrix_copied_col_data

    def set_copied_col_data(self, copied_col_data) -> None:
        """设置复制的列数据（同时更新新旧字段以保持兼容）"""
        self.matrix_copied_col_data = copied_col_data
        self.copied_col_data = copied_col_data

    def get_project_context(self) -> Optional[ProjectContext]:
        """获取项目上下文对象（优先使用本地缓存，否则从控制器获取）"""
        return self.project_context or self.matrix_controller.get_project_context()

    def get_project_path(self) -> Optional[str]:
        """获取当前项目路径"""
        project_context = self.get_project_context()
        return project_context.project_path if project_context else None

    def get_project_data_file_path(self) -> Optional[str]:
        """获取项目数据文件路径（JSON 文件）"""
        project_context = self.get_project_context()
        return resolve_project_data_file_path(project_context)

    def resolve_project_data_file_path(self) -> Optional[str]:
        """解析项目数据文件路径
        
        按以下优先级查找 JSON 数据文件：
        1. 从项目上下文获取标准路径
        2. 在项目目录中查找第一个 JSON 文件
        3. 在父目录中查找第一个 JSON 文件
        
        Returns:
            找到的数据文件路径，未找到则返回 None
        """
        project_data_file_path = self.get_project_data_file_path()
        if project_data_file_path and os.path.exists(project_data_file_path):
            return project_data_file_path

        current_project = self.get_project_path()
        if not current_project or not os.path.exists(current_project):
            return project_data_file_path

        try:
            json_files = [f for f in os.listdir(current_project) if f.endswith(".json")]
            if json_files:
                return os.path.join(current_project, json_files[0])

            parent_path = os.path.dirname(current_project)
            if os.path.exists(parent_path):
                parent_json_files = [f for f in os.listdir(parent_path) if f.endswith(".json")]
                if parent_json_files:
                    return os.path.join(parent_path, parent_json_files[0])
        except Exception as exc:
            logger.error(f"查找项目数据文件时出错: {exc}")

        return project_data_file_path

    def build_default_output_path(self, filename: str) -> str:
        """构建默认输出文件路径（基于项目目录）
        
        Args:
            filename: 文件名
            
        Returns:
            完整的文件路径
        """
        project_path = self.get_project_path()
        if project_path and os.path.exists(project_path):
            return os.path.join(project_path, filename)
        return filename

    def get_data_model(self):
        """获取 Matrix 数据模型"""
        return self.matrix_controller.get_matrix_data()

    def sync_service_exports(self) -> None:
        """将表格数据同步到数据模型"""
        self.matrix_controller.sync_table_to_model()

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """从规格书导入测试方法
        
        Args:
            file_path: 规格书文件路径
            page_number: 页码（可选）
            keyword: 搜索关键词（可选）
        """
        return self.matrix_controller.import_from_spec(file_path, page_number, keyword)

    def initialize_matrix(self):
        """初始化 Matrix 数据结构"""
        return self.matrix_controller.initialize_matrix()

    def extract_test_methods_from_spec(self):
        """从规格书中提取测试方法"""
        return self.matrix_controller.extract_test_methods_from_spec()

    def update_standard_versions(self):
        """更新标准版本号"""
        return self.matrix_controller.update_standard_versions()

    def standardize_and_fill_matrix(self):
        """执行 Matrix 标准化填充主流程。"""
        return self.matrix_controller.standardize_and_fill_matrix()

    def export_to_excel(self, file_path, export_type="matrix_excel"):
        """导出 Matrix 到 Excel 文件
        
        Args:
            file_path: 导出文件路径
            export_type: 导出类型（默认 matrix_excel）
        """
        return self.matrix_controller.export_to_excel(file_path, export_type)

    def can_undo_cell_operation(self):
        """检查是否可以撤销单元格操作"""
        return self.matrix_controller.can_undo_cell_operation()

    def get_undo_cell_operation_text(self):
        """获取撤销操作的显示文本"""
        return self.matrix_controller.get_undo_cell_operation_text()

    def can_redo_cell_operation(self):
        """检查是否可以重做单元格操作"""
        return self.matrix_controller.can_redo_cell_operation()

    def get_redo_cell_operation_text(self):
        """获取重做操作的显示文本"""
        return self.matrix_controller.get_redo_cell_operation_text()

    # ==================== 行操作委托方法 ====================
    
    def append_row_to_model(self):
        """在模型末尾添加一行"""
        self.matrix_controller.add_row()

    def insert_row_to_model(self, row):
        """在指定位置插入一行
        
        Args:
            row: 插入位置的行索引
        """
        self.matrix_controller.insert_row(row)

    def remove_row_from_model(self, row):
        """从模型中删除指定行
        
        Args:
            row: 要删除的行索引
        """
        self.matrix_controller.remove_row(row)

    def move_row_in_model(self, row, new_position):
        """在模型中移动行位置
        
        Args:
            row: 当前行索引
            new_position: 目标位置
        """
        return self.matrix_controller.move_row(row, new_position)

    def copy_row_from_model(self, row):
        """从模型中复制行数据
        
        Args:
            row: 要复制的行索引
        """
        return self.matrix_controller.copy_row(row)

    def paste_row_to_model(self, row, copied_row_data):
        """将复制的行数据粘贴到模型
        
        Args:
            row: 粘贴位置的行索引
            copied_row_data: 复制的行数据
        """
        return self.matrix_controller.paste_row(row, copied_row_data)

    # ==================== 列操作委托方法 ====================
    
    def append_column_to_model(self):
        """在模型末尾添加一列"""
        self.matrix_controller.add_column()

    def insert_column_to_model(self, col):
        """在指定位置插入一列
        
        Args:
            col: 插入位置的列索引
        """
        self.matrix_controller.insert_column(col)

    def remove_column_from_model(self, col):
        """从模型中删除指定列
        
        Args:
            col: 要删除的列索引
        """
        self.matrix_controller.remove_column(col)

    def move_column_in_model(self, col, new_position):
        """在模型中移动列位置
        
        Args:
            col: 当前列索引
            new_position: 目标位置
        """
        return self.matrix_controller.move_column(col, new_position)

    def copy_column_from_model(self, col):
        """从模型中复制列数据
        
        Args:
            col: 要复制的列索引
        """
        return self.matrix_controller.copy_column(col)

    def paste_column_to_model(self, col, copied_col_data):
        """将复制的列数据粘贴到模型
        
        Args:
            col: 粘贴位置的列索引
            copied_col_data: 复制的列数据
        """
        return self.matrix_controller.paste_column(col, copied_col_data)

    def _setup_ui(self):
        """构建 UI 界面布局
        
        创建并配置以下组件：
        1. 工具栏（MatrixToolbar）
        2. 表格控件（QTableWidget）及样式
        3. 各类管理器（表格管理、数据同步、导入导出、事件处理、右键菜单）
        4. 信号槽连接
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 创建工具栏
        self.matrix_toolbar = MatrixToolbar(self.matrix_controller, self)
        layout.addWidget(self.matrix_toolbar.get_widget())

        # 创建并配置表格控件
        self.matrix_table_widget = QTableWidget()
        self.matrix_table_widget.setStyleSheet(MATRIX_TABLE_STYLESHEET)
        # 配置表头行为
        self.matrix_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.matrix_table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.matrix_table_widget.verticalHeader().setVisible(True)
        self.matrix_table_widget.setAlternatingRowColors(True)
        self.matrix_table_widget.setSelectionMode(QTableWidget.ContiguousSelection)
        self.matrix_table_widget.setSelectionBehavior(QTableWidget.SelectItems)

        # 初始化管理器组件
        self.matrix_table_manager = TableManager(self)
        self.matrix_data_sync_manager = DataSyncManager(self)
        self.matrix_import_export_manager = ImportExportManager(self, self.matrix_controller)
        self.matrix_event_handlers = MatrixEventHandlers(self)
        self.matrix_context_menus = MatrixContextMenus(self)

        # 配置右键菜单策略
        self.matrix_table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.matrix_table_widget.customContextMenuRequested.connect(
            self.matrix_context_menus.show_cell_context_menu
        )
        self.matrix_table_widget.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.matrix_table_widget.verticalHeader().customContextMenuRequested.connect(
            self.matrix_context_menus.show_row_context_menu
        )
        self.matrix_table_widget.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.matrix_table_widget.horizontalHeader().customContextMenuRequested.connect(
            self.matrix_context_menus.show_col_context_menu
        )
        # 连接选择变化和单元格编辑信号
        self.matrix_table_widget.itemSelectionChanged.connect(self.handle_selection_changed)
        self.matrix_table_widget.itemChanged.connect(self.handle_item_changed)

        # 连接工具栏信号到事件处理器
        self.matrix_toolbar.connect_signals(self.matrix_event_handlers)
        layout.addWidget(self.matrix_table_widget)

        # 延迟初始化表格数据（避免阻塞 UI）
        QTimer.singleShot(0, self.initialize_table)

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        """设置项目上下文
        
        Args:
            project_context: 项目上下文对象
        """
        self.project_context = project_context
        if self.matrix_import_export_manager:
            self.matrix_import_export_manager.set_project_context(project_context)

    def handle_page_activated(self):
        """处理页面激活事件（首次显示时延迟加载表格数据）"""
        if not self._matrix_table_initialized:
            logger.debug("首次显示Matrix页面，延迟加载表格数据")
            try:
                self.matrix_table_manager.update_table()
                self._matrix_table_initialized = True
                logger.debug("Matrix表格数据加载完成")
            except Exception as exc:
                logger.error(f"延迟加载Matrix表格失败: {exc}")

    def initialize_table(self):
        """初始化表格数据（从模型加载到视图）"""
        try:
            logger.debug("开始初始化Matrix表格数据")
            self.matrix_table_manager.update_table()
            self._matrix_table_initialized = True
            logger.debug("Matrix表格初始化完成")
        except Exception as exc:
            logger.error(f"初始化Matrix表格失败: {exc}", exc_info=True)

    def handle_selection_changed(self):
        """处理表格选择项变化事件（更新右键菜单状态）"""
        logger.debug("Matrix表格选择项发生变化")
        if hasattr(self.matrix_context_menus, "update_cell_menu_actions"):
            self.matrix_context_menus.update_cell_menu_actions()

    def sync_to_model(self):
        """将表格数据同步到数据模型"""
        self.matrix_data_sync_manager.sync_table_to_model()

    def refresh_table(self):
        """刷新表格显示（从模型重新加载数据）"""
        self.matrix_table_manager.update_table()

    def save_merged_cells_info(self):
        """保存合并单元格信息"""
        self.matrix_data_sync_manager.save_merged_cells_info()

    def auto_import_from_project(self):
        """从项目中自动导入 Matrix 数据"""
        self.matrix_import_export_manager.auto_import_matrix_from_project()

    def handle_item_changed(self, item):
        """处理表格单元格内容变更事件
        
        Args:
            item: 被修改的表格项
        """
        try:
            row = item.row()
            col = item.column()
            value = item.text()
            logger.debug(f"Matrix表格项变更: [{row},{col}] = '{value}'")
            self.matrix_controller.set_cell_value(row, col, value)
        except Exception as exc:
            logger.error(f"处理 Matrix 表格项变更失败: {exc}", exc_info=True)

    def merge_or_split_cells(self):
        """合并或拆分选中的单元格"""
        self.matrix_controller.merge_or_split_cells(self.matrix_table_widget)

    def undo_cell_operation(self):
        """撤销上一次单元格操作"""
        self.matrix_controller.undo_cell_operation()

    def redo_cell_operation(self):
        """重做已撤销的单元格操作"""
        self.matrix_controller.redo_cell_operation()

    # ==================== 表格行操作方法 ====================
    
    def add_row(self):
        """添加新行到表格末尾"""
        self.sync_to_model()
        self.matrix_table_manager.add_row()

    def insert_row(self):
        """在当前选中行之前插入新行"""
        selected_rows = self.matrix_table_widget.selectionModel().selectedRows()
        if selected_rows:
            self.sync_to_model()
            self.matrix_table_manager.insert_row(selected_rows[0].row())
        else:
            QMessageBox.warning(self, "警告", "请先选择一行")

    def move_row_at(self, row):
        """移动指定行到新位置
        
        Args:
            row: 要移动的行索引
        """
        self.sync_to_model()
        self.matrix_table_manager.move_row(row)

    def copy_row(self, row):
        """复制指定行的数据
        
        Args:
            row: 要复制的行索引
        """
        copied_row_data = self.matrix_table_manager.copy_row(row)
        self.set_copied_row_data(copied_row_data)

    def paste_row(self, row):
        """将复制的行数据粘贴到指定位置
        
        Args:
            row: 粘贴位置的行索引
        """
        self.sync_to_model()
        self.matrix_table_manager.paste_row(row)
        self.copied_row_data = self.matrix_copied_row_data

    def remove_row(self):
        """删除选中的行"""
        selected_rows = self.matrix_table_widget.selectionModel().selectedRows()
        if selected_rows:
            self.sync_to_model()
            self.matrix_table_manager.remove_row(selected_rows[0].row())
        else:
            QMessageBox.warning(self, "警告", "请先选择一行")

    # ==================== 表格列操作方法 ====================
    
    def add_column(self):
        """添加新列到表格末尾"""
        self.sync_to_model()
        self.matrix_table_manager.add_column()

    def insert_column(self):
        """在当前选中列之前插入新列"""
        selected_cols = self.matrix_table_widget.selectionModel().selectedColumns()
        if selected_cols:
            self.sync_to_model()
            self.matrix_table_manager.insert_column(selected_cols[0].column())
        else:
            QMessageBox.warning(self, "警告", "请先选择一列")

    def move_column(self, col):
        """移动指定列到新位置
        
        Args:
            col: 要移动的列索引
        """
        self.sync_to_model()
        self.matrix_table_manager.move_column(col)

    def copy_column(self, col):
        """复制指定列的数据
        
        Args:
            col: 要复制的列索引
        """
        copied_col_data = self.matrix_table_manager.copy_column(col)
        self.set_copied_col_data(copied_col_data)

    def paste_column(self, col):
        """将复制的列数据粘贴到指定位置
        
        Args:
            col: 粘贴位置的列索引
        """
        self.sync_to_model()
        self.matrix_table_manager.paste_column(col)
        self.copied_col_data = self.matrix_copied_col_data

    def remove_column(self):
        """删除选中的列"""
        selected_cols = self.matrix_table_widget.selectionModel().selectedColumns()
        if selected_cols:
            self.sync_to_model()
            self.matrix_table_manager.remove_column(selected_cols[0].column())
        else:
            QMessageBox.warning(self, "警告", "请先选择一列")
