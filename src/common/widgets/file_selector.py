"""
文件选择器控件模块
提供文件选择功能的自定义控件
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal
from src.core.logger import logger


class FileSelector(QWidget):
    """
    文件选择器控件
    提供文件路径输入和浏览功能
    """

    # 文件路径改变信号
    pathChanged = pyqtSignal(str)

    def __init__(self, parent=None, file_filter: str = "All Files (*)"):
        """
        初始化文件选择器

        Args:
            parent: 父窗口
            file_filter: 文件过滤器，如 "Text Files (*.txt)"
        """
        super().__init__(parent)
        self.file_filter = file_filter
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 文件路径输入框
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择文件...")
        self.path_edit.textChanged.connect(self._on_path_changed)

        # 浏览按钮
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)

        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)

        self.setLayout(layout)

    def _browse_file(self) -> None:
        """浏览文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", self.file_filter
            )
            if file_path:
                self.set_path(file_path)
        except Exception as e:
            logger.error(f"Failed to browse file: {e}")

    def _on_path_changed(self, path: str) -> None:
        """路径改变时的处理"""
        self.pathChanged.emit(path)

    def set_path(self, path: str) -> None:
        """
        设置文件路径

        Args:
            path: 文件路径
        """
        self.path_edit.setText(path)

    def get_path(self) -> str:
        """
        获取文件路径

        Returns:
            当前文件路径
        """
        return self.path_edit.text()

    def set_file_filter(self, file_filter: str) -> None:
        """
        设置文件过滤器

        Args:
            file_filter: 文件过滤器
        """
        self.file_filter = file_filter


class DirectorySelector(QWidget):
    """
    目录选择器控件
    提供目录路径输入和浏览功能
    """

    # 目录路径改变信号
    pathChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        初始化目录选择器

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 目录路径输入框
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择目录...")
        self.path_edit.textChanged.connect(self._on_path_changed)

        # 浏览按钮
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_directory)

        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)

        self.setLayout(layout)

    def _browse_directory(self) -> None:
        """浏览目录"""
        try:
            directory = QFileDialog.getExistingDirectory(self, "选择目录")
            if directory:
                self.set_path(directory)
        except Exception as e:
            logger.error(f"Failed to browse directory: {e}")

    def _on_path_changed(self, path: str) -> None:
        """路径改变时的处理"""
        self.pathChanged.emit(path)

    def set_path(self, path: str) -> None:
        """
        设置目录路径

        Args:
            path: 目录路径
        """
        self.path_edit.setText(path)

    def get_path(self) -> str:
        """
        获取目录路径

        Returns:
            当前目录路径
        """
        return self.path_edit.text()
