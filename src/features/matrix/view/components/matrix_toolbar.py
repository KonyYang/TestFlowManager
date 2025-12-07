# src/features/matrix/view/components/matrix_toolbar.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from src.core.logger import logger


class MatrixToolbar(QWidget):
    """Matrix工具栏组件 - 处理所有顶部按钮"""
    
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()
        
    def _setup_ui(self):
        """设置工具栏界面"""
        self.layout_ = QHBoxLayout()
        self.layout_.setSpacing(5)
        
        self.import_btn = QPushButton("导入Matrix")
        self.standardize_and_fill_btn = QPushButton("标准化填充Matrix")
        self.basic_info_btn = QPushButton("基本信息")
        self.generate_test_status_btn = QPushButton("生成Test Status")
        self.update_standard_versions_btn = QPushButton("更新标准版本")
        self.generate_test_record_btn = QPushButton("生成Test Record")
        
        self.layout_.addWidget(self.import_btn)
        self.layout_.addWidget(self.standardize_and_fill_btn)
        self.layout_.addWidget(self.update_standard_versions_btn)
        self.layout_.addWidget(self.basic_info_btn)
        self.layout_.addWidget(self.generate_test_status_btn)
        self.layout_.addWidget(self.generate_test_record_btn)
        
        self.layout_.addStretch()  # 添加弹性空间
        
    def layout(self):
        """返回工具栏的布局"""
        return self.layout_
        
    def connect_signals(self, handlers):
        """连接所有信号到处理函数"""
        self.import_btn.clicked.connect(handlers.on_import_clicked)
        self.standardize_and_fill_btn.clicked.connect(handlers.on_standardize_and_fill_clicked)
        self.basic_info_btn.clicked.connect(handlers.on_show_basic_info_dialog)
        self.generate_test_status_btn.clicked.connect(handlers.on_export_clicked)
        self.update_standard_versions_btn.clicked.connect(handlers.on_update_standards_clicked)
        self.generate_test_record_btn.clicked.connect(handlers.on_generate_test_record_clicked)