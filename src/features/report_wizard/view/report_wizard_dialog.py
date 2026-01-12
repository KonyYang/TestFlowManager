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
from src.features.report_wizard.view.test_spec_tables_page import TestSpecTablesPage


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
        
        # Matrix服务引用
        self.matrix_service = None
        
        # 初始化UI
        self.init_ui()
        
        # 添加页眉信息页面
        self.add_header_info_page()
        
        # 添加正文内容编辑页面
        self.add_body_content_page()
        
        # 添加Test Spec Tables页面
        self.add_test_spec_tables_page()
    
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
        
        # 上一步按钮已被禁用以简化操作流程
        # self.prev_button = QPushButton("上一步")
        # self.prev_button.clicked.connect(self.go_to_prev_page)
        # self.prev_button.setEnabled(False)  # 初始时禁用上一步按钮
        
        self.next_button = QPushButton("下一步")
        self.next_button.clicked.connect(self.go_to_next_page)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        # button_layout.addWidget(self.prev_button)  # 已禁用上一步按钮
        button_layout.addWidget(self.next_button)
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
    
    def add_test_spec_tables_page(self):
        """添加Test Spec Tables页面"""
        from src.core.logger import logger
        # 从body_content_page获取文档路径
        if len(self.pages) > 1:
            body_page = self.pages[1]  # 第二页是正文内容编辑页
            if hasattr(body_page, 'get_document_path'):
                document_path = body_page.get_document_path()
                logger.info(f"从body_content_page获取文档路径: {document_path}")
            else:
                document_path = None
                logger.info("body_content_page没有get_document_path方法")
        else:
            document_path = None
            logger.info("页面列表中body_content_page不存在")
        
        logger.info(f"创建TestSpecTablesPage: 传递document_path和matrix_service参数")
        logger.info(f"传递的document_path: {document_path}")
        logger.info(f"传递的matrix_service: {self.matrix_service is not None}")
        
        # 创建TestSpecTablesPage并传递文档路径和Matrix服务
        test_spec_page = TestSpecTablesPage(
            document_path=document_path,
            matrix_service=self.matrix_service  # 传递Matrix服务
        )
        
        # 注释掉next_clicked信号连接，因为现在处理完成后直接关闭向导
        # test_spec_page.next_clicked.connect(self.go_to_next_page)
        
        self.pages.append(test_spec_page)
        self.page_container.addWidget(test_spec_page)
        
        self.update_navigation_buttons()
    
    def _on_content_updated(self, document_path: str):
        """处理正文内容更新完成事件"""
        print(f"正文内容已更新: {document_path}")
    
    # def go_to_prev_page(self):
    #     """跳转到上一页"""
    #     if self.current_page_index > 0:
    #         # 在切换页面之前，保存当前页面的数据
    #         current_page = self.pages[self.current_page_index]
    #         if hasattr(current_page, 'get_header_data'):
    #             # 保存页眉页面数据
    #             header_data = current_page.get_header_data()
    #         
    #         self.current_page_index -= 1
    #         self.page_container.setCurrentIndex(self.current_page_index)
    #         self.update_navigation_buttons()
    
    def go_to_next_page(self):
        """跳转到下一页"""
        import os
        from src.features.report_wizard.service.report_generation_service import ReportGenerationService
        from src.core.logger import logger
        
        logger.info(f"准备跳转到第 {self.current_page_index + 1} 页，当前索引: {self.current_page_index}")
        
        if self.current_page_index < len(self.pages) - 1:
            # 在跳转到下一页之前，处理当前页的数据
            if self.current_page_index == 0:  # 从页眉信息页跳转到正文内容页
                logger.info("开始处理页眉信息页面数据")
                
                # 获取页眉信息页面的数据
                header_page = self.pages[0]
                header_data = header_page.get_header_data()
                
                logger.info(f"获取到页眉数据: {header_data}")
                
                # 创建报告生成服务
                service = ReportGenerationService()
                
                # 创建报告文档
                logger.info("开始创建报告文档")
                try:
                    document_path = service.create_report_from_template(header_data)
                    logger.info(f"报告文档创建成功: {document_path}")
                    
                    # 设置正文内容页面的文档路径
                    body_content_page = self.pages[1]
                    body_content_page.set_document_path(document_path)
                    
                    logger.info(f"文档路径已设置到正文内容页面: {document_path}")
                    
                except Exception as e:
                    logger.error(f"创建报告文档失败: {e}")
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "错误", f"创建报告文档失败: {str(e)}")
                    return  # 不继续跳转到下一页
            
            # 跳转到下一页
            self.current_page_index += 1
            
            logger.info(f"跳转到页面索引: {self.current_page_index}")
            
            # 如果跳转到TestSpecTablesPage（索引为2），则传递文档路径和Matrix服务
            if self.current_page_index == 2 and len(self.pages) > 1:
                body_page = self.pages[1]  # 第二页是正文内容编辑页
                logger.info(f"正在跳转到TestSpecTablesPage，body_page类型: {type(body_page)}")
                
                document_path = None
                if hasattr(body_page, 'get_document_path'):
                    document_path = body_page.get_document_path()
                    logger.info(f"从body_page获取文档路径: {document_path}")
                else:
                    logger.info("body_page没有get_document_path方法")
                
                if document_path:
                    test_spec_page = self.pages[2]
                    logger.info(f"向test_spec_page设置文档路径: {document_path}")
                    if hasattr(test_spec_page, 'set_document_path'):
                        test_spec_page.set_document_path(document_path)
                        
                    # 同时设置Matrix服务（如果可用）
                    if self.matrix_service:
                        logger.info("向test_spec_page设置Matrix服务")
                        if hasattr(test_spec_page, 'set_matrix_service'):
                            test_spec_page.set_matrix_service(self.matrix_service)
                else:
                    logger.warning("无法获取文档路径")
            
            self.page_container.setCurrentIndex(self.current_page_index)
            self.update_navigation_buttons()
            
            logger.info(f"已跳转到第 {self.current_page_index + 1} 页")
    
    def update_navigation_buttons(self):
        """更新导航按钮状态"""
        # 更新进度标签
        self.progress_label.setText(f"步骤 {self.current_page_index + 1}/{len(self.pages)}: {self.get_page_title()}")
        
        # 上一步按钮已被禁用以简化操作流程
        # self.prev_button.setEnabled(self.current_page_index > 0)
        
        # 更新下一步按钮状态
        self.next_button.setEnabled(self.current_page_index < len(self.pages) - 1)
        

    
    def get_page_title(self) -> str:
        """获取当前页面标题"""
        if self.current_page_index == 0:
            return "页眉信息"
        elif self.current_page_index == 1:
            return "正文内容编辑"
        elif self.current_page_index == 2:
            return "填充Test表格"
        return f"步骤 {self.current_page_index + 1}"
    
    def get_all_data(self):
        """获取所有页面的数据"""
        all_data = {}
        
        # 获取页眉信息页面的数据
        if len(self.pages) > 0:
            header_page = self.pages[0]
            if hasattr(header_page, 'get_header_data'):
                all_data['header_data'] = header_page.get_header_data()
        
        # 获取Test Spec Tables页面的数据
        if len(self.pages) > 2:
            test_spec_page = self.pages[2]
            if hasattr(test_spec_page, 'get_current_data'):
                all_data['test_spec_data'] = test_spec_page.get_current_data()
        
        return all_data
    
    def set_matrix_service(self, matrix_service):
        """设置Matrix服务"""
        from src.core.logger import logger
        logger.info(f"ReportWizardDialog接收到Matrix服务: {matrix_service is not None}")
        self.matrix_service = matrix_service

