"""
LTR编号输入对话框模块
提供LTR编号输入和验证功能
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtCore import Qt
from src.common.ui.font_utils import FontUtils
from src.core.logger import logger


class LTRNumberInputDialog(QDialog):
    """
    LTR编号输入对话框类
    提供LTR编号输入和验证功能
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dl_number = None
        self._setup_ui()

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("输入DL编号")
        self.setModal(True)
        global_font = FontUtils.get_scaled_font(9)
        self.setFont(global_font)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.dl_input = QLineEdit()
        self.dl_input.setPlaceholderText("请输入完整DL编号如：DL-2025-01-001")
        self.dl_input.setFont(FontUtils.get_scaled_font(9))
        self.dl_input.returnPressed.connect(self._on_confirm)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self._on_confirm)
        self.confirm_button.setDefault(True)
        self.confirm_button.setFont(FontUtils.get_scaled_font(8))
        self.confirm_button.setEnabled(False)

        self.skip_button = QPushButton("跳过")
        self.skip_button.clicked.connect(self._on_skip)
        self.skip_button.setFont(FontUtils.get_scaled_font(8))

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFont(FontUtils.get_scaled_font(8))

        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(self.dl_input)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.dl_input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text):
        """处理输入框文本变化"""
        self.confirm_button.setEnabled(len(text.strip()) > 0)

    def _on_confirm(self):
        """处理确认按钮点击"""
        dl_number = self.dl_input.text().strip()
        if dl_number:
            self.dl_number = dl_number
            self.accept()

    def _on_skip(self):
        """处理跳过按钮点击"""
        self.dl_number = None
        self.accept()

    def get_dl_number(self):
        """
        获取DL编号

        Returns:
            str: DL编号或None（如果用户选择跳过）
        """
        return self.dl_number
