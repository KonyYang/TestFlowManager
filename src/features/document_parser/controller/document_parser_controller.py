"""
文档解析控制器
协调文档解析和处理的各个组件
"""

from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from src.features.document_parser.service.document_parser_service import DocumentParserService
from src.features.document_parser.protocols.content_editor_protocol import (
    DocumentContentEditorProtocol,
    BodyContentServiceProtocol,
)
from src.core.logger import logger


class DocumentParserController:
    """
    文档解析控制器
    协调文档解析和处理的各个组件
    """

    def __init__(
        self,
        parent_window=None,
        body_content_service: Optional[BodyContentServiceProtocol] = None,
        document_content_editor: Optional[DocumentContentEditorProtocol] = None,
    ):
        """
        初始化文档解析控制器
        
        Args:
            parent_window: 父窗口
            body_content_service: 正文内容服务（可选，默认使用 content_editor 实现）
            document_content_editor: 文档内容编辑器（可选，默认使用 content_editor 实现）
        """
        self.parent_window = parent_window
        self.service = DocumentParserService()
        
        # 依赖注入：如果未提供，则延迟导入默认实现
        if body_content_service is None:
            from src.features.content_editor.service.body_content_service import BodyContentService
            self.body_content_service = BodyContentService()
        else:
            self.body_content_service = body_content_service
        
        if document_content_editor is None:
            from src.features.content_editor.utils.document_content_editor import DocumentContentEditor
            self.document_content_editor = DocumentContentEditor()
        else:
            self.document_content_editor = document_content_editor

    def show_body_content_editor(self, file_path: str):
        """
        显示正文内容编辑器

        Args:
            file_path: Word文档路径
        """
        try:
            logger.info(f"开始显示正文内容编辑器，文件路径: {file_path}")
            # 使用文档内容编辑器工具来显示编辑对话框
            success = self.document_content_editor.edit_document_content(file_path, self.parent_window)
            if success:
                logger.info(f"正文内容编辑对话框已处理，文件路径: {file_path}")
            else:
                logger.warning(f"正文内容编辑对话框未成功处理，文件路径: {file_path}")
            
        except Exception as e:
            logger.error(f"显示正文内容编辑器时出错: {e}")
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
            logger.error(f"更新文档内容时出错: {e}")
            if self.parent_window:
                QMessageBox.critical(self.parent_window, "错误", f"更新文档内容时出错: {str(e)}")
