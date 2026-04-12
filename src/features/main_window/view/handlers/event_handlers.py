"""
事件处理模块
集中管理所有事件回调函数
"""

from PyQt5.QtWidgets import QFileDialog
from src.core.logger import logger


class EventHandlers:
    """事件处理器，集中管理所有UI事件回调"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def on_view_ltr(self) -> None:
        """处理查看LTR事件"""
        logger.debug("View LTR action triggered")
        if self.main_window.controller.handle_view_ltr():
            self._update_status()
    
    def on_new_file(self) -> None:
        """处理新建文件事件"""
        logger.debug("New file action triggered")
        if self.main_window.controller.handle_new_file():
            self._update_status()
    
    def on_open_project(self) -> None:
        """处理打开项目事件"""
        logger.debug("Open project action triggered")
        if self.main_window.controller.handle_open_project():
            self._update_status()
    
    def on_export_matrix(self) -> None:
        """处理导出矩阵事件"""
        self.main_window._on_export_matrix()
    
    def on_export_llcr(self) -> None:
        """处理导出LLCR事件"""
        logger.debug("Export LLCR action triggered")
        if self.main_window.matrix_controller.handle_export_llcr():
            self._update_status()
    
    def on_export_cr(self) -> None:
        """处理导出CR事件"""
        logger.debug("Export CR action triggered")
        if self.main_window.matrix_controller.handle_export_cr():
            self._update_status()
    
    def on_create_report(self) -> None:
        """处理创建报告事件"""
        logger.debug("Create report action triggered")
        self.main_window.report_wizard_controller.set_project_context(self.main_window.controller.project_context)
        self.main_window.report_wizard_controller.set_matrix_controller(self.main_window.matrix_controller)
        self.main_window.report_wizard_controller.show_wizard()
        self._update_status()
    
    def on_update_report(self) -> None:
        """处理更新报告事件"""
        logger.debug("Update report action triggered")
        self.main_window.report_updater_controller.set_project_context(self.main_window.controller.project_context)
        self.main_window.report_updater_controller.show_report_updater_dialog()
        self._update_status()
    
    def on_convert_customer_version(self) -> None:
        """处理转换为客户版本事件"""
        logger.debug("Convert to customer version action triggered")
        if self.main_window.customer_report_controller.handle_generate_customer_report_with_context(self.main_window.controller.project_context):
            self._update_status()
        else:
            self._update_status()
    
    def on_edit_body_content(self) -> None:
        """处理编辑正文内容事件"""
        logger.debug("Edit body content action triggered")
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "选择 Word 文档", "", "Word 文档 (*.doc *.docx)"
        )
        if file_path:
            logger.info(f"用户选择了文件：{file_path}")
            self.main_window.document_parser_controller.show_body_content_editor(file_path)
        else:
            logger.info("用户取消了文件选择")
        self._update_status()
    
    def on_encrypt_test_files(self) -> None:
        """处理加密测试文件事件"""
        logger.debug("Encrypt test files action triggered")
        try:
            from src.features.file_encryption.controller.file_encryption_controller import FileEncryptionController
            
            encryption_controller = FileEncryptionController(self.main_window)
            folder_path = encryption_controller.show_folder_selection()
            if folder_path:
                encryption_controller.start_encryption_task(folder_path)
            self._update_status()
        except Exception as e:
            logger.error(f"加密功能执行失败：{e}", exc_info=True)
    
    def on_exit(self) -> None:
        """处理退出应用事件"""
        logger.debug("Exit action triggered")
        self.main_window.close()
    
    def on_about(self) -> None:
        """处理关于对话框事件"""
        logger.debug("About action triggered")
        self.main_window.controller.handle_about()
    
    def _update_status(self) -> None:
        """更新状态栏"""
        status = self.main_window.controller.get_status()
        self.main_window.status_label.setText(status)
