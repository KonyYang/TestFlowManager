"""
基本信息对话框基类模块
提供一个基类用于显示和编辑基于字段配置的信息
"""

import logging
import re
from typing import Dict, Any, List
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QWidget, QScrollArea, QLabel, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QDesktopWidget

from src.features.ltr_manager.utils.field_config_loader import LTRFieldConfigLoader
from src.common.widgets import EnglishDateEdit, convert_to_english_format, MONTH_ABBREVIATIONS
from src.core.window_utils import WindowUtils
from src.core.config_manager import config_manager

# Configure logging for this module
logger = logging.getLogger(__name__)


class BaseInfoDialog(QDialog):
    """BaseInfoDialog
    基本信息对话框基类
    用于显示和编辑基于字段配置的信息
    """

    def __init__(self, title: str, data: Dict[str, Any], parent=None):
        """
        初始化基本信息对话框基类

        Args:
            title: 对话框标题
            data: 包含数据的字典
            parent: 父窗口
        """
        super().__init__(parent)
        self.parent_window = parent
        self.data = data

        # 从配置文件加载字段映射关系
        config_loader = LTRFieldConfigLoader()
        self._default_items_structure = config_loader.load_application_field_mapping()

        self.table_items_data: List[Dict[str, Any]] = []
        self.date_fields: Dict[int, EnglishDateEdit] = {}  # 存储日期字段的引用

        self._setup_ui(title)
        self._populate_data()
        self._center_dialog()

    def _setup_ui(self, title: str):
        """设置用户界面"""
        self.setWindowTitle(title)
        # 设置更小的最小尺寸并根据DPI进行适配
        min_width, min_height = WindowUtils.get_scaled_window_size(1000, 1000)
        self.setMinimumSize(min_width, min_height)
        # 设置更小的初始尺寸并根据DPI进行适播
        init_width, init_height = WindowUtils.get_scaled_window_size(1000, 1200)
        self.resize(init_width, init_height)

        # 创建主布局
        main_layout = QVBoxLayout(self)

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
        # 设置"具体内容"列随着窗口大小调整而自动调整
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.info_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # 根据DPI调整最小宽度
        min_width = WindowUtils.get_scaled_size(600)  # 保持最小宽度为600像素
        self.info_table.setMinimumWidth(min_width)

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
        data = self.data
        logger.debug(f"开始填充数据到表格，数据: {data}")

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
                # 创建QComboBox实例
                combo_box = QComboBox()

                # 重写wheelEvent方法以禁用鼠标滚轮切换选项的功能
                def wheelEvent(event):
                    """
                    重写wheelEvent以禁用鼠标滚轮切换选项的功能

                    Args:
                        event: 鼠标滚轮事件
                    """
                    # 不调用父类的wheelEvent，从而阻止默认的滚轮行为
                    pass

                # 将自定义的wheelEvent方法赋值给combo_box的wheelEvent属性
                combo_box.wheelEvent = wheelEvent
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
                # 根据DPI调整最大高度
                # 仅对"Description P/N"字段应用4行显示，其他多行文本字段保持原来的一行显示
                if item_data['key'] == 'sample_information':  # "Description P/N"字段
                    max_height = WindowUtils.get_scaled_size(120)  # 4行大约需要120像素高度
                else:  # 其他多行文本字段保持原来的一行显示
                    max_height = WindowUtils.get_scaled_size(30)  # 保持原来的一行显示
                text_edit.setMaximumHeight(max_height)
                text_edit.setPlainText(item_data.get('value', ''))
                self.info_table.setCellWidget(row_index, 1, text_edit)
                # 设置行高为较小值
                self.info_table.setRowHeight(row_index, max_height + 10)
            else:
                value_item = QTableWidgetItem(item_data.get('value', ''))
                value_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                self.info_table.setItem(row_index, 1, value_item)

        # 行高自适应内容
        self.info_table.resizeRowsToContents()
        logger.debug("数据填充完成")

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
        logger.debug("开始收集表单数据")
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

        logger.debug(f"收集到的表单数据: {saved_data}")
        return saved_data

    def get_modified_data(self) -> dict:
        """
        获取用户修改后的数据

        Returns:
            包含修改后数据的字典
        """
        return self._collect_form_data()