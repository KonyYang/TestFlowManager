"""
正文内容编辑对话框视图
提供交互式编辑Word文档正文内容的界面
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTextEdit, QListWidget, QListWidgetItem, QPushButton, 
    QLabel, QGroupBox, QFormLayout, QFrame, QScrollArea
)
from PyQt5.QtCore import pyqtSignal
from src.core.logger import logger
from src.features.document_parser.service.body_content_service import BodyContentService
from src.features.document_parser.utils.document_editor_mixin import DocumentEditorMixin


class BodyContentDialog(QDialog, DocumentEditorMixin):
    """
    正文内容编辑对话框
    提供交互式编辑Word文档正文内容的界面
    """
    
    # 自定义信号
    content_updated = pyqtSignal(dict)  # 传递更新的内容字典
    
    def __init__(self, file_path: str, parent=None):
        """
        初始化正文内容编辑对话框

        Args:
            file_path: Word文档路径
            parent: 父窗口
        """
        super().__init__(parent)
        self._init_document_editor_components(file_path)  # 初始化混入类组件
        
        self.setWindowTitle("正文内容编辑")
        self.setGeometry(200, 200, 1200, 800)
        
        # 初始化UI
        self.init_ui()
        
        # 加载文档内容
        self.load_document_content()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(f"编辑文档: {self.file_path}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建分割窗口
        splitter = QSplitter()
        
        # 左侧：内容编辑区域（分上下两部分）
        left_widget = self._create_content_edit_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：预设描述区域（分上下两部分）
        right_widget = self._create_preset_panel()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([600, 600])  # 设置初始大小
        main_layout.addWidget(splitter)
        
        # 按钮区域
        button_layout = self._create_buttons()
        # 连接取消按钮信号
        for i in reversed(range(button_layout.count())):
            item = button_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QPushButton) and item.widget().text() == "取消":
                item.widget().clicked.connect(self.reject)
                break
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 连接其他信号
        self._connect_common_signals()