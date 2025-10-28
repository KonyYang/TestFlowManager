"""
LTR编辑对话框模块
提供一个对话框用于显示和编辑LTR信息
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QWidget, QScrollArea, QDesktopWidget)
from PyQt5.QtCore import Qt
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_editor_data import LTREditorData
from src.features.ltr_manager.view.components.ltr_field_widgets import LTRTextEdit, LTRComboBox, LTRTableWidgetItem
from src.core.window_utils import WindowUtils  # 导入窗口工具类


class LTREditorDialog(QDialog):
    """
    LTR编辑对话框类
    用于显示和编辑指定DL编号的LTR信息（E到Q列）
    """

    def __init__(self, dl_data, parent=None):
        """
        初始化LTR编辑对话框

        Args:
            dl_data: 包含DL编号和相关数据的字典
            parent: 父窗口
        """
        super().__init__(parent)
        self.parent_window = parent
        self.dl_data = dl_data
        self.data_model = LTREditorData()

        self.dl_number = dl_data.get('dl_number', '')
        # 转换数据格式
        self._convert_data_format(dl_data.get('data', {}))
        self.modified_data = self.original_data.copy()

        # 初始化数据模型
        self.data_model.set_dl_number(self.dl_number)
        self.data_model.set_original_data(self.original_data)

        # 获取字段映射关系
        self.field_mapping = self.data_model.get_field_mapping()
        
        # 检查字段映射是否为空
        if not self.field_mapping:
            logger.warning("字段映射为空，对话框可能无法正常显示")

        self._setup_ui()
        self._populate_data()
        print("[DEBUG] Data population completed")

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"编辑 LTR 信息: {self.dl_number}")
        self.setModal(True)

        # 获取屏幕尺寸并设置窗口大小为屏幕的40%，并根据DPI进行适配
        width, height = WindowUtils.get_scaled_screen_geometry(0.4)
        self.resize(width, height)
        # 居中显示
        desktop = QDesktopWidget().availableGeometry()
        self.move((desktop.width() - width) // 2, (desktop.height() - height) // 2)

        layout = QVBoxLayout()

        # 创建滚动区域以容纳表格
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 创建表格显示数据
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["字段", "当前值", "修改值"])

        # 设置表格属性
        self.data_table.setSelectionMode(QTableWidget.NoSelection)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.verticalHeader().setVisible(False)

        # 设置列宽策略
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 字段名列自适应
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 当前值列拉伸
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 修改值列拉伸

        scroll_layout.addWidget(self.data_table)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self._on_update)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _convert_data_format(self, raw_data):
        """转换原始数据格式"""
        column_to_field_map = {
            'E': 'project_type', 'F': 'sample_information', 'G': 'tests_to_be_performed',
            'H': 'test_type', 'I': 'requested_by', 'J': 'location',
            'K': 'project_leader', 'L': 'test_result', 'M': 'failed_item',
            'N': 'sample_deposition', 'O': 'sub_contract', 'P': 'test_fee', 'Q': 'remarks_po'
        }

        self.original_data = {}
        for column, value in raw_data.items():
            field_name = column_to_field_map.get(column)
            if field_name:
                self.original_data[field_name] = value

    def _populate_data(self):
        """填充数据到表格"""
        # 检查字段映射是否为空
        if not self.field_mapping:
            logger.warning("字段映射为空，无法填充数据到表格")
            return
            
        self.data_table.setRowCount(len(self.field_mapping))

        row = 0
        for field_info in self.field_mapping:
            key = field_info['key']
            label = field_info['label']
            editor_type = field_info['editor_type']
            # 获取原始值
            original_value = self.original_data.get(key, '')
            if original_value is None:
                original_value = ''

            # 字段名
            field_item = LTRTableWidgetItem(label, editable=False)

            # 当前值
            display_value = str(original_value) if original_value is not None else ""
            current_item = LTRTableWidgetItem(display_value, editable=False)

            # 修改值（根据字段类型创建不同的编辑控件）
            self.data_table.setItem(row, 0, field_item)
            self.data_table.setItem(row, 1, current_item)

            if editor_type == 'multiline':
                # 对于多行文本，使用LTRTextEdit，设置为单行高度
                text_edit = LTRTextEdit(str(original_value))
                self.data_table.setCellWidget(row, 2, text_edit)
            elif editor_type == 'dropdown':
                # 对于下拉框字段，使用LTRComboBox
                combo_box = LTRComboBox(field_info['options'], str(original_value))
                self.data_table.setCellWidget(row, 2, combo_box)
            else:
                # 默认使用普通文本编辑
                modified_item = LTRTableWidgetItem(str(original_value), editable=True)
                self.data_table.setItem(row, 2, modified_item)

            row += 1

        self.data_table.resizeRowsToContents()

    def _on_update(self):
        """处理更新按钮点击事件"""
        # 收集修改后的数据
        for row in range(self.data_table.rowCount()):
            field_item = self.data_table.item(row, 0)

            if field_item:
                field_label = field_item.text()

                # 查找字段键名
                field_key = None
                field_info = self.data_model.get_field_by_label(field_label)
                if field_info:
                    field_key = field_info['key']

                if field_key:
                    # 获取修改后的值
                    cell_widget = self.data_table.cellWidget(row, 2)
                    if cell_widget:
                        # 对于特殊控件，需要特殊处理
                        if isinstance(cell_widget, LTRTextEdit):
                            modified_value = cell_widget.toPlainText()
                        elif isinstance(cell_widget, LTRComboBox):
                            modified_value = cell_widget.currentText()
                        else:
                            modified_value = cell_widget.text()
                    else:
                        # 普通文本项
                        modified_item = self.data_table.item(row, 2)
                        modified_value = modified_item.text() if modified_item else ""
                        if modified_value == "None":
                            modified_value = ""
                    self.modified_data[field_key] = modified_value

        # 更新数据模型中的修改数据
        self.data_model.set_modified_data(self.modified_data)

        # 调用父控制器执行更新操作
        from src.features.ltr_manager.controller.ltr_editor_controller import LTREditorController
        from src.features.ltr_manager.controller.ltr_viewer_controller import LTRViewerController

        # 创建LTR控制器和服务实例（在实际应用中，这些应该通过依赖注入传递）
        ltr_controller = LTRViewerController()
        ltr_editor_controller = LTREditorController(ltr_controller.data_model, ltr_controller.service)

        # 执行更新操作
        success = ltr_editor_controller.update_ltr_data(self.dl_number, self.modified_data, self.parent_window)

        if success:
            # 更新成功，刷新"当前值"列
            self._refresh_current_values()
            # 更新原始数据为修改后的数据
            self.original_data = self.modified_data.copy()
            self.data_model.set_original_data(self.original_data)

    def _refresh_current_values(self):
        """刷新当前值列"""
        for row in range(self.data_table.rowCount()):
            field_item = self.data_table.item(row, 0)
            if field_item:
                field_label = field_item.text()

                # 查找字段键名
                field_key = None
                field_info = self.data_model.get_field_by_label(field_label)
                if field_info:
                    field_key = field_info['key']

                if field_key:
                    # 更新当前值
                    current_value = self.modified_data.get(field_key, '')
                    current_item = self.data_table.item(row, 1)
                    if current_item:
                        current_item.setText(str(current_value))

    def get_modified_data(self):
        """
        获取修改后的数据

        Returns:
            dict: 包含修改后数据的字典
        """
        return self.modified_data