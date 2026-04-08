"""
客户报告生成控制器模块
处理客户报告生成的业务逻辑和事件
"""

from PyQt5.QtWidgets import QMessageBox
from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.features.customer_report_generator.service.customer_report_service import CustomerReportService


class CustomerReportController:
    """
    客户报告生成控制器类
    处理客户报告生成的业务逻辑和事件
    """

    def __init__(self, parent_window=None):
        """
        初始化客户报告生成控制器

        Args:
            parent_window: 父窗口实例
        """
        self.parent_window = parent_window
        self.service = CustomerReportService()
        self.project_context = None

    def handle_generate_customer_report(self, project_path=None):
        """
        处理生成客户报告事件

        Args:
            project_path: 项目路径

        Returns:
            bool: 是否成功生成客户报告
        """
        project_context = ProjectContext.from_project_path(project_path) if project_path else None
        return self.handle_generate_customer_report_with_context(project_context)

    def handle_generate_customer_report_with_context(self, project_context=None):
        project_path = project_context.project_path if project_context else None
        self.project_context = project_context
        try:
            logger.debug("处理生成客户报告事件")
            
            # 调用服务生成客户报告
            success, result = self.service.generate_customer_report(
                parent_window=self.parent_window,
                project_path=project_path
            )
            
            if success:
                # 不再显示成功消息框，只记录日志
                logger.info(f"客户报告生成成功: {result}")
                return True
            else:
                # 只有在真正发生错误时才显示错误消息
                # 如果用户取消操作，result会指示这一点，不需要显示错误框
                if result != "用户取消了操作" and result != "用户取消了保存操作":
                    QMessageBox.critical(
                        self.parent_window,
                        "客户报告生成失败",
                        f"生成客户报告时出现错误:\n{result}"
                    )
                logger.error(f"客户报告生成失败: {result}")
                return False
        except Exception as e:
            logger.error(f"处理生成客户报告事件时出错: {e}")
            QMessageBox.critical(
                self.parent_window,
                "错误",
                f"处理生成客户报告事件时出现未预期的错误:\n{str(e)}"
            )
            return False
