"""
报告更新模块对话框
实现报告更新功能的用户界面
"""
import os
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QListWidget, QLabel, QGroupBox, 
                             QComboBox, QFileDialog, QMessageBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from src.core.logger import logger
from src.shell.main_window.view.lims_dialog_base import LimsDialogBase
from src.common.ui.font_utils import FontUtils
from src.features.report_updater.model.report_updater_data import ReportUpdaterData


class ReportUpdaterDialog(LimsDialogBase):
    """报告更新功能的对话框类"""
    
    # 定义信号
    equipment_update_requested = pyqtSignal()  # 设备更新请求信号
    
    def __init__(self, data_model: ReportUpdaterData, parent=None, selected_report=None):
        """
        初始化报告更新对话框

        Args:
            data_model: 数据模型实例
            parent: 父窗口
            selected_report: 已选择的报告文件路径
        """
        window_title = f"报告更新 - {os.path.basename(selected_report) if selected_report else '未选择报告'}"
        super().__init__(title=window_title, parent=parent)
        self.data_model = data_model
        self.parent = parent
        self.selected_report = selected_report  # 已选择的报告文件
        
        self.setMinimumSize(500, 350)
        self.resize(800, 400)
        
        # 应用全局字体
        global_font = FontUtils.get_scaled_font(9)
        self.setFont(global_font)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        
        # 创建按钮网格布局
        button_grid_layout = QGridLayout()
        
        # 更新设备列表按钮 - 位于第0行第0列
        self.update_equipment_btn = QPushButton("更新设备列表")
        self.update_equipment_btn.setFixedWidth(150)  # 设置固定宽度
        self.update_equipment_btn.clicked.connect(self.on_update_equipment_clicked)
        button_grid_layout.addWidget(self.update_equipment_btn, 0, 0)  # 行0，列0
        
        # 预留更多按钮的位置
        # 示例：button_grid_layout.addWidget(new_button, row, col)
        
        # 设置网格布局对齐方式为靠上靠左
        button_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addLayout(button_grid_layout)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def on_update_equipment_clicked(self):
        """处理更新设备列表按钮点击事件"""
        logger.debug("Update equipment button clicked")
        
        # 发射信号让控制器处理
        self.equipment_update_requested.emit()