from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
from src.core.logger import logger


class ExportDialog(LimsDialogBase):
    """导出对话框 - View层"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_export_type = None
        self.setWindowTitle("选择导出类型")
        self.setModal(True)
        self.resize(300, 150)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        
        # 导出类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("导出类型:"))
        self.type_combo = QComboBox()
        # 添加各种导出类型选项
        self.type_combo.addItem("Matrix Excel", "matrix_excel")
        self.type_combo.addItem("Test Status表", "test_status")
        self.type_combo.addItem("LLCR", "llcr")
        self.type_combo.addItem("CR", "cr")
        self.type_combo.addItem("Mating/Unmating", "mating_unmating")
        self.type_combo.addItem("IR&DWV", "ir_dwv")
        self.type_combo.setCurrentIndex(0)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _on_type_changed(self, index):
        """处理导出类型变化"""
        self.selected_export_type = self.type_combo.currentData()
        
    def _on_ok_clicked(self):
        """处理确定按钮点击事件"""
        self.selected_export_type = self.type_combo.currentData()
        self.accept()
        
    def get_selected_export_type(self):
        """获取选择的导出类型"""
        return self.selected_export_type