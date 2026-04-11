# src/features/matrix/view/components/matrix_toolbar.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PyQt5.QtCore import Qt
from src.core.logger import logger


class MatrixToolbar(QWidget):
    """Matrix工具栏组件 - 处理所有顶部按钮（现代化样式）"""
    
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()
        
    def _setup_ui(self):
        """设置工具栏界面"""
        # 工具栏容器
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("MatrixToolbarFrame")
        toolbar_frame.setStyleSheet("""
            QFrame#MatrixToolbarFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f7fafc, stop:1 #edf2f7);
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 12px;
            }
        """)
        
        main_layout = QHBoxLayout(toolbar_frame)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)
        
        # 定义按钮样式 - 大字体版本（高分辨率屏幕优化）
        button_style = """
            QPushButton {
                background: white;
                color: #4a5568;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #edf2f7;
                border-color: #cbd5e0;
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
        """
        
        primary_button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4299e1, stop:1 #3182ce);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3182ce, stop:1 #2b6cb0);
            }
            QPushButton:pressed {
                background: #2b6cb0;
            }
        """
        
        # 导入按钮（主要操作）
        self.import_btn = QPushButton("📥 导入Matrix")
        self.import_btn.setStyleSheet(primary_button_style)
        
        # 标准化填充按钮（主要操作）
        self.standardize_and_fill_btn = QPushButton("✨ 标准化填充")
        self.standardize_and_fill_btn.setStyleSheet(primary_button_style)
        
        # 更新标准版本
        self.update_standard_versions_btn = QPushButton("🔄 更新标准版本")
        self.update_standard_versions_btn.setStyleSheet(button_style)
        
        # 基本信息
        self.basic_info_btn = QPushButton("ℹ️ 基本信息")
        self.basic_info_btn.setStyleSheet(button_style)
        
        # 生成Test Status
        self.generate_test_status_btn = QPushButton("📊 生成Test Status")
        self.generate_test_status_btn.setStyleSheet(button_style)
        
        # 生成Step Record
        self.generate_step_record_btn = QPushButton("📝 生成Step Record")
        self.generate_step_record_btn.setStyleSheet(button_style)
        
        # 生成费用表
        self.generate_cost_sheet_btn = QPushButton("💰 费用表")
        self.generate_cost_sheet_btn.setStyleSheet(button_style)
        
        # 添加到布局
        main_layout.addWidget(self.import_btn)
        main_layout.addWidget(self.standardize_and_fill_btn)
        main_layout.addWidget(self.update_standard_versions_btn)
        main_layout.addWidget(self.basic_info_btn)
        main_layout.addWidget(self.generate_test_status_btn)
        main_layout.addWidget(self.generate_step_record_btn)
        main_layout.addWidget(self.generate_cost_sheet_btn)
        main_layout.addStretch()
        
        # 保存布局引用
        self._toolbar_frame = toolbar_frame
        self._main_layout = main_layout
        
    def layout(self):
        """返回工具栏的布局"""
        return self._main_layout
    
    def get_widget(self):
        """返回工具栏主控件"""
        return self._toolbar_frame
        
    def connect_signals(self, handlers):
        """连接所有信号到处理函数"""
        self.import_btn.clicked.connect(handlers.on_import_clicked)
        self.standardize_and_fill_btn.clicked.connect(handlers.on_standardize_and_fill_clicked)
        self.basic_info_btn.clicked.connect(handlers.on_show_basic_info_dialog)
        self.generate_test_status_btn.clicked.connect(handlers.on_export_clicked)
        self.update_standard_versions_btn.clicked.connect(handlers.on_update_standards_clicked)
        self.generate_step_record_btn.clicked.connect(handlers.on_generate_step_record_clicked)
        self.generate_cost_sheet_btn.clicked.connect(handlers.on_generate_cost_sheet_clicked)