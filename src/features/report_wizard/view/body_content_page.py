"""
正文内容页面视图
实现向导中正文内容编辑页面的UI组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QFrame, QTextEdit, QFileDialog
)
from PyQt5.QtCore import pyqtSignal
from src.features.document_parser.view.body_content_dialog import BodyContentDialog
from src.features.document_parser.service.body_content_service import BodyContentService
from src.core.logger import logger


class BodyContentPage(QFrame):
    """
    正文内容页面视图组件
    提供报告正文内容编辑的向导页面
    """
    
    # 自定义信号
    content_updated = pyqtSignal(str)  # 传递更新的文档路径
    
    def __init__(self, parent=None):
        """初始化正文内容页面"""
        super().__init__(parent)
        self.document_path = None
        self.body_content_service = BodyContentService()
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 页面标题
        title_label = QLabel("正文内容编辑")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 说明文本
        desc_label = QLabel("请选择需要编辑正文内容的Word文档")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 功能按钮区域
        button_group = QGroupBox("操作选项")
        button_layout = QHBoxLayout()
        
        # 选择现有文档按钮
        self.select_doc_btn = QPushButton("选择现有文档")
        self.select_doc_btn.clicked.connect(self.select_existing_document)
        button_layout.addWidget(self.select_doc_btn)
        
        # 编辑内容按钮
        self.edit_content_btn = QPushButton("编辑正文内容")
        self.edit_content_btn.clicked.connect(self.edit_document_content)
        self.edit_content_btn.setEnabled(False)  # 初始禁用，直到选择了文档
        button_layout.addWidget(self.edit_content_btn)
        
        button_group.setLayout(button_layout)
        layout.addWidget(button_group)
        
        # 文档路径显示
        self.path_label = QLabel("未选择文档")
        self.path_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.path_label)
        
        # 文档预览区域
        preview_group = QGroupBox("文档预览")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        self.setLayout(layout)
    
    def select_existing_document(self):
        """选择现有文档"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择Word文档", 
                "", 
                "Word文档 (*.doc *.docx)"
            )
            
            if file_path:
                self.document_path = file_path
                self.path_label.setText(f"文档路径: {file_path}")
                self.edit_content_btn.setEnabled(True)
                
                # 预览文档内容
                self.preview_document_content()
                
                logger.info(f"选择了文档: {file_path}")
                
        except Exception as e:
            logger.error(f"选择文档时出错: {e}")
    
    def edit_document_content(self):
        """编辑文档内容"""
        if not self.document_path:
            logger.warning("没有选择文档，无法编辑内容")
            return
        
        try:
            # 显示正文内容编辑对话框
            dialog = BodyContentDialog(self.document_path, self)
            
            # 连接内容更新信号
            dialog.content_updated.connect(self._on_content_updated)
            
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"编辑文档内容时出错: {e}")
    
    def _on_content_updated(self, updates):
        """处理内容更新完成事件"""
        logger.info(f"文档内容已更新")
        self.content_updated.emit(self.document_path)
        self.preview_document_content()
    
    def preview_document_content(self):
        """预览文档内容"""
        try:
            from docx import Document
            
            if self.document_path and self.document_path.endswith('.docx'):
                doc = Document(self.document_path)
                
                # 获取前几段内容作为预览
                preview_text = ""
                for i, paragraph in enumerate(doc.paragraphs):
                    if i >= 10:  # 只显示前10段
                        break
                    if paragraph.text.strip():
                        preview_text += paragraph.text + "\n"
                
                self.preview_text.setPlainText(preview_text or "文档为空或无可见内容")
            else:
                self.preview_text.setPlainText("无法预览此文档类型")
                
        except Exception as e:
            logger.error(f"预览文档内容时出错: {e}")
            self.preview_text.setPlainText(f"预览出错: {str(e)}")
    
    def get_document_path(self) -> str:
        """
        获取文档路径
        
        Returns:
            文档路径
        """
        return self.document_path