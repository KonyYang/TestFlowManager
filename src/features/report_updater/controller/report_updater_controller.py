"""
报告更新模块控制器
处理报告更新功能的业务逻辑
"""
import os
from typing import Optional, List, Dict
from PyQt5.QtWidgets import QWidget, QMessageBox, QFileDialog, QDialog
from src.core.logger import logger
from src.features.report_updater.model.report_updater_data import ReportUpdaterData
from src.features.report_updater.view.report_updater_dialog import ReportUpdaterDialog
from src.features.report_updater.service.report_updater_service import ReportUpdaterService


class ReportUpdaterController:
    """报告更新功能的控制器类"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化报告更新控制器

        Args:
            parent: 父窗口部件
        """
        self.parent = parent
        self.data_model = ReportUpdaterData()
        self.service = ReportUpdaterService()  # 添加服务实例
        self.current_project_path = None  # 存储当前项目路径
        self.view: Optional[ReportUpdaterDialog] = None
        logger.info("ReportUpdaterController initialized")
    
    def set_project_path(self, project_path: Optional[str]) -> None:
        """
        设置当前项目路径

        Args:
            project_path: 项目路径，如果为None则表示没有打开项目
        """
        if project_path and os.path.exists(project_path):
            self.current_project_path = project_path
            self.data_model.set_project_path(project_path)
            # 重新创建服务实例以使用新的项目路径
            self.service = ReportUpdaterService(project_path=project_path)
            logger.info(f"Project path set to: {project_path}")
        else:
            # 没有项目打开，使用默认路径
            self.current_project_path = None
            self.data_model.is_project_loaded = False
            self.data_model.config.base_directory = "D:\\OutFile"
            # 重新创建服务实例以使用默认配置
            self.service = ReportUpdaterService()
            logger.info("No project loaded, using default path: D:\\OutFile")
    
    def show_report_updater_dialog(self) -> bool:
        """
        显示报告更新对话框，首先弹出文件选择对话框

        Returns:
            是否成功显示对话框
        """
        try:
            logger.info("Showing report updater dialog")
            
            # 首先弹出文件选择对话框
            selected_report = self.select_report_file()
            if not selected_report:
                logger.info("User cancelled report file selection")
                return False
            
            # 设置选中的报告文件
            self.data_model.select_report(selected_report)
            
            # 创建对话框，只显示更新功能（不显示文件列表）
            self.view = ReportUpdaterDialog(self.data_model, parent=self.parent, selected_report=selected_report)
            
            # 连接对话框的信号
            self.view.equipment_update_requested.connect(self.handle_equipment_update)
            
            # 显示对话框
            result = self.view.exec_()
            
            if result == QDialog.Accepted:
                logger.info("Report updater dialog accepted")
                return True
            else:
                logger.info("Report updater dialog cancelled")
                return False
                
        except Exception as e:
            logger.error(f"Error showing report updater dialog: {e}")
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"显示报告更新对话框时出错: {str(e)}")
            return False
    
    def handle_equipment_update(self) -> bool:
        """
        处理设备列表更新请求

        Returns:
            是否成功更新设备列表
        """
        try:
            logger.info("Handling equipment list update request")
            
            # 获取选中的报告文件
            selected_report = self.data_model.config.selected_report_path
            if not selected_report:
                # 如果没有选择报告，让用户选择一个
                selected_report = self.select_report_file()
                if not selected_report:
                    QMessageBox.warning(self.parent, "警告", "请先选择要更新的报告文件！")
                    return False
            
            # 直接使用服务层执行实际的更新操作，不需要传入设备数据
            # 因为新的实现会从外部源（Excel文件）获取设备数据
            success = self.service.update_equipment_list(selected_report)
            
            if success:
                # 更新数据模型
                QMessageBox.information(self.parent, "成功", f"设备列表已成功更新到报告:\n{os.path.basename(selected_report)}")
                logger.info(f"Equipment list updated successfully in {selected_report}")
            else:
                QMessageBox.warning(self.parent, "警告", "设备列表更新失败！")
                logger.warning("Equipment list update failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error handling equipment update: {e}")
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"更新设备列表时出错: {str(e)}")
            return False
    
    def select_report_file(self) -> Optional[str]:
        """
        让用户选择报告文件

        Returns:
            选中的文件路径，如果取消则返回None
        """
        try:
            # 根据是否有项目打开来决定起始目录
            start_directory = self.data_model.get_current_directory()
            
            if not os.path.exists(start_directory):
                start_directory = "D:\\OutFile"
                if not os.path.exists(start_directory):
                    start_directory = os.path.expanduser("~")
            
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self.parent,
                "选择报告文件",
                start_directory,
                "文档文件 (*.docx *.doc *.pdf *.xlsx *.xls);;所有文件 (*)"
            )
            
            if file_path:
                # 选择文件成功
                self.data_model.select_report(file_path)
                logger.info(f"Selected report file: {file_path}")
                return file_path
            else:
                logger.info("User cancelled report file selection")
                return None
                
        except Exception as e:
            logger.error(f"Error selecting report file: {e}")
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"选择报告文件时出错: {str(e)}")
            return None
    
    def get_available_reports(self) -> List[str]:
        """
        获取可用的报告文件列表

        Returns:
            报告文件路径列表
        """
        return self.data_model.load_available_reports()