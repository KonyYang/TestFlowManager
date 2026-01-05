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
from src.core.logger import logger

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
        self.version_edit.setPlaceholderText("例如: A")
        self.version_edit.setText("A")  # 默认值
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
        
        # 样品接收日期
        self.sample_received_date = QDateEdit()
        self.sample_received_date.setDate(QDate.currentDate())
        self.sample_received_date.setCalendarPopup(True)
        form_layout.addRow("样品接收日期:", self.sample_received_date)
        
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
        report_date_qdate = self.report_completion_date.date()
        report_day = report_date_qdate.day()
        report_month = report_date_qdate.month()
        report_year = report_date_qdate.year()
        report_date_str = f"{report_day:02d}/{months[report_month]}/{report_year}"
        
        # 格式化样品接收日期
        sample_received_date_qdate = self.sample_received_date.date()
        sample_received_day = sample_received_date_qdate.day()
        sample_received_month = sample_received_date_qdate.month()
        sample_received_year = sample_received_date_qdate.year()
        sample_received_date_str = f"{sample_received_day:02d}/{months[sample_received_month]}/{sample_received_year}"
        
        self.header_data = HeaderData(
            report_no=self.report_no_edit.text().strip(),
            version=self.version_edit.text().strip(),
            tester=self.tester_edit.text().strip(),
            report_title=self.report_title_edit.text().strip(),
            requested_by=self.requested_by_edit.text().strip(),
            test_period=test_period,
            report_date=report_date_str,
            date_lab_received_samples=sample_received_date_str
        )
        return self.header_data
    
    def set_header_data(self, header_data: HeaderData):
        """
        设置页面中的页眉数据

        Args:
            header_data: 要设置的页眉数据对象
        """
        logger.info(f"开始设置页眉数据: {header_data}")

        self.report_no_edit.setText(header_data.report_no)
        self.version_edit.setText(header_data.version)
        self.tester_edit.setText(header_data.tester)
        self.report_title_edit.setText(header_data.report_title)
        self.requested_by_edit.setText(header_data.requested_by)

        # 首先记录从JSON获取的日期字段值
        logger.info(f"从JSON获取的start_test_date: '{header_data.start_test_date}'")
        logger.info(f"从JSON获取的finish_test_date: '{header_data.finish_test_date}'")
        logger.info(f"从JSON获取的report_date: '{header_data.report_date}'")
        logger.info(f"从JSON获取的test_period: '{header_data.test_period}'")
        logger.info(f"从JSON获取的date_lab_received_samples: '{header_data.date_lab_received_samples}'")
        
        # 优先使用单独的日期字段，如果不存在再尝试使用test_period字段
        # 设置样品接收日期
        sample_received_date_set = False
        if header_data.date_lab_received_samples:
            try:
                # 优先使用手动解析器处理标准格式 "DD MMM YYYY"
                parsed_date = self.parse_date_string(header_data.date_lab_received_samples)
                if parsed_date and parsed_date.isValid():
                    self.sample_received_date.setDate(parsed_date)
                    logger.info(f"设置样品接收日期(从date_lab_received_samples字段手动解析): {parsed_date.toString('yyyy/MM/dd')}")
                    sample_received_date_set = True
                else:
                    # 如果手动解析失败，尝试其他方法
                    logger.debug(f"手动解析失败，尝试其他格式: '{header_data.date_lab_received_samples}'")
                    sample_received_date = QDate.fromString(header_data.date_lab_received_samples, "yyyy-MM-dd")
                    if not sample_received_date.isValid():
                        # 尝试其他格式
                        formats = ["dd MMM yyyy", "dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                        for fmt in formats:
                            sample_received_date = QDate.fromString(header_data.date_lab_received_samples, fmt)
                            logger.debug(f"尝试格式 '{fmt}'，解析结果: {sample_received_date.isValid()}")
                            if sample_received_date.isValid():
                                break

                    if sample_received_date.isValid():
                        self.sample_received_date.setDate(sample_received_date)
                        logger.info(f"设置样品接收日期(从date_lab_received_samples字段): {sample_received_date.toString('yyyy/MM/dd')}")
                        sample_received_date_set = True
                    else:
                        logger.warning(f"无法解析date_lab_received_samples: {header_data.date_lab_received_samples}")
                        logger.warning(f"可用格式: dd MMM yyyy, dd/MMM/yyyy, dd/MM/yyyy, d/MMM/yyyy, d/MM/yyyy, yyyy-MM-dd")
            except Exception as e:
                logger.error(f"解析date_lab_received_samples时出错: {e}")
        
        # 设置测试开始日期
        start_date_set = False
        if header_data.start_test_date:
            try:
                # 优先使用手动解析器处理标准格式 "DD MMM YYYY"
                parsed_date = self.parse_date_string(header_data.start_test_date)
                if parsed_date and parsed_date.isValid():
                    self.test_start_date.setDate(parsed_date)
                    logger.info(f"设置测试开始日期(从start_test_date字段手动解析): {parsed_date.toString('yyyy/MM/dd')}")
                    start_date_set = True
                else:
                    # 如果手动解析失败，尝试其他方法
                    logger.debug(f"手动解析失败，尝试其他格式: '{header_data.start_test_date}'")
                    start_date = QDate.fromString(header_data.start_test_date, "yyyy-MM-dd")
                    if not start_date.isValid():
                        # 尝试其他格式
                        formats = ["dd MMM yyyy", "dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                        for fmt in formats:
                            start_date = QDate.fromString(header_data.start_test_date, fmt)
                            logger.debug(f"尝试格式 '{fmt}'，解析结果: {start_date.isValid()}")
                            if start_date.isValid():
                                break

                    if start_date.isValid():
                        self.test_start_date.setDate(start_date)
                        logger.info(f"设置测试开始日期(从start_test_date字段): {start_date.toString('yyyy/MM/dd')}")
                        start_date_set = True
                    else:
                        logger.warning(f"无法解析start_test_date: {header_data.start_test_date}")
                        logger.warning(f"可用格式: dd MMM yyyy, dd/MMM/yyyy, dd/MM/yyyy, d/MMM/yyyy, d/MM/yyyy, yyyy-MM-dd")
            except Exception as e:
                logger.error(f"解析start_test_date时出错: {e}")
        
        # 设置测试结束日期
        finish_date_set = False
        if header_data.finish_test_date:
            try:
                # 优先使用手动解析器处理标准格式 "DD MMM YYYY"
                parsed_date = self.parse_date_string(header_data.finish_test_date)
                if parsed_date and parsed_date.isValid():
                    self.test_end_date.setDate(parsed_date)
                    logger.info(f"设置测试结束日期(从finish_test_date字段手动解析): {parsed_date.toString('yyyy/MM/dd')}")
                    finish_date_set = True
                else:
                    # 如果手动解析失败，尝试其他方法
                    logger.debug(f"手动解析失败，尝试其他格式: '{header_data.finish_test_date}'")
                    end_date = QDate.fromString(header_data.finish_test_date, "yyyy-MM-dd")
                    if not end_date.isValid():
                        # 尝试其他格式
                        formats = ["dd MMM yyyy", "dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                        for fmt in formats:
                            end_date = QDate.fromString(header_data.finish_test_date, fmt)
                            logger.debug(f"尝试格式 '{fmt}'，解析结果: {end_date.isValid()}")
                            if end_date.isValid():
                                break

                    if end_date.isValid():
                        self.test_end_date.setDate(end_date)
                        logger.info(f"设置测试结束日期(从finish_test_date字段): {end_date.toString('yyyy/MM/dd')}")
                        finish_date_set = True
                    else:
                        logger.warning(f"无法解析finish_test_date: {header_data.finish_test_date}")
                        logger.warning(f"可用格式: dd MMM yyyy, dd/MMM/yyyy, dd/MM/yyyy, d/MMM/yyyy, d/MM/yyyy, yyyy-MM-dd")
            except Exception as e:
                logger.error(f"解析finish_test_date时出错: {e}")
        
        # 如果单独的日期字段未设置，尝试从test_period字段解析
        if not start_date_set or not finish_date_set:
            if header_data.test_period:
                try:
                    # 测试周期格式为 "DD/MMM/YYYY-DD/MMM/YYYY" 或 "DD MMM YYYY-DD MMM YYYY"
                    if '-' in header_data.test_period:
                        dates = header_data.test_period.split('-')
                        if len(dates) >= 2:
                            start_date_str = dates[0].strip()
                            end_date_str = dates[1].strip()

                            # 解析开始日期
                            if not start_date_set:
                                # 优先使用手动解析器
                                parsed_date = self.parse_date_string(start_date_str)
                                if parsed_date and parsed_date.isValid():
                                    self.test_start_date.setDate(parsed_date)
                                    logger.info(f"设置测试开始日期(从test_period字段手动解析): {parsed_date.toString('yyyy/MM/dd')}")
                                else:
                                    start_date = QDate.fromString(start_date_str, "dd/MMM/yyyy")
                                    if not start_date.isValid():
                                        # 尝试其他格式
                                        formats = ["dd MMM yyyy", "dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                                        for fmt in formats:
                                            start_date = QDate.fromString(start_date_str, fmt)
                                            logger.debug(f"从test_period解析开始日期，格式 '{fmt}'，结果: {start_date.isValid()}")
                                            if start_date.isValid():
                                                break

                                    if start_date.isValid():
                                        self.test_start_date.setDate(start_date)
                                        logger.info(f"设置测试开始日期(从test_period字段): {start_date.toString('yyyy/MM/dd')}")

                            # 解析结束日期
                            if not finish_date_set:
                                # 优先使用手动解析器
                                parsed_date = self.parse_date_string(end_date_str)
                                if parsed_date and parsed_date.isValid():
                                    self.test_end_date.setDate(parsed_date)
                                    logger.info(f"设置测试结束日期(从test_period字段手动解析): {parsed_date.toString('yyyy/MM/dd')}")
                                else:
                                    end_date = QDate.fromString(end_date_str, "dd/MMM/yyyy")
                                    if not end_date.isValid():
                                        # 尝试其他格式
                                        formats = ["dd MMM yyyy", "dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MMM/yyyy", "yyyy-MM-dd"]
                                        for fmt in formats:
                                            end_date = QDate.fromString(end_date_str, fmt)
                                            logger.debug(f"从test_period解析结束日期，格式 '{fmt}'，结果: {end_date.isValid()}")
                                            if end_date.isValid():
                                                break

                                    if end_date.isValid():
                                        self.test_end_date.setDate(end_date)
                                        logger.info(f"设置测试结束日期(从test_period字段): {end_date.toString('yyyy/MM/dd')}")
                except Exception as e:
                    logger.error(f"解析测试周期时出错: {e}")

        # 设置报告完成日期
        report_date_set = False
        if header_data.report_date:  # 使用report_date字段
            try:
                # 优先使用手动解析器处理标准格式 "DD MMM YYYY"
                parsed_date = self.parse_date_string(header_data.report_date)
                if parsed_date and parsed_date.isValid():
                    self.report_completion_date.setDate(parsed_date)
                    logger.info(f"设置报告完成日期(从report_date字段手动解析): {parsed_date.toString('yyyy/MM/dd')}")
                    report_date_set = True
                else:
                    # 如果手动解析失败，尝试其他方法
                    logger.debug(f"手动解析失败，尝试其他格式: '{header_data.report_date}'")
                    report_date = QDate.fromString(header_data.report_date, "yyyy-MM-dd")
                    if not report_date.isValid():
                        # 尝试其他格式
                        formats = ["dd MMM yyyy", "dd/MMM/yyyy", "dd/MM/yyyy", "d/MMM/yyyy", "d/MM/yyyy", "yyyy-MM-dd"]
                        for fmt in formats:
                            report_date = QDate.fromString(header_data.report_date, fmt)
                            logger.debug(f"尝试格式 '{fmt}'，解析结果: {report_date.isValid()}")
                            if report_date.isValid():
                                break

                    if report_date.isValid():
                        self.report_completion_date.setDate(report_date)
                        logger.info(f"设置报告完成日期(从report_date字段): {report_date.toString('yyyy/MM/dd')}")
                        report_date_set = True
                    else:
                        logger.warning(f"无法解析report_date: {header_data.report_date}")
                        logger.warning(f"可用格式: dd MMM yyyy, dd/MMM/yyyy, dd/MM/yyyy, d/MMM/yyyy, d/MM/yyyy, yyyy-MM-dd")
            except Exception as e:
                logger.error(f"解析report_date时出错: {e}")
        
        # 如果以上都没有设置，使用当前日期
        if not report_date_set:
            self.report_completion_date.setDate(QDate.currentDate())
            logger.info(f"使用当前日期作为报告完成日期")

        self.header_data = header_data
        logger.info("页眉数据设置完成")
        
    def parse_date_string(self, date_str: str):
        """
        手动解析日期字符串，优先处理JSON中的标准格式 "DD MMM YYYY" (如 "07 Dec 2025")
        """
        import re
        from datetime import datetime
        
        if not date_str:
            return None
            
        logger.debug(f"尝试手动解析日期字符串: {date_str}")
        
        # 清理输入字符串
        date_str = date_str.strip()
        
        # 尝试解析 "DD MMM YYYY" 格式，例如 "07 Dec 2025"
        # 这是JSON中标准的日期格式
        pattern1 = r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})"
        match = re.match(pattern1, date_str)
        
        if match:
            day = int(match.group(1))
            month_str = match.group(2).capitalize()  # 确保首字母大写
            year = int(match.group(3))
            
            # 月份缩写映射
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            if month_str in month_map:
                month = month_map[month_str]
                try:
                    # 验证日期是否有效
                    datetime(year, month, day)
                    # 创建QDate对象
                    qdate = QDate(year, month, day)
                    if qdate.isValid():
                        logger.debug(f"手动解析成功 (DD MMM YYYY): {qdate.toString('yyyy/MM/dd')}")
                        return qdate
                    else:
                        logger.warning(f"创建的QDate对象无效 (DD MMM YYYY): {year}-{month}-{day}")
                except ValueError as e:
                    logger.error(f"日期验证失败 (DD MMM YYYY): {e}")
        
        # 尝试解析 "DD/MMM/YYYY" 格式，例如 "07/Dec/2025"
        pattern2 = r"(\d{1,2})[/](\w{3})[/](\d{4})"
        match = re.match(pattern2, date_str)
        
        if match:
            day = int(match.group(1))
            month_str = match.group(2).capitalize()  # 确保首字母大写
            year = int(match.group(3))
            
            # 月份缩写映射
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            if month_str in month_map:
                month = month_map[month_str]
                try:
                    # 验证日期是否有效
                    datetime(year, month, day)
                    # 创建QDate对象
                    qdate = QDate(year, month, day)
                    if qdate.isValid():
                        logger.debug(f"手动解析成功 (DD/MMM/YYYY): {qdate.toString('yyyy/MM/dd')}")
                        return qdate
                    else:
                        logger.warning(f"创建的QDate对象无效 (DD/MMM/YYYY): {year}-{month}-{day}")
                except ValueError as e:
                    logger.error(f"日期验证失败 (DD/MMM/YYYY): {e}")
        
        logger.debug(f"手动解析失败: {date_str}")
        return None
