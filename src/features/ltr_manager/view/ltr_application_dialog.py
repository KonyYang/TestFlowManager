"""
LTR申请单对话框模块
提供一个对话框用于显示和编辑LTR申请单信息
"""

import logging
import re
from typing import Dict, Any, List
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QWidget, QScrollArea, QLabel, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QDesktopWidget

from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
from src.features.ltr_manager.service.ltr_application_service import LTRApplicationService
from src.common.widgets import EnglishDateEdit, convert_to_english_format, MONTH_ABBREVIATIONS

# Configure logging for this module
logger = logging.getLogger(__name__)


class LTRApplicationDialog(QDialog):
    """LTRApplicationDialog
    LTR申请单对话框类
    用于显示和编辑LTR申请单信息
    """

    def __init__(self, application_data, parent=None, parent_controller=None):
        """
        初始化LTR申请单对话框

        Args:
            application_data: 包含申请单数据的字典
            parent: 父窗口
        """
        super().__init__(parent)
        self.parent_window = parent
        self.parent_controller = parent_controller
        self.application_data = application_data

        self.dl_number = application_data.get('dl_number', '')
        self.original_data = application_data.get('data', {})
        self.modified_data = self.original_data.copy()

        # 初始化数据模型
        self.data_model = LTRApplicationData.from_dict(self.original_data)

        # 初始化服务层和控制器
        self.service = LTRApplicationService()
        self.controller = parent_controller

        # 字段映射关系
        self._default_items_structure = [
            {'key': 'DL', 'label': 'DL', 'value': '', 'feedback': ''},
            {'key': 'project_type', 'label': 'Project Type', 'value': '', 'feedback': '', 'editor_type': 'dropdown'},
            {'key': 'sample_information', 'label': 'Description P/N', 'value': '', 'feedback': '',
             'editor_type': 'multiline'},
            {'key': 'tests_to_be_performed', 'label': 'Test Item', 'value': '', 'feedback': '',
             'editor_type': 'multiline'},
            {'key': 'applicable_specifications', 'label': 'Applicable Specifications', 'value': '', 'feedback': '',
             'editor_type': 'multiline'},
            {'key': 'test_type', 'label': 'Test Type', 'value': '', 'feedback': '', 'editor_type': 'dropdown'},
            {'key': 'requested_by', 'label': 'Requested by', 'value': '', 'feedback': ''},
            {'key': 'location', 'label': 'Location', 'value': '', 'feedback': ''},
            {'key': 'project_leader', 'label': 'Project Leader', 'value': '', 'feedback': ''},
            {'key': 'test_result', 'label': 'Test Result', 'value': '', 'feedback': '', 'editor_type': 'dropdown'},
            {'key': 'failed_item', 'label': 'Failed item', 'value': '', 'feedback': ''},
            {'key': 'sample_deposition', 'label': 'Sample deposition', 'value': '', 'feedback': ''},
            {'key': 'sub_contract', 'label': 'Sub-contract', 'value': '', 'feedback': '', 'editor_type': 'dropdown'},
            {'key': 'test_fee', 'label': 'Test Fee', 'value': '', 'feedback': ''},
            {'key': 'remarks_po', 'label': 'Remarks (PO)', 'value': '', 'feedback': ''},
            {'key': 'phone', 'label': 'Phone', 'value': '', 'feedback': ''},
            {'key': 'email_requestor', 'label': 'E-mail of Requestor', 'value': '', 'feedback': ''},
            {'key': 'product_description', 'label': 'Product Description', 'value': '', 'feedback': '',
             'editor_type': 'multiline'},
            {'key': 'lab_performing_the_tests', 'label': 'Lab Performing the Tests', 'value': '', 'feedback': '',
             'editor_type': 'dropdown'},
            {'key': 'condition_of_samples_when_received', 'label': 'Condition of Samples when Received', 'value': '',
             'feedback': '', 'editor_type': 'dropdown'},

            # ====== 日期字段 ======
            {'key': 'date_lab_received_samples', 'label': 'Date Lab Received Samples', 'value': '', 'feedback': '',
             'editor_type': 'calendar'},
            {'key': 'estimated_completion_date', 'label': 'Estimated Completion Date', 'value': '', 'feedback': '',
             'editor_type': 'calendar'},
            {'key': 'start_test_date', 'label': 'Start Test Date', 'value': '', 'feedback': '',
             'editor_type': 'calendar'},
            {'key': 'finish_test_date', 'label': 'Finish Test Date', 'value': '', 'feedback': '',
             'editor_type': 'calendar'},
            {'key': 'report_date', 'label': 'Report Date', 'value': '', 'feedback': '',
             'editor_type': 'calendar'},
        ]

        self.table_items_data: List[Dict[str, Any]] = []
        self.date_fields: Dict[int, EnglishDateEdit] = {}  # 存储日期字段的引用

        self._setup_ui()
        self._populate_data()
        self._center_dialog()

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"LTR申请单: {self.dl_number}" if self.dl_number else "新LTR申请单")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 版本标签
        self.version_label = QLabel("Application Version: N/A")
        main_layout.addWidget(self.version_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建表格用于显示数据
        self.info_table = QTableWidget(0, 2)
        self.info_table.setObjectName("info_table")
        self.info_table.setHorizontalHeaderLabels(["信息项", "具体内容"])

        # 设置列宽调整策略
        header = self.info_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.info_table.setColumnWidth(1, 300)
        self.info_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.info_table.setMinimumWidth(600)

        # 美化滚动条
        self.info_table.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                height: 15px;
                background: #F0F0F0;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #A0A0A0;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #707070;
            }
        """)

        scroll_area.setWidget(self.info_table)
        main_layout.addWidget(scroll_area)

        # 创建按钮
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_buttons(self, main_layout):
        """创建按钮"""
        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 创建按钮
        self.open_ltr_button = QPushButton("查看LTR")
        self.apply_ltr_button = QPushButton("申请LTR")
        self.update_ltr_button = QPushButton("更新LTR")
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")

        # 连接信号
        self.open_ltr_button.clicked.connect(self._open_ltr)
        self.apply_ltr_button.clicked.connect(self._apply_ltr)
        self.update_ltr_button.clicked.connect(self._update_ltr)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # 添加按钮到布局
        button_layout.addStretch()
        button_layout.addWidget(self.open_ltr_button)
        button_layout.addWidget(self.apply_ltr_button)
        button_layout.addWidget(self.update_ltr_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def _populate_data(self):
        """填充数据到表格"""
        # 获取数据
        data = self.data_model.to_dict()

        # 设置版本信息
        version = data.get("version", "N/A")
        self.version_label.setText(f"Application Version: {version}")

        # 处理特殊字段格式
        for key in ['sample_information', 'tests_to_be_performed', 'applicable_specifications']:
            if key in data:
                item = next((item for item in self._default_items_structure if item['key'] == key), None)
                if item and item.get('editor_type') == 'multiline':
                    # 仅在需要显示到multiline编辑器时才换行，不影响原始数据
                    data[key] = data[key].replace(';', '\n')

        # 构造table_items_data
        self.table_items_data = []
        for default_item in self._default_items_structure:
            item = default_item.copy()
            item_key = item['key']

            value = data.get(item_key, default_item.get('value', ''))

            # 对于日期字段，转换为英文格式
            if item.get('editor_type') == 'calendar':
                value = convert_to_english_format(value)

            item['value'] = value
            self.table_items_data.append(item)

        # 设置表格行数
        self.info_table.setRowCount(len(self.table_items_data))

        # 填充每一行内容
        for row_index, item_data in enumerate(self.table_items_data):
            label_item = QTableWidgetItem(item_data.get('label', ''))
            label_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.info_table.setItem(row_index, 0, label_item)

            # 特殊处理日期字段
            if item_data.get('editor_type') == 'calendar':
                date_edit = EnglishDateEdit()

                date_value = item_data['value']
                if date_value:
                    try:
                        match = re.match(r"(\d{1,2})\s+([a-zA-Z]{3})\s+(\d{4})", date_value, re.IGNORECASE)
                        if match:
                            day, month_abbr, year = match.groups()
                            month_num = next((num for num, abbr in MONTH_ABBREVIATIONS.items()
                                              if abbr.lower() == month_abbr.lower()), None)

                            if month_num:
                                date_edit.setDate(QDate(int(year), month_num, int(day)))
                        else:
                            date_edit.setDate(QDate.currentDate())
                    except Exception as e:
                        logger.error(f"日期解析错误: {e}")
                        date_edit.setDate(QDate.currentDate())
                else:
                    date_edit.setDate(QDate.currentDate())

                self.date_fields[row_index] = date_edit
                self.info_table.setCellWidget(row_index, 1, date_edit)

            # 创建控件
            elif item_data.get('editor_type') == 'dropdown':
                combo_box = QComboBox()

                if item_data['key'] == 'test_result':
                    options = ["In progress", "OK", "Ref", "NG", "In-waiting"]
                elif item_data['key'] == 'test_type':
                    options = ["Partial Qualification", "Qualification", "Failure Analysis", "Other", "Analysis",
                               "Chemical", "Electrical", "Environmental", "Whisker", "Mechanical", "ORT",
                               "Solderability"]
                elif item_data['key'] == 'project_type':
                    options = ["NPD", "PEX", "OPS", "CR", "ADM"]
                elif item_data['key'] == 'sub_contract':
                    options = ["Yes", "No"]
                elif item_data['key'] == 'lab_performing_the_tests':
                    options = ["Dongguan", "Valley Green"]
                elif item_data['key'] == 'condition_of_samples_when_received':
                    options = ["Acceptable", "Not Acceptable"]
                else:
                    logger.warning(f"未知的dropdown字段: {item_data['key']}")
                    continue

                combo_box.addItems(options)

                # 获取当前字段值
                current_value = item_data.get('value', '')

                # 如果是project_type，则进行映射转换
                if item_data['key'] == 'project_type':
                    mapped_value = ""
                    if current_value == "New Product Development":
                        mapped_value = "NPD"
                    elif current_value == "Product Extension":
                        mapped_value = "PEX"
                    elif current_value == "Operational Support":
                        mapped_value = "OPS"
                    elif current_value == "Cost Reduction":
                        mapped_value = "CR"
                    elif current_value in ["Lab Activities (Lab Use Only)", "Innovation"]:
                        mapped_value = "ADM"
                    current_value = mapped_value  # 替换为映射后的值用于查找

                # 如果是test_type，则进行映射转换
                elif item_data['key'] == 'test_type':
                    mapped_value = ""
                    if current_value == "Product/Process Development":
                        mapped_value = "Partial Qualification"
                    elif current_value == "Product/Process Qualification":
                        mapped_value = "Qualification"
                    elif current_value == "Lab/Failure Analysis":
                        mapped_value = "Failure Analysis"
                    elif current_value == "Customer Specific Testing":
                        mapped_value = "Other"
                    current_value = mapped_value  # 替换为映射后的值用于查找

                # 设置下拉框选中项
                index = combo_box.findText(current_value, Qt.MatchFixedString)
                combo_box.setCurrentIndex(index if index >= 0 else 0)

                self.info_table.setCellWidget(row_index, 1, combo_box)

            elif item_data.get('editor_type') == 'multiline':
                text_edit = QTextEdit()
                text_edit.setMaximumHeight(80)
                text_edit.setPlainText(item_data.get('value', ''))
                self.info_table.setCellWidget(row_index, 1, text_edit)
                self.info_table.setRowHeight(row_index, 80)
            else:
                value_item = QTableWidgetItem(item_data.get('value', ''))
                value_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                self.info_table.setItem(row_index, 1, value_item)

        # 行高自适应内容
        self.info_table.resizeRowsToContents()

    def _center_dialog(self):
        """居中对话框"""
        if self.parent_window:
            parent_center = self.parent_window.geometry().center()
            self.move(parent_center.x() - self.width() // 2,
                     parent_center.y() - self.height() // 2)
        else:
            # 如果没有父窗口，在屏幕中央显示
            qr = self.frameGeometry()
            cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())

    def _collect_form_data(self) -> Dict[str, Any]:
        """收集表单数据"""
        saved_data = {}
        for row_index in range(self.info_table.rowCount()):
            key = self.table_items_data[row_index]['key']
            cell_widget = self.info_table.cellWidget(row_index, 1)

            # 处理各种控件类型
            if isinstance(cell_widget, QComboBox):
                current_text = cell_widget.currentText()
                # 对project_type做逆向映射
                if key == 'project_type':
                    reverse_map = {
                        "NPD": "New Product Development",
                        "PEX": "Product Extension",
                        "OPS": "Operational Support",
                        "CR": "Cost Reduction",
                        "ADM": "Lab Activities (Lab Use Only)"
                    }
                    saved_data[key] = reverse_map.get(current_text, current_text)

                # 对test_type做逆向映射
                elif key == 'test_type':
                    reverse_map = {
                        "Partial Qualification": "Product/Process Development",
                        "Qualification": "Product/Process Qualification",
                        "Failure Analysis": "Lab/Failure Analysis",
                        "Other": "Customer Specific Testing",
                        "Analysis": "Customer Specific Testing",
                        "Chemical": "Customer Specific Testing",
                        "Electrical": "Customer Specific Testing",
                        "Environmental": "Customer Specific Testing",
                        "Whisker": "Customer Specific Testing",
                        "Mechanical": "Customer Specific Testing",
                        "ORT": "Customer Specific Testing",
                        "Solderability": "Customer Specific Testing",
                    }
                    saved_data[key] = reverse_map.get(current_text, current_text)

                else:
                    saved_data[key] = current_text
            elif isinstance(cell_widget, EnglishDateEdit):
                saved_data[key] = cell_widget.text()
            elif isinstance(cell_widget, QTextEdit):
                saved_data[key] = cell_widget.toPlainText()
            else:
                item = self.info_table.item(row_index, 1)
                saved_data[key] = item.text() if item else ''

        return saved_data

    def get_modified_data(self) -> dict:
        """
        获取用户修改后的数据

        Returns:
            包含修改后数据的字典
        """
        return self._collect_form_data()

    def _open_ltr(self):
        """查看LTR"""
        # 后续实现
        pass

    def _apply_ltr(self):
        """申请LTR"""
        if not self.controller and self.parent_window:
            # 如果有父窗口且父窗口有controller属性，则使用父窗口的controller
            self.controller = getattr(self.parent_window, 'controller', None)

        # 如果仍然没有controller，则在方法内部创建或处理
        if not self.controller:
            # 延迟导入以避免循环依赖
            from src.features.ltr_manager.controller.ltr_application_controller import LTRApplicationController
            self.controller = LTRApplicationController(self.parent_window)

        # 后续实现

    def _update_ltr(self):
        """更新LTR"""
        if not self.controller and self.parent_window:
            # 如果有父窗口且父窗口有controller属性，则使用父窗口的controller
            self.controller = getattr(self.parent_window, 'controller', None)

        # 如果仍然没有controller，则在方法内部创建或处理
        if not self.controller:
            # 延迟导入以避免循环依赖
            from src.features.ltr_manager.controller.ltr_application_controller import LTRApplicationController
            self.controller = LTRApplicationController(self.parent_window)

        # 后续实现

    def accept(self):
        """重写accept方法，添加数据验证"""
        # 这里可以添加数据验证逻辑
        super().accept()
