"""
DL编号输入对话框模块
提供一个对话框用于输入DL编号进行LTR查询
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import Qt
from src.core.logger import logger
import re


class DLInputDialog(QDialog):
    """
    DL编号输入对话框类
    用于询问用户是否输入指定DL编号进行查询
    """

    def __init__(self, parent=None):
        """
        初始化DL编号输入对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.dl_number = None
        self._setup_ui()
        self._setup_validation()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        self.setWindowTitle("查询指定DL编号信息")
        self.setModal(True)
        self.resize(400, 150)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 输入框
        self.dl_input = QLineEdit()
        self.dl_input.setPlaceholderText("请输入DL编号...")
        self.dl_input.returnPressed.connect(self._on_confirm)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self._on_confirm)
        self.confirm_button.setDefault(True)

        self.skip_button = QPushButton("跳过")
        self.skip_button.clicked.connect(self._on_skip)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(self.dl_input)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _setup_validation(self) -> None:
        """设置输入验证"""
        # 初始状态下禁用确认按钮
        self.confirm_button.setEnabled(False)

        # 连接输入框的文本变化信号
        self.dl_input.textChanged.connect(self._validate_input)

    def _validate_input(self, text: str) -> None:
        """验证输入的DL编号格式"""
        # 如果输入为空，禁用确认按钮
        if not text.strip():
            self.confirm_button.setEnabled(False)
            return

        # 验证DL编号基本格式 DL-XXXX-YY-ZZZ[后缀]
        match = re.match(r"DL-(\d{4})-(\d{2})-(\d{3})(.*)", text.strip())
        if match:
            year = int(match.group(1))
            # 验证年份合理性（2000年到当前年份+1）
            from datetime import datetime
            current_year = datetime.now().year
            if 2000 <= year <= current_year + 1:
                self.confirm_button.setEnabled(True)
                return

        self.confirm_button.setEnabled(False)

    def _on_confirm(self) -> None:
        """处理确认按钮点击事件"""
        dl_number = self.dl_input.text().strip()
        if dl_number:
            self.dl_number = dl_number
            self.accept()
        else:
            # 如果没有输入DL编号，则当作跳过处理
            self.dl_number = None
            self.accept()

    def _on_skip(self) -> None:
        """处理跳过按钮点击事件"""
        self.dl_number = None
        self.accept()

    def get_dl_number(self) -> str:
        """
        获取输入的DL编号

        Returns:
            输入的DL编号，如果选择跳过则返回None
        """
        return self.dl_number
