"""
自定义对话框控件模块
提供通用的自定义对话框
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from src.core.logger import logger


class CustomDialog(QDialog):
    """
    自定义对话框类
    提供可定制的对话框功能
    """

    def __init__(self, parent=None):
        """
        初始化自定义对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        self.setWindowTitle("自定义对话框")
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout()

        # 标题标签
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # 内容标签
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setWordWrap(True)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(self.title_label)
        layout.addWidget(self.content_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def set_title(self, title: str) -> None:
        """
        设置对话框标题

        Args:
            title: 标题文本
        """
        self.title_label.setText(title)
        self.setWindowTitle(title)

    def set_content(self, content: str) -> None:
        """
        设置对话框内容

        Args:
            content: 内容文本
        """
        self.content_label.setText(content)

    def set_buttons(self, ok_text: str = "确定", cancel_text: str = "取消") -> None:
        """
        设置按钮文本

        Args:
            ok_text: 确定按钮文本
            cancel_text: 取消按钮文本
        """
        self.ok_button.setText(ok_text)
        self.cancel_button.setText(cancel_text)

    def hide_cancel_button(self) -> None:
        """隐藏取消按钮"""
        self.cancel_button.hide()

    def show_cancel_button(self) -> None:
        """显示取消按钮"""
        self.cancel_button.show()


class InfoDialog(CustomDialog):
    """
    信息对话框类
    用于显示信息提示
    """

    def __init__(self, parent=None, title: str = "信息", message: str = ""):
        """
        初始化信息对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 信息内容
        """
        super().__init__(parent)
        self.set_title(title)
        self.set_content(message)
        self.hide_cancel_button()
        self.set_buttons("确定")


class ConfirmDialog(CustomDialog):
    """
    确认对话框类
    用于显示确认提示
    """

    def __init__(self, parent=None, title: str = "确认", message: str = ""):
        """
        初始化确认对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 确认内容
        """
        super().__init__(parent)
        self.set_title(title)
        self.set_content(message)
        self.set_buttons("确定", "取消")
