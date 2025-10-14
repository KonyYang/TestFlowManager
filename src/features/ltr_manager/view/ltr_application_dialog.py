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
from src.features.ltr_manager.utils.field_config_loader import LTRFieldConfigLoader
from src.common.widgets import EnglishDateEdit, convert_to_english_format, MONTH_ABBREVIATIONS
from src.core.event_dispatcher import event_dispatcher

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

        # 从配置文件加载字段映射关系
        config_loader = LTRFieldConfigLoader()
        self._default_items_structure = config_loader.load_application_field_mapping()

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

        # 创建按钮 - 只保留确认和取消按钮
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_buttons(self, main_layout):
        """创建按钮 - 只保留确认和取消按钮"""
        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 只创建确认和取消按钮
        self.ok_button = QPushButton("确认")
        self.cancel_button = QPushButton("取消")

        # 连接信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # 添加按钮到布局
        button_layout.addStretch()
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

                if 'options' in item_data:
                    options = item_data['options']
                else:
                    # 为向后兼容，保留原有选项定义
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
                saved_data[key] = cell_widget.currentText()
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

    def accept(self):
        """重写accept方法，添加数据验证和处理"""
        # 收集表单数据
        form_data = self._collect_form_data()

        # 如果有控制器，调用控制器处理LTR申请
        if self.controller and hasattr(self.controller, 'apply_ltr_number'):
            try:
                result = self.controller.apply_ltr_number(form_data)

                if result.get("success"):
                    # 显示成功消息
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(self, "成功", f"LTR编号申请成功: {result.get('ltr_number')}")
                    # 调用父类方法关闭对话框
                    super().accept()
                else:
                    # 显示错误消息
                    from PyQt5.QtWidgets import QMessageBox
                    error_msg = result.get('error', '未知错误')
                    QMessageBox.critical(self, "错误", f"LTR编号申请失败: {error_msg}")

                    # 如果是需要重新输入的错误（如DL编号格式错误），保持对话框打开
                    if result.get('retry', False):
                        # 不调用super().accept()，保持对话框打开
                        return
                    else:
                        # 其他错误关闭对话框
                        self.reject()
            except Exception as e:
                import traceback
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"处理申请时发生异常: {str(e)}")
                self.reject()
        else:
            print("[DEBUG] No controller found, closing dialog directly")
            super().accept()
