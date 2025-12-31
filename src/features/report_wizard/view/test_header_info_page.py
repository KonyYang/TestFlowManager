"""
HeaderInfoPage 单元测试
测试日期解析和其他功能
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# 添加项目路径以导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QApplication
from src.features.report_wizard.view.header_info_page import HeaderInfoPage
from src.features.report_wizard.model.header_data import HeaderData


class TestHeaderInfoPage(unittest.TestCase):
    """测试 HeaderInfoPage 类的功能"""
    
    @classmethod
    def setUpClass(cls):
        """初始化 QApplication"""
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """在每个测试方法前运行"""
        self.header_info_page = HeaderInfoPage()
    
    def tearDown(self):
        """在每个测试方法后运行"""
        self.header_info_page.deleteLater()
    
    def test_parse_date_string_valid_formats(self):
        """测试 parse_date_string 方法 - 有效格式"""
        # 测试 "07 Dec 2025" 格式
        result = self.header_info_page.parse_date_string("07 Dec 2025")
        self.assertIsNotNone(result)
        self.assertTrue(result.isValid())
        self.assertEqual(result.year(), 2025)
        self.assertEqual(result.month(), 12)  # Dec = 12
        self.assertEqual(result.day(), 7)
        
        # 测试 "1 Jan 2024" 格式（单个数字日期）
        result = self.header_info_page.parse_date_string("1 Jan 2024")
        self.assertIsNotNone(result)
        self.assertTrue(result.isValid())
        self.assertEqual(result.year(), 2024)
        self.assertEqual(result.month(), 1)  # Jan = 1
        self.assertEqual(result.day(), 1)
        
        # 测试 "15 Mar 2023" 格式
        result = self.header_info_page.parse_date_string("15 Mar 2023")
        self.assertIsNotNone(result)
        self.assertTrue(result.isValid())
        self.assertEqual(result.year(), 2023)
        self.assertEqual(result.month(), 3)  # Mar = 3
        self.assertEqual(result.day(), 15)
    
    def test_parse_date_string_invalid_formats(self):
        """测试 parse_date_string 方法 - 无效格式"""
        # 测试无效日期（例如2月30日）
        result = self.header_info_page.parse_date_string("30 Feb 2024")
        self.assertIsNone(result)
        
        # 测试无效月份
        result = self.header_info_page.parse_date_string("07 Xxx 2024")
        self.assertIsNone(result)
        
        # 测试无效格式
        result = self.header_info_page.parse_date_string("invalid date format")
        self.assertIsNone(result)
        
        # 测试空字符串
        result = self.header_info_page.parse_date_string("")
        self.assertIsNone(result)
    
    def test_set_header_data_with_valid_dates(self):
        """测试 set_header_data 方法 - 有效日期"""
        # 创建一个包含有效日期的 HeaderData 对象
        header_data = HeaderData(
            report_no="DL-2025-12345",
            version="1.0",
            date="07 Dec 2025",
            tester="Test User",
            report_title="Test Report Title",
            requested_by="Requester Name",
            test_period="07 Dec 2025-08 Dec 2025",
            start_test_date="07 Dec 2025",
            finish_test_date="08 Dec 2025",
            report_date="09 Dec 2025"
        )
        
        # 调用 set_header_data 方法
        self.header_info_page.set_header_data(header_data)
        
        # 验证文本字段是否正确设置
        self.assertEqual(self.header_info_page.report_no_edit.text(), "DL-2025-12345")
        self.assertEqual(self.header_info_page.version_edit.text(), "1.0")
        self.assertEqual(self.header_info_page.tester_edit.text(), "Test User")
        self.assertEqual(self.header_info_page.report_title_edit.text(), "Test Report Title")
        self.assertEqual(self.header_info_page.requested_by_edit.text(), "Requester Name")
        
        # 验证日期字段是否正确设置
        start_date = self.header_info_page.test_start_date.date()
        self.assertEqual(start_date.year(), 2025)
        self.assertEqual(start_date.month(), 12)
        self.assertEqual(start_date.day(), 7)
        
        end_date = self.header_info_page.test_end_date.date()
        self.assertEqual(end_date.year(), 2025)
        self.assertEqual(end_date.month(), 12)
        self.assertEqual(end_date.day(), 8)
        
        completion_date = self.header_info_page.report_completion_date.date()
        self.assertEqual(completion_date.year(), 2025)
        self.assertEqual(completion_date.month(), 12)
        self.assertEqual(completion_date.day(), 9)
    
    def test_set_header_data_with_invalid_dates(self):
        """测试 set_header_data 方法 - 无效日期"""
        # 创建一个包含无效日期的 HeaderData 对象
        header_data = HeaderData(
            report_no="DL-2025-12345",
            version="1.0",
            tester="Test User",
            report_title="Test Report Title",
            requested_by="Requester Name",
            start_test_date="30 Feb 2024",  # 无效日期
            finish_test_date="invalid date",  # 无效格式
            report_date="99 Xxx 2024"  # 无效月份
        )
        
        # 调用 set_header_data 方法
        self.header_info_page.set_header_data(header_data)
        
        # 对于无效日期，应该保持原始值（当前日期）
        current_date = QDate.currentDate()
        completion_date = self.header_info_page.report_completion_date.date()
        
        # 因为 report_date 无效，所以应该使用当前日期
        self.assertEqual(completion_date.year(), current_date.year())
        self.assertEqual(completion_date.month(), current_date.month())
        self.assertEqual(completion_date.day(), current_date.day())
    
    def test_set_header_data_with_test_period(self):
        """测试 set_header_data 方法 - 使用 test_period 字段"""
        # 创建一个包含 test_period 但没有单独日期字段的 HeaderData 对象
        header_data = HeaderData(
            report_no="DL-2025-12345",
            version="1.0",
            tester="Test User",
            report_title="Test Report Title",
            requested_by="Requester Name",
            test_period="05 Jan 2024-10 Jan 2024",  # DD MMM YYYY 格式
            start_test_date="",  # 空值
            finish_test_date=""  # 空值
        )
        
        # 调用 set_header_data 方法
        self.header_info_page.set_header_data(header_data)
        
        # 验证日期字段是否从 test_period 正确解析
        start_date = self.header_info_page.test_start_date.date()
        self.assertEqual(start_date.year(), 2024)
        self.assertEqual(start_date.month(), 1)  # Jan = 1
        self.assertEqual(start_date.day(), 5)
        
        end_date = self.header_info_page.test_end_date.date()
        self.assertEqual(end_date.year(), 2024)
        self.assertEqual(end_date.month(), 1)
        self.assertEqual(end_date.day(), 10)
    
    def test_set_header_data_empty_fields(self):
        """测试 set_header_data 方法 - 空字段"""
        # 创建一个所有字段都为空的 HeaderData 对象
        header_data = HeaderData()
        
        # 调用 set_header_data 方法
        self.header_info_page.set_header_data(header_data)
        
        # 验证文本字段是否被正确设置（注意 version 有默认值 'Rev.A'）
        self.assertEqual(self.header_info_page.report_no_edit.text(), "")
        self.assertEqual(self.header_info_page.version_edit.text(), "Rev.A")  # 默认值
        self.assertEqual(self.header_info_page.tester_edit.text(), "")
        self.assertEqual(self.header_info_page.report_title_edit.text(), "")
        self.assertEqual(self.header_info_page.requested_by_edit.text(), "")
        
        # 对于日期字段，应该保持当前日期
        current_date = QDate.currentDate()
        completion_date = self.header_info_page.report_completion_date.date()
        self.assertEqual(completion_date.year(), current_date.year())
        self.assertEqual(completion_date.month(), current_date.month())
        self.assertEqual(completion_date.day(), current_date.day())
    
    def test_get_header_data(self):
        """测试 get_header_data 方法"""
        # 预先设置一些值到页面组件
        self.header_info_page.report_no_edit.setText("DL-2025-54321")
        self.header_info_page.version_edit.setText("2.0")
        self.header_info_page.tester_edit.setText("Another User")
        self.header_info_page.report_title_edit.setText("Another Report Title")
        self.header_info_page.requested_by_edit.setText("Another Requester")
        
        # 设置一个特定日期
        test_date = QDate(2024, 6, 15)
        self.header_info_page.report_completion_date.setDate(test_date)
        
        # 获取 HeaderData 对象
        result = self.header_info_page.get_header_data()
        
        # 验证获取的数据是否正确
        self.assertEqual(result.report_no, "DL-2025-54321")
        self.assertEqual(result.version, "2.0")
        self.assertEqual(result.tester, "Another User")
        self.assertEqual(result.report_title, "Another Report Title")
        self.assertEqual(result.requested_by, "Another Requester")
        # 验证 report_date 应该是格式化的日期字符串
        self.assertIn("15/Jun/2024", result.report_date)
    
    def test_date_formats_priority(self):
        """测试日期格式解析的优先级 - 现在手动解析器优先处理 DD MMM YYYY 格式"""
        # 创建一个包含多种可能日期格式的 HeaderData 对象
        header_data = HeaderData(
            report_no="DL-2025-12345",
            start_test_date="2024-12-25",  # yyyy-MM-dd 格式
            finish_test_date="25 Dec 2024",  # dd MMM yyyy 格式 (JSON标准格式)
            report_date="26/Dec/2024"  # dd/MMM/yyyy 格式
        )
        
        # 调用 set_header_data 方法
        self.header_info_page.set_header_data(header_data)
        
        # 验证各种格式的日期是否都能被正确解析
        start_date = self.header_info_page.test_start_date.date()
        self.assertEqual(start_date.year(), 2024)
        self.assertEqual(start_date.month(), 12)
        self.assertEqual(start_date.day(), 25)
        
        end_date = self.header_info_page.test_end_date.date()
        self.assertEqual(end_date.year(), 2024)
        self.assertEqual(end_date.month(), 12)
        self.assertEqual(end_date.day(), 25)
        
        completion_date = self.header_info_page.report_completion_date.date()
        # 由于 "26/Dec/2024" 使用了 "/" 分隔符，应该能被手动解析器处理
        self.assertEqual(completion_date.year(), 2024)
        self.assertEqual(completion_date.month(), 12)
        self.assertEqual(completion_date.day(), 26)


if __name__ == '__main__':
    unittest.main()