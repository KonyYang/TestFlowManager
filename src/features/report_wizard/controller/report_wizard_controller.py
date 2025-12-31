"""
报告向导控制器
协调报告生成向导的各个组件
"""

from typing import Optional
from PyQt5.QtWidgets import QApplication
from src.features.report_wizard.view.report_wizard_dialog import ReportWizardDialog
from src.features.report_wizard.service.report_generation_service import ReportGenerationService
from src.features.report_wizard.model.header_data import HeaderData


class ReportWizardController:
    """
    报告向导控制器
    协调报告生成向导的各个组件
    """

    def __init__(self, parent_window=None):
        """初始化报告向导控制器"""
        self.parent_window = parent_window
        self.view = None
        self.service = ReportGenerationService()
        self.current_project_path = None

    def set_project_path(self, project_path: str):
        """
        设置当前项目路径
        
        Args:
            project_path: 项目路径
        """
        self.current_project_path = project_path

    def show_wizard(self):
        """显示报告向导对话框"""
        self.view = ReportWizardDialog(self.parent_window)
        
        # 如果有项目路径，尝试加载项目数据
        if self.current_project_path:
            project_data = self.service.load_project_data(self.current_project_path)
            if project_data:
                # 获取页眉信息页面并设置数据
                header_page = self.view.pages[0]  # 第一页是页眉信息页
                header_page.set_header_data(project_data)
        
        # 连接完成信号
        self.view.finished.connect(self.on_wizard_finished)
        
        # 显示对话框
        self.view.exec_()

    def on_wizard_finished(self, result):
        """
        处理向导完成事件
        
        Args:
            result: 对话框结果（Accepted或Rejected）
        """
        if result == ReportWizardDialog.Accepted:
            # 获取所有数据
            all_data = self.view.get_all_data()
            
            if 'header_data' in all_data:
                header_data = all_data['header_data']
                
                try:
                    # 获取正文内容页面的文档路径
                    body_content_page = self.view.pages[1]  # 第二页是正文内容编辑页
                    document_path = body_content_page.get_document_path()
                    
                    if document_path:
                        # 如果用户选择了文档，则更新文档内容
                        print(f"使用用户选择的文档: {document_path}")
                        output_path = document_path
                    else:
                        # 如果用户没有选择文档，则生成新报告
                        output_path = self.service.create_report_from_template(header_data)

                    # 显示成功消息
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(self.view, "成功", f"报告已成功生成:\n{output_path}")
                    
                    print(f"报告已生成: {output_path}")
                    
                except Exception as e:
                    # 处理错误
                    print(f"生成报告时出错: {e}")
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self.view, "错误", f"生成报告时出错: {str(e)}")