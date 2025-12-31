"""
报告向导对话框视图
实现报告生成向导的主界面
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWizard, QWizardPage, 
    QStackedLayout, QPushButton, QLabel, QProgressBar, QWidget
)
from PyQt5.QtCore import pyqtSignal
from src.features.report_wizard.view.header_info_page import HeaderInfoPage
from src.features.report_wizard.view.body_content_page import BodyContentPage


class ReportWizardDialog(QDialog):
    """
    报告向导对话框视图
    实现报告生成向导的主界面
    """
    
    # 自定义信号
    wizard_finished = pyqtSignal(str)  # 传递生成的报告路径
    
    def __init__(self, parent=None):
        """初始化报告向导对话框"""
        super().__init__(parent)
        self.setWindowTitle("报告生成向导")
        self.setGeometry(200, 200, 800, 600)
        
        # 当前页索引
        self.current_page_index = 0
        
        # 存储所有页面
        self.pages = []
        
        # 初始化UI
        self.init_ui()
        
        # 添加页眉信息页面
        self.add_header_info_page()
        
        # 添加正文内容编辑页面
        self.add_body_content_page()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()
        
        # 标题栏
        title_label = QLabel("创建标准化测试报告")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 进度指示器
        self.progress_label = QLabel("步骤 1/2: 页眉信息")
        self.progress_label.setStyleSheet("font-size: 14px; margin: 5px;")
        main_layout.addWidget(self.progress_label)
        
        # 页面容器
        self.page_container = QStackedLayout()
        main_layout.addLayout(self.page_container)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一步")
        self.prev_button.clicked.connect(self.go_to_prev_page)
        self.prev_button.setEnabled(False)  # 初始时禁用上一步按钮
        
        self.next_button = QPushButton("下一步")
        self.next_button.clicked.connect(self.go_to_next_page)
        
        self.finish_button = QPushButton("完成")
        self.finish_button.clicked.connect(self.finish_wizard)
        self.finish_button.setEnabled(False)  # 初始时禁用完成按钮
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.finish_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def add_header_info_page(self):
        """添加页眉信息页面"""
        header_page = HeaderInfoPage()
        self.pages.append(header_page)
        self.page_container.addWidget(header_page)
        self.update_navigation_buttons()
    
    def add_body_content_page(self):
        """添加正文内容编辑页面"""
        body_content_page = BodyContentPage()
        self.pages.append(body_content_page)
        self.page_container.addWidget(body_content_page)
        
        # 连接正文内容更新信号
        body_content_page.content_updated.connect(self._on_content_updated)
        
        self.update_navigation_buttons()
    
    def _on_content_updated(self, document_path: str):
        """处理正文内容更新完成事件"""
        print(f"正文内容已更新: {document_path}")
    
    def go_to_prev_page(self):
        """跳转到上一页"""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.page_container.setCurrentIndex(self.current_page_index)
            self.update_navigation_buttons()
    
    def go_to_next_page(self):
        """跳转到下一页"""
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.page_container.setCurrentIndex(self.current_page_index)
            self.update_navigation_buttons()
    
    def finish_wizard(self):
        """完成向导"""
        # 获取所有页面的数据
        all_data = self.get_all_data()
        
        # 获取正文内容页面的文档路径
        body_content_page = self.pages[1]  # 假设正文内容页面是第二个页面
        document_path = body_content_page.get_document_path()
        
        if document_path:
            print(f"完成向导，文档路径: {document_path}")
            print(f"页眉数据: {all_data.get('header_data')}")
        else:
            print("完成向导，但未选择文档")
            
        self.accept()  # 关闭对话框
    
    def update_navigation_buttons(self):
        """更新导航按钮状态"""
        # 更新进度标签
        self.progress_label.setText(f"步骤 {self.current_page_index + 1}/{len(self.pages)}: {self.get_page_title()}")
        
        # 更新上一步按钮状态
        self.prev_button.setEnabled(self.current_page_index > 0)
        
        # 更新下一步按钮状态
        self.next_button.setEnabled(self.current_page_index < len(self.pages) - 1)
        
        # 更新完成按钮状态
        self.finish_button.setEnabled(self.current_page_index == len(self.pages) - 1)
    
    def get_page_title(self) -> str:
        """获取当前页面标题"""
        if self.current_page_index == 0:
            return "页眉信息"
        elif self.current_page_index == 1:
            return "正文内容编辑"
        return f"步骤 {self.current_page_index + 1}"
    
    def get_all_data(self):
        """获取所有页面的数据"""
        all_data = {}
        
        # 获取页眉信息页面的数据
        if len(self.pages) > 0:
            header_page = self.pages[0]
            if hasattr(header_page, 'get_header_data'):
                all_data['header_data'] = header_page.get_header_data()
        
        return all_data