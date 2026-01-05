"""
内容编辑器控制器
协调文档内容编辑的各个组件
"""

from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from src.features.document_parser.service.body_content_service import BodyContentService
from src.features.content_editor.view.body_content_dialog import BodyContentDialog
from src.core.logger import logger


class ContentEditorController:
    """
    内容编辑器控制器
    协调文档内容编辑的各个组件
    """

    def __init__(self, parent_window=None):
        """初始化内容编辑器控制器"""
        self.parent_window = parent_window
        self.body_content_service = BodyContentService()
        
        # 确保Word应用程序在后台运行
        try:
            from src.utils.word_utils import get_shared_word_app
            word_app = get_shared_word_app()
            if word_app:
                word_app.Visible = False
                word_app.DisplayAlerts = False
        except Exception as e:
            logger.error(f"初始化时设置Word应用程序后台模式失败: {e}")

    def show_body_content_editor(self, file_path: str):
        """
        显示正文内容编辑器

        Args:
            file_path: Word文档路径
        """
        try:
            logger.info(f"开始显示正文内容编辑器，文件路径: {file_path}")
            # 显示编辑对话框
            dialog = BodyContentDialog(file_path, self.parent_window)
            logger.info(f"正文内容编辑对话框已创建，文件路径: {file_path}")
            
            # 连接内容更新信号
            dialog.content_updated.connect(
                lambda updates: self._update_document_content(file_path, updates)
            )
            
            dialog.exec_()
            logger.info(f"正文内容编辑对话框已关闭，文件路径: {file_path}")
            
        except Exception as e:
            print(f"显示正文内容编辑器时出错: {e}")
            if self.parent_window:
                QMessageBox.critical(self.parent_window, "错误", f"显示正文内容编辑器时出错: {str(e)}")

    def _update_document_content(self, file_path: str, updates: dict):
        """
        更新文档内容

        Args:
            file_path: Word文档路径
            updates: 更新内容字典
        """
        try:
            # 由于更新已在对话框中完成，这里只需要显示成功消息
            if updates:
                if self.parent_window:
                    QMessageBox.information(self.parent_window, "成功", "文档内容已成功更新")
        except Exception as e:
            print(f"更新文档内容时出错: {e}")
            if self.parent_window:
                QMessageBox.critical(self.parent_window, "错误", f"更新文档内容时出错: {str(e)}")