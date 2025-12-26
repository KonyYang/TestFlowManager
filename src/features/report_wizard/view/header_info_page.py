"""
页眉信息页面视图
实现向导中页眉信息输入页面的UI组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
    QLabel, QDateEdit, QGroupBox, QFrame
)
from PyQt5.QtCore import QDate
from src.features.report_wizard.model.header_data import HeaderData


class HeaderInfoPage(QFrame):
    """
    页眉信息页面视图组件
    提供报告页眉信息的输入界面
    """
    
    def __init__(self, parent=None):
        """初始化页眉信息页面"""
        super().__init__(parent)
        self.header_data = HeaderData()
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 页面标题
        title_label = QLabel("页眉信息")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 创建表单布局
        form_group = QGroupBox("报告页眉信息")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # 报告编号输入
        self.report_no_edit = QLineEdit()
        self.report_no_edit.setPlaceholderText("请输入报告编号")
        form_layout.addRow("报告编号:", self.report_no_edit)
        
        # 版本号输入
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("例如: Rev.A")
        self.version_edit.setText("Rev.A")  # 默认值
        form_layout.addRow("版本号:", self.version_edit)
        

        
        # 测试者输入
        self.tester_edit = QLineEdit()
        self.tester_edit.setPlaceholderText("请输入测试者姓名")
        form_layout.addRow("测试者:", self.tester_edit)
        
        # 报告标题输入
        self.report_title_edit = QLineEdit()
        self.report_title_edit.setPlaceholderText("请输入报告标题")
        form_layout.addRow("报告标题:", self.report_title_edit)
        
        # 请求者输入
        self.requested_by_edit = QLineEdit()
        self.requested_by_edit.setPlaceholderText("请输入请求者姓名")
        form_layout.addRow("请求者:", self.requested_by_edit)
        
        # 测试开始日期
        self.test_start_date = QDateEdit()
        self.test_start_date.setDate(QDate.currentDate())
        self.test_start_date.setCalendarPopup(True)
        form_layout.addRow("测试开始日期:", self.test_start_date)
        
        # 测试结束日期
        self.test_end_date = QDateEdit()
        self.test_end_date.setDate(QDate.currentDate())
        self.test_end_date.setCalendarPopup(True)
        form_layout.addRow("测试结束日期:", self.test_end_date)
        
        # 报告完成日期
        self.report_completion_date = QDateEdit()
        self.report_completion_date.setDate(QDate.currentDate())
        self.report_completion_date.setCalendarPopup(True)
        form_layout.addRow("报告完成日期:", self.report_completion_date)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        self.setLayout(layout)
    
    def get_header_data(self) -> HeaderData:
        """
        获取页面中输入的页眉数据
        
        Returns:
            HeaderData: 包含页眉信息的数据对象
        """
        # 格式化测试周期为开始日期-结束日期格式 (使用英文月份缩写)
        start_date_qdate = self.test_start_date.date()
        end_date_qdate = self.test_end_date.date()
        
        # 手动构建英文月份格式，避免本地化问题
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        start_day = start_date_qdate.day()
        start_month = start_date_qdate.month()
        start_year = start_date_qdate.year()
        start_date = f"{start_day:02d}/{months[start_month]}/{start_year}"
        
        end_day = end_date_qdate.day()
        end_month = end_date_qdate.month()
        end_year = end_date_qdate.year()
        end_date = f"{end_day:02d}/{months[end_month]}/{end_year}"
        
        test_period = f"{start_date}-{end_date}"
        
        # 格式化完成日期
        completion_date_qdate = self.report_completion_date.date()
        completion_day = completion_date_qdate.day()
        completion_month = completion_date_qdate.month()
        completion_year = completion_date_qdate.year()
        completion_date = f"{completion_day:02d}/{months[completion_month]}/{completion_year}"
        
        self.header_data = HeaderData(
            report_no=self.report_no_edit.text().strip(),
            version=self.version_edit.text().strip(),
            tester=self.tester_edit.text().strip(),
            report_title=self.report_title_edit.text().strip(),
            requested_by=self.requested_by_edit.text().strip(),
            test_period=test_period,
            completion_date=completion_date
        )
        return self.header_data
    
    def set_header_data(self, header_data: HeaderData):
        """
        设置页面中的页眉数据
        
        Args:
            header_data: 要设置的页眉数据对象
        """
        self.report_no_edit.setText(header_data.report_no)
        self.version_edit.setText(header_data.version)
        

        
        self.tester_edit.setText(header_data.tester)
        self.report_title_edit.setText(header_data.report_title)
        self.requested_by_edit.setText(header_data.requested_by)
        
        # 解析测试周期字符串并设置到开始和结束日期编辑器
        if header_data.test_period:
            try:
                # 测试周期格式为 "DD/MMM/YYYY-DD/MMM/YYYY"
                if '-' in header_data.test_period:
                    dates = header_data.test_period.split('-')
                    if len(dates) >= 2:
                        start_date_str = dates[0].strip()
                        end_date_str = dates[1].strip()
                        
                        # 解析开始日期
                        start_date = QDate.fromString(start_date_str, "dd/MMM/yyyy")
                        if not start_date.isValid():
                            # 尝试其他格式
                            formats = ["dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                            for fmt in formats:
                                start_date = QDate.fromString(start_date_str, fmt)
                                if start_date.isValid():
                                    break
                        
                        # 解析结束日期
                        end_date = QDate.fromString(end_date_str, "dd/MMM/yyyy")
                        if not end_date.isValid():
                            # 尝试其他格式
                            formats = ["dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                            for fmt in formats:
                                end_date = QDate.fromString(end_date_str, fmt)
                                if end_date.isValid():
                                    break
                        
                        if start_date.isValid():
                            self.test_start_date.setDate(start_date)
                        if end_date.isValid():
                            self.test_end_date.setDate(end_date)
            except Exception as e:
                print(f"解析测试周期时出错: {e}")
                # 如果解析失败，使用当前日期
                self.test_start_date.setDate(QDate.currentDate())
                self.test_end_date.setDate(QDate.currentDate())
        else:
            # 如果没有测试周期，默认使用当前日期
            self.test_start_date.setDate(QDate.currentDate())
            self.test_end_date.setDate(QDate.currentDate())
        
        # 设置完成日期
        if header_data.completion_date:
            try:
                # 尝试解析完成日期字符串并设置到日期编辑器
                completion_date = QDate.fromString(header_data.completion_date, "dd/MMM/yyyy")
                if not completion_date.isValid():
                    # 如果格式不匹配，尝试其他格式
                    formats = ["dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                    for fmt in formats:
                        completion_date = QDate.fromString(header_data.completion_date, fmt)
                        if completion_date.isValid():
                            break
                
                if completion_date.isValid():
                    self.report_completion_date.setDate(completion_date)
                else:
                    self.report_completion_date.setDate(QDate.currentDate())
            except:
                self.report_completion_date.setDate(QDate.currentDate())
        else:
            self.report_completion_date.setDate(QDate.currentDate())
        
        self.header_data = header_data