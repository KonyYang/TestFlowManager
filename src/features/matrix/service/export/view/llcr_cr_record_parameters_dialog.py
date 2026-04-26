from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QCheckBox, QLabel, QSpinBox, QListWidget, QListWidgetItem, QMessageBox, QTextEdit
from PyQt5.QtCore import Qt
from src.core.logger import logger
from src.shell.main_window.view.lims_dialog_base import LimsDialogBase
from src.utils.smart_point_parser import SmartPointParser


class LLCR_CR_RecordParametersDialog(QDialog):
    """LLCR/CR记录参数输入对话框 - View层"""
    
    def __init__(self, parent=None, test_type="LLCR", default_points=None, test_category_dict=None):
        super().__init__(parent)
        self.test_type = test_type
        self.point_array = []
        self.sample_count = 5
        self.is_delta_r_checked = False
        self.cr_current_value = ""
        self.default_points = default_points or []
        self.test_category_dict = test_category_dict or {}
        
        self.setWindowTitle(f"{test_type} 参数设置")
        self.setModal(True)
        self.resize(500, 400)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # 设置主布局左对齐
        
        # 测试点位输入框
        point_layout = QVBoxLayout()
        point_label = QLabel("输入测试点位 (支持格式如: 1-8;P1-P3;Hp1-Hp5,Hp7;A,B)\n\n"
            "- 范围: 1-5 展开为 [1,2,3,4,5]\n"
            "- 步长: 1-10:2 展开为 [1,3,5,7,9]\n"
            "- 排除: 1-5!3 展开为 [1,2,4,5]\n"
            "- 分组: 使用分号';'分隔不同组别，使用逗号','分隔同组点位")
        point_label.setAlignment(Qt.AlignLeft)  # 确保标签左对齐
        point_layout.addWidget(point_label)
        self.point_input = QTextEdit()
        self.point_input.setMaximumHeight(60)
        point_layout.addWidget(self.point_input)
        point_layout.setAlignment(Qt.AlignLeft)  # 设置点位布局左对齐
        
        layout.addLayout(point_layout)
        
        # 样本数量和ΔR计算选项
        sample_layout = QHBoxLayout()
        sample_layout.setAlignment(Qt.AlignLeft)  # 设置样本数量布局左对齐
        # 调整标签和输入框间距
        label = QLabel("样本数量")
        label.setFixedWidth(100)  # 设置标签固定宽度
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 标签右对齐，垂直居中
        sample_layout.addWidget(label)
        self.sample_spinbox = QSpinBox()
        self.sample_spinbox.setMinimum(1)
        self.sample_spinbox.setMaximum(50)
        self.sample_spinbox.setValue(5)
        self.sample_spinbox.setMaximumWidth(80)  # 缩短50%的宽度
        sample_layout.addWidget(self.sample_spinbox)
        
        # ΔR 计算选项 (仅对LLCR有效)
        if self.test_type == "LLCR":
            self.delta_r_checkbox = QCheckBox("计算 ΔR")
            self.delta_r_checkbox.setChecked(True)  # 默认勾选
            sample_layout.addWidget(self.delta_r_checkbox)
        
        layout.addLayout(sample_layout)
        
        # CR电流值输入 (仅对CR有效)
        if self.test_type == "CR":
            # 添加到样本数量行
            # 调整标签和输入框间距
            label = QLabel("CR电流(A)")
            label.setFixedWidth(120)  # 增加标签宽度以适应更长的文本
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 标签右对齐，垂直居中
            sample_layout.addWidget(label)
            self.cr_current_input = QLineEdit()
            self.cr_current_input.setText("1.0")
            self.cr_current_input.setMaximumWidth(100)  # 缩短70%的宽度
            sample_layout.addWidget(self.cr_current_input)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)  # 按钮右对齐
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("btn_secondary")
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 初始化测试点位
        self._init_points()
        
    def _init_points(self):
        """初始化测试点位"""
        # 始终使用默认的"P1"点位，不再从Matrix数据中提取
        self._init_default_points()
        
        # 设置焦点和光标位置
        self.point_input.setFocus()
        cursor = self.point_input.textCursor()
        cursor.movePosition(cursor.End)
        self.point_input.setTextCursor(cursor)
        
    def _init_default_points(self):
        """初始化默认测试点位"""
        default_points = ["P1"]
        point_text = ", ".join(default_points)
        self.point_input.setPlainText(point_text)
        
        # 设置光标位置在"P1"之后
        cursor = self.point_input.textCursor()
        cursor.movePosition(cursor.End)
        self.point_input.setTextCursor(cursor)
        
    def _validate_cr_current(self, value):
        """验证CR电流值"""
        if not value:
            return False, "电流值不能为空"
            
        try:
            float_value = float(value)
            if float_value <= 0:
                return False, "电流值必须大于0"
            # 检查是否全为0（包括0.000这样的形式）
            if float_value == 0.0:
                return False, "电流值不能为0或0.0"
            return True, ""
        except ValueError:
            return False, "请输入有效的数字"
            
    def _on_ok_clicked(self):
        """处理确定按钮点击事件"""
        # 获取测试点位
        point_text = self.point_input.toPlainText().strip()
        
        if not point_text:
            QMessageBox.warning(self, "警告", "请输入测试点位")
            return
            
        # 使用智能解析器解析点位
        parser = SmartPointParser()
        try:
            result = parser.parse(point_text)
            
            # 检查是否有解析错误
            if result['statistics']['parsing_errors']:
                error_msg = "\n".join(result['statistics']['parsing_errors'])
                QMessageBox.warning(self, "解析错误", f"点位解析出现以下错误:\n{error_msg}")
                return
                
            # 合并所有点位
            self.point_array = []
            for points in result['categories'].values():
                self.point_array.extend(points)
                
            # 去重但保持顺序
            unique_points = []
            for point in self.point_array:
                if point not in unique_points:
                    unique_points.append(point)
            self.point_array = unique_points
            
        except Exception as e:
            QMessageBox.warning(self, "解析错误", f"点位解析失败:\n{str(e)}")
            return
            
        if not self.point_array:
            QMessageBox.warning(self, "警告", "请至少添加一个测试点位")
            return
            
        # 获取样本数量
        self.sample_count = self.sample_spinbox.value()
        
        # 获取ΔR选项
        if self.test_type == "LLCR":
            self.is_delta_r_checked = self.delta_r_checkbox.isChecked()
            
        # 获取CR电流值并验证
        if self.test_type == "CR":
            self.cr_current_value = self.cr_current_input.text().strip()
            is_valid, error_msg = self._validate_cr_current(self.cr_current_value)
            if not is_valid:
                QMessageBox.warning(self, "输入错误", error_msg)
                return
            
        self.accept()
        
    def get_parameters(self):
        """获取用户输入的参数"""
        return {
            "point_array": self.point_array,
            "sample_count": self.sample_count,
            "is_delta_r_checked": self.is_delta_r_checked,
            "cr_current_value": self.cr_current_value
        }
        
    def set_import_callback(self, callback):
        """设置导入点位的回调函数"""
        self.import_callback = callback
        # 更新导入按钮的连接
        try:
            self.import_points_button.clicked.disconnect()
        except TypeError:
            # 如果之前没有连接过信号，则忽略异常
            pass
        self.import_points_button.clicked.connect(self._execute_import_callback)
        
    def _execute_import_callback(self):
        """执行导入回调"""
        if hasattr(self, 'import_callback') and self.import_callback:
            points = self.import_callback()
            if points:
                # 清空现有点位
                self.point_list.clear()
                self.point_array = []
                
                # 添加新点位
                for point in points:
                    item = QListWidgetItem(str(point))
                    self.point_list.addItem(item)
                    self.point_array.append(str(point))
        else:
            QMessageBox.information(self, "提示", "未设置导入功能")