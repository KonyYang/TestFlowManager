"""
日期编辑控件模块
提供日期选择和编辑功能
"""

import re
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QDateEdit, QPushButton, QCalendarWidget
from PyQt5.QtCore import QDate, pyqtSignal, QLocale, Qt
from src.core.logger import logger

# 月份名称英文缩写映射
MONTH_ABBREVIATIONS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}


class EnglishDateEdit(QDateEdit):
    """自定义日期编辑控件，强制显示英文月份缩写"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置使用英文的本地化
        self.setLocale(QLocale(QLocale.English))
        self.setDisplayFormat("dd MMM yyyy")
        self.setCalendarPopup(True)

        # 创建自定义日历控件
        cal = QCalendarWidget()
        cal.setGridVisible(True)
        cal.setFirstDayOfWeek(Qt.Monday)
        cal.setLocale(QLocale(QLocale.English))  # 确保日历也显示英文
        self.setCalendarWidget(cal)


def convert_to_english_format(date_str):
    """将各种日期格式转换为标准的 DD Mon YYYY 英文格式"""
    match = re.match(r"(\d{1,2})\s+([a-zA-Z]{3})\s+(\d{4})", date_str, re.IGNORECASE)
    if match:
        day, month_abbr, year = match.groups()
        return f"{day.zfill(2)} {month_abbr.capitalize()} {year}"

    match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
    if match:
        month, day, year = match.groups()
        return f"{day.zfill(2)} {MONTH_ABBREVIATIONS.get(int(month), '')} {year}"

    match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_str)
    if match:
        year, month, day = match.groups()
        return f"{day.zfill(2)} {MONTH_ABBREVIATIONS.get(int(month), '')} {year}"

    return ""


class DateEdit(QWidget):
    """
    日期编辑控件
    提供日期选择和编辑功能
    """

    # 日期改变信号
    dateChanged = pyqtSignal(QDate)

    def __init__(self, parent=None):
        """
        初始化日期编辑控件

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 日期选择器
        self.date_edit = EnglishDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self._on_date_changed)

        # 今天按钮
        self.today_button = QPushButton("今天")
        self.today_button.clicked.connect(self._set_today)

        layout.addWidget(self.date_edit)
        layout.addWidget(self.today_button)

        self.setLayout(layout)

    def _on_date_changed(self, date: QDate) -> None:
        """日期改变时的处理"""
        self.dateChanged.emit(date)

    def _set_today(self) -> None:
        """设置为今天"""
        today = QDate.currentDate()
        self.date_edit.setDate(today)

    def set_date(self, date: QDate) -> None:
        """
        设置日期

        Args:
            date: 日期
        """
        self.date_edit.setDate(date)

    def get_date(self) -> QDate:
        """
        获取日期

        Returns:
            当前选择的日期
        """
        return self.date_edit.date()

    def set_minimum_date(self, date: QDate) -> None:
        """
        设置最小日期

        Args:
            date: 最小日期
        """
        self.date_edit.setMinimumDate(date)

    def set_maximum_date(self, date: QDate) -> None:
        """
        设置最大日期

        Args:
            date: 最大日期
        """
        self.date_edit.setMaximumDate(date)

    def set_date_range(self, min_date: QDate, max_date: QDate) -> None:
        """
        设置日期范围

        Args:
            min_date: 最小日期
            max_date: 最大日期
        """
        self.date_edit.setDateRange(min_date, max_date)


class DateTimeEditWidget(QWidget):
    """
    日期时间编辑控件
    提供日期和时间选择功能
    """

    # 日期时间改变信号
    dateTimeChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        初始化日期时间编辑控件

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        # TODO: 实现日期时间编辑控件
        pass
