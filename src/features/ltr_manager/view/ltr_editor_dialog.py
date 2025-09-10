"""
LTR编辑对话框模块
提供一个对话框用于显示和编辑LTR信息
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QHeaderView,
                             QTextEdit, QWidget, QScrollArea, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDesktopWidget
from src.core.logger import logger


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
        self.dl_data = dl_data
        self.dl_number = dl_data.get('dl_number', '')
        self.original_data = dl_data.get('data', {})  # E到Q列的数据
        self.modified_data = self.original_data.copy()

        # 字段映射关系，定义字段类型和下拉选项
        self.field_mapping = [
            {'key': 'project_type', 'label': 'Project Type', 'editor_type': 'dropdown',
             'options': ["NPD", "PEX", "OPS", "CR", "ADM"]},
            {'key': 'sample_information', 'label': 'Description P/N', 'editor_type': 'multiline'},
            {'key': 'tests_to_be_performed', 'label': 'Test Item', 'editor_type': 'multiline'},
            {'key': 'test_type', 'label': 'Test Type', 'editor_type': 'dropdown',
             'options': ["Partial Qualification", "Qualification", "Failure Analysis", "Other", "Analysis",
                         "Chemical", "Electrical", "Environmental", "Whisker", "Mechanical", "ORT", "Solderability"]},
            {'key': 'requested_by', 'label': 'Requested by', 'editor_type': 'text'},
            {'key': 'location', 'label': 'Location', 'editor_type': 'text'},
            {'key': 'project_leader', 'label': 'Project Leader', 'editor_type': 'text'},
            {'key': 'test_result', 'label': 'Test Result', 'editor_type': 'dropdown',
             'options': ["In progress", "OK", "Ref", "NG", "In-waiting"]},
            {'key': 'failed_item', 'label': 'Failed item', 'editor_type': 'text'},
            {'key': 'sample_deposition', 'label': 'Sample deposition', 'editor_type': 'text'},
            {'key': 'sub_contract', 'label': 'Sub-contract', 'editor_type': 'dropdown', 'options': ["Yes", "No"]},
            {'key': 'test_fee', 'label': 'Test Fee', 'editor_type': 'text'},
            {'key': 'remarks_po', 'label': 'Remarks (PO)', 'editor_type': 'text'}
        ]

        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"编辑DL编号: {self.dl_number}")
        self.setModal(True)

        # 获取屏幕尺寸并设置窗口大小为屏幕的60%
        desktop = QDesktopWidget().availableGeometry()
        width, height = int(desktop.width() * 0.6), int(desktop.height() * 0.6)
        self.setGeometry(0, 0, width, height)
        self.move((desktop.width() - width) // 2, (desktop.height() - height) // 2)

        layout = QVBoxLayout()

        # 标题
        title_label = QLabel(f"DL编号: {self.dl_number}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

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

    def _populate_data(self):
        """填充数据到表格"""
        self.data_table.setRowCount(len(self.field_mapping))

        row = 0
        for field_info in self.field_mapping:
            key = field_info['key']
            label = field_info['label']
            editor_type = field_info['editor_type']

            # 获取原始值
            original_value = self.original_data.get(key, '')

            # 字段名
            field_item = QTableWidgetItem(label)
            field_item.setFlags(Qt.ItemIsEnabled)

            # 当前值
            current_item = QTableWidgetItem(str(original_value))
            current_item.setFlags(Qt.ItemIsEnabled)

            # 修改值（根据字段类型创建不同的编辑控件）
            self.data_table.setItem(row, 0, field_item)
            self.data_table.setItem(row, 1, current_item)

            if editor_type == 'multiline':
                # 对于多行文本，使用QTextEdit
                text_edit = QTextEdit()
                text_edit.setText(str(original_value))
                text_edit.setMaximumHeight(100)
                self.data_table.setCellWidget(row, 2, text_edit)
            elif editor_type == 'dropdown':
                # 对于下拉框字段
                combo_box = QComboBox()
                combo_box.addItems(field_info['options'])
                index = combo_box.findText(str(original_value), Qt.MatchFixedString)
                if index >= 0:
                    combo_box.setCurrentIndex(index)
                self.data_table.setCellWidget(row, 2, combo_box)
            else:
                # 默认使用普通文本编辑
                modified_item = QTableWidgetItem(str(original_value))
                modified_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)
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
                for field_info in self.field_mapping:
                    if field_info['label'] == field_label:
                        field_key = field_info['key']
                        break

                if field_key:
                    # 获取修改后的值
                    cell_widget = self.data_table.cellWidget(row, 2)
                    if cell_widget:
                        # 对于特殊控件，需要特殊处理
                        if isinstance(cell_widget, QTextEdit):
                            modified_value = cell_widget.toPlainText()
                        elif isinstance(cell_widget, QComboBox):
                            modified_value = cell_widget.currentText()
                        else:
                            modified_value = cell_widget.text()
                    else:
                        # 普通文本项
                        modified_item = self.data_table.item(row, 2)
                        modified_value = modified_item.text() if modified_item else ""

                    self.modified_data[field_key] = modified_value

        self.accept()

    def get_modified_data(self):
        """
        获取修改后的数据

        Returns:
            dict: 包含修改后数据的字典
        """
        return self.modified_data
