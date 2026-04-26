# src/features/matrix/view/matrix_filter_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt
from src.shell.main_window.view.lims_dialog_base import LimsDialogBase


class MatrixFilterDialog(LimsDialogBase):
    """Matrix筛选对话框 - 用于导入时筛选特定页码和关键字的表格
    
    注意：当目标文档已在Word/Excel中打开时，系统将以只读方式访问文档内容，
    不会影响用户正在进行的编辑工作。
    """
    
    def __init__(self, parent=None, page_number=8, keyword="test"):
        super().__init__(title="筛选表格", parent=parent)
        self.setModal(True)
        self.resize(300, 150)
        
        self.page_number = page_number
        self.keyword = keyword
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        
        # 页码输入（改为可输入数字的方式）
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("页码:"))
        self.page_line_edit = QLineEdit()
        self.page_line_edit.setText(str(self.page_number))
        # 设置只能输入非0的正整数
        validator = QIntValidator(1, 9999)
        validator.setRange(1, 9999)  # 明确设置范围
        self.page_line_edit.setValidator(validator)
        page_layout.addWidget(self.page_line_edit)
        layout.addLayout(page_layout)
        
        # 关键字输入
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("关键字:"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setText(self.keyword)
        keyword_layout.addWidget(self.keyword_edit)
        layout.addLayout(keyword_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("btn_secondary")
        
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_filter_params(self):
        """获取筛选参数"""
        # 获取页码，确保是有效数字
        page_text = self.page_line_edit.text()
        page_number = 8  # 默认值改为8
        if page_text.isdigit() and int(page_text) > 0:
            page_number = int(page_text)
        
        return {
            'page': page_number,
            'keyword': self.keyword_edit.text() if self.keyword_edit.text() else "test"  # 默认关键字改为"test"
        }
        
    def _on_ok_clicked(self):
        """处理确定按钮点击事件"""
        # 检查页码是否为空
        if not self.page_line_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "页码不能为空，请输入有效的页码。")
            return
            
        # 检查关键字是否为空
        if not self.keyword_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "关键字不能为空，请输入有效的关键字。")
            return
            
        # 检查页码是否为有效数字
        page_text = self.page_line_edit.text()
        if not (page_text.isdigit() and int(page_text) > 0):
            QMessageBox.warning(self, "输入错误", "页码必须是大于0的整数。")
            return
        
        # 所有验证通过，接受对话框
        self.accept()