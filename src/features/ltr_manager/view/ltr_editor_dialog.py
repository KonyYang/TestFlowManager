"""
LTR编辑对话框模块
提供一个对话框用于显示和编辑LTR信息
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel
from PyQt5.QtCore import Qt
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

        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"编辑DL编号: {self.dl_number}")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout()

        # 标题
        title_label = QLabel(f"DL编号: {self.dl_number}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 创建表格显示数据
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["字段", "当前值", "修改值"])
        self.data_table.setRowCount(len(self.original_data))

        # 设置表格属性
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止直接编辑
        self.data_table.setSelectionMode(QTableWidget.NoSelection)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.verticalHeader().setVisible(False)

        layout.addWidget(self.data_table)

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
        fields_mapping = {
            'sample_information': 'Description P/N',
            'tests_to_be_performed': 'Test Item',
            'applicable_specifications': 'Applicable Specifications',
            'test_type': 'Test Type',
            'requested_by': 'Requested by',
            'location': 'Location',
            'project_leader': 'Project Leader',
            'test_result': 'Test Result',
            'failed_item': 'Failed item',
            'sample_deposition': 'Sample deposition',
            'sub_contract': 'Sub-contract',
            'test_fee': 'Test Fee',
            'remarks_po': 'Remarks (PO)'
        }

        row = 0
        for key, original_value in self.original_data.items():
            # 字段名
            field_item = QTableWidgetItem(fields_mapping.get(key, key))
            field_item.setFlags(Qt.ItemIsEnabled)

            # 当前值
            current_item = QTableWidgetItem(str(original_value))
            current_item.setFlags(Qt.ItemIsEnabled)

            # 修改值（可编辑）
            modified_item = QTableWidgetItem(str(original_value))
            modified_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)

            self.data_table.setItem(row, 0, field_item)
            self.data_table.setItem(row, 1, current_item)
            self.data_table.setItem(row, 2, modified_item)

            row += 1

        self.data_table.resizeColumnsToContents()

    def _on_update(self):
        """处理更新按钮点击事件"""
        # 收集修改后的数据
        for row in range(self.data_table.rowCount()):
            field_item = self.data_table.item(row, 0)
            modified_item = self.data_table.item(row, 2)

            if field_item and modified_item:
                field_name = field_item.text()
                modified_value = modified_item.text()

                # 更新修改后的数据
                # 需要将显示的字段名映射回实际的键名
                for key, display_name in {
                    'sample_information': 'Description P/N',
                    'tests_to_be_performed': 'Test Item',
                    'applicable_specifications': 'Applicable Specifications',
                    'test_type': 'Test Type',
                    'requested_by': 'Requested by',
                    'location': 'Location',
                    'project_leader': 'Project Leader',
                    'test_result': 'Test Result',
                    'failed_item': 'Failed item',
                    'sample_deposition': 'Sample deposition',
                    'sub_contract': 'Sub-contract',
                    'test_fee': 'Test Fee',
                    'remarks_po': 'Remarks (PO)'
                }.items():
                    if display_name == field_name:
                        self.modified_data[key] = modified_value
                        break

        self.accept()

    def get_modified_data(self):
        """
        获取修改后的数据

        Returns:
            dict: 包含修改后数据的字典
        """
        return self.modified_data
