# src/features/test_record_generator/view/test_record_dialog.py
"""
Test Record生成对话框
提供用户界面用于生成Test Record文档
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFileDialog, QMessageBox)
from src.core.logger import logger


class TestRecordDialog(QDialog):
    """
    Test Record生成对话框
    """

    def __init__(self, parent=None, default_output_path=None):
        super().__init__(parent)
        self.setWindowTitle("生成Test Record")
        self.setGeometry(200, 200, 400, 150)
        
        self.output_path = ""
        self.default_output_path = default_output_path
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # 输出路径选择
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("输出路径:"))
        
        self.path_edit = QLineEdit()
        # 如果提供了默认路径，则设置为默认路径
        if self.default_output_path:
            self.path_edit.setText(self.default_output_path)
            self.output_path = self.default_output_path
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_output_path)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def _browse_output_path(self):
        """浏览输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存Test Record文档", 
            self.path_edit.text() if self.path_edit.text() else "", 
            "Word文档 (*.docx)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
            self.output_path = file_path

    def get_output_path(self):
        """获取输出路径"""
        # 如果用户没有选择路径，则使用默认路径
        if not self.output_path and self.default_output_path:
            return self.default_output_path
        return self.output_path