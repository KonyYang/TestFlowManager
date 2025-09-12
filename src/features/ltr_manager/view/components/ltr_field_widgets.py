"""
LTR字段控件组件模块
提供LTR编辑器中使用的自定义控件
"""

from PyQt5.QtWidgets import QTextEdit, QComboBox, QTableWidgetItem
from PyQt5.QtCore import Qt


class LTRTextEdit(QTextEdit):
    """
    LTR多行文本编辑控件
    """

    def __init__(self, text="", max_height=100, parent=None):
        """
        初始化LTR多行文本编辑控件

        Args:
            text: 初始文本
            max_height: 最大高度
            parent: 父控件
        """
        super().__init__(parent)
        self.setText(text)
        self.setMaximumHeight(max_height)


class LTRComboBox(QComboBox):
    """
    LTR下拉选择控件
    """

    def __init__(self, options=None, current_text="", parent=None):
        """
        初始化LTR下拉选择控件

        Args:
            options: 选项列表
            current_text: 当前选中文本
            parent: 父控件
        """
        super().__init__(parent)
        if options:
            self.addItems(options)
        if current_text:
            index = self.findText(current_text, Qt.MatchFixedString)
            if index >= 0:
                self.setCurrentIndex(index)


class LTRTableWidgetItem(QTableWidgetItem):
    """
    LTR表格项控件
    """

    def __init__(self, text="", editable=False):
        """
        初始化LTR表格项控件

        Args:
            text: 项文本
            editable: 是否可编辑
        """
        super().__init__(text)
        if editable:
            self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)
        else:
            self.setFlags(Qt.ItemIsEnabled)
