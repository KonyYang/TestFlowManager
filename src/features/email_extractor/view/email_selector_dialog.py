"""
邮件选择对话框模块
提供一个简单的对话框用于选择单个.msg邮件文件或拖拽邮件
"""

import os
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QLabel, QFileDialog, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from src.core.logger import logger
from src.common.ui.font_utils import FontUtils  # 导入字体工具类
from src.common.ui.window_utils import WindowUtils  # 导入窗口工具类
from src.shell.main_window.view.lims_dialog_base import LimsDialogBase


class EmailSelectorDialog(LimsDialogBase):
    """
    邮件选择对话框类
    用于选择单个.msg邮件文件或拖拽邮件
    """

    msg_file_selected = pyqtSignal(str)  # MSG文件选中信号

    def __init__(self, parent=None):
        """
        初始化邮件选择对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.selected_msg_file = None
        self.temp_folder = None  # 用于存储临时文件夹路径
        self.is_reselect_mode = False  # 标志：是否为重新选择附件模式

        # 启用拖拽
        self.setAcceptDrops(True)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("选择邮件文件")
        self.setModal(True)
        # 根据DPI调整窗口尺寸，使用更合适的默认尺寸
        width, height = WindowUtils.get_scaled_window_size(800, 600)  # 增加窗口尺寸
        self.resize(width, height)

        layout = QVBoxLayout()

        # 文件选择区域
        file_select_layout = QHBoxLayout()
        # 使用动态字体，减小基础字号以适应不同DPI设置
        font = FontUtils.get_scaled_font(9)  # 减小基础字号从10到9

        self.select_msg_file_button = QPushButton("选择.msg邮件文件")
        self.select_msg_file_button.setFont(font)

        self.drop_info_label = QLabel("或将.msg邮件文件拖拽到此对话框")
        self.drop_info_label.setFont(font)

        file_select_layout.addWidget(self.select_msg_file_button)
        file_select_layout.addWidget(self.drop_info_label)
        file_select_layout.addStretch()

        # 邮件信息显示
        self.email_info_label = QLabel("未选择邮件")
        self.email_info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.email_info_label.setStyleSheet("""
            font-weight: bold;
            color: #1a3a5c;
            background-color: #e3f2fd;
            padding: 8px;
            border-radius: 4px;
        """)
        # 根据DPI调整高度，使用较小的固定高度
        label_height = WindowUtils.get_scaled_size(60)  # 减小高度从70到60
        self.email_info_label.setFixedHeight(label_height)
        self.email_info_label.setWordWrap(True)
        self.email_info_label.setFont(font)

        # 附件列表
        self.attachment_label = QLabel("附件列表:")
        self.attachment_label.setFont(font)

        # 附件表格
        self.attachment_table = QTableWidget()
        self.attachment_table.setColumnCount(2)
        self.attachment_table.setHorizontalHeaderLabels(["文件名", "大小"])
        self.attachment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attachment_table.setSelectionMode(QTableWidget.SingleSelection)
        # 根据DPI调整最小高度，减小高度以适应整体布局
        min_height = WindowUtils.get_scaled_size(120)  # 减小最小高度从150到120
        self.attachment_table.setMinimumHeight(min_height)
        self.attachment_table.setFont(font)

        # 👇 新增：设置表头字体
        header = self.attachment_table.horizontalHeader()
        header.setFont(font)  # 关键！否则表头字体不会变大

        # 启用双击事件
        self.attachment_table.doubleClicked.connect(self._preview_attachment)

        # 设置列宽策略
        header = self.attachment_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.select_button = QPushButton("申请LTR编号")
        self.select_button.setEnabled(False)
        self.select_button.setFont(font)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFont(font)

        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)

        # 添加到主布局
        layout.addLayout(file_select_layout)
        layout.addWidget(self.email_info_label)
        layout.addWidget(self.attachment_label)
        layout.addWidget(self.attachment_table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 初始化记录当前选中的附件索引
        self.selected_attachment_index = None

    def _connect_signals(self):
        """连接信号和槽"""
        self.select_msg_file_button.clicked.connect(self._on_select_msg_file)
        self.select_button.clicked.connect(self._on_apply_for_ltr)
        self.cancel_button.clicked.connect(self.reject)
        # 连接附件表格的选择变化信号
        self.attachment_table.itemSelectionChanged.connect(self._on_attachment_selection_changed)

    def _on_select_msg_file(self):
        """选择MSG文件按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择邮件文件",
            "",
            "Outlook邮件文件 (*.msg)"
        )

        if file_path:
            self._handle_msg_file_selected(file_path)

    def _on_apply_for_ltr(self):
        """申请LTR编号按钮点击事件"""
        logger.debug("Apply for LTR button clicked")
        # 直接关闭对话框，返回Accepted结果
        # 邮件处理和附件提取已在用户选择或拖拽.msg文件时完成
        logger.debug("Accepting email selector dialog")
        self.accept()

    def _on_attachment_selection_changed(self):
        """附件选择变化事件"""
        selected_items = self.attachment_table.selectedItems()
        if selected_items:
            # 记录当前选中的附件行索引
            self.selected_attachment_index = selected_items[0].row()
        else:
            self.selected_attachment_index = None

    def get_selected_attachment(self):
        """获取当前选中的附件"""
        if self.selected_attachment_index is not None and hasattr(self, '_current_attachments'):
            attachments = self._current_attachments
            if 0 <= self.selected_attachment_index < len(attachments):
                return attachments[self.selected_attachment_index]
        return None  # 明确返回None

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.msg'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.msg'):
                    # 发射信号让控制器处理文件选择
                    self.msg_file_selected.emit(file_path)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def _handle_msg_file_selected(self, file_path):
        """处理选中的MSG文件"""
        # 在处理新邮件前，清空之前的选择
        self.clear_selection()
        
        self.selected_msg_file = file_path
        self.select_button.setEnabled(True)

        # 发射信号让控制器处理文件并更新界面
        self.msg_file_selected.emit(file_path)

    def update_email_info(self, info_text, attachments=None):
        """
        更新邮件信息显示

        Args:
            info_text: 邮件信息文本
            attachments: 附件列表
        """
        self.email_info_label.setText(info_text)

        if attachments is not None:
            # 更新附件列表显示
            self._current_attachments = attachments
            self.attachment_table.setRowCount(len(attachments))

            for row, attachment in enumerate(attachments):
                # 文件名
                filename_item = QTableWidgetItem(attachment.get('filename', ''))
                filename_item.setFlags(filename_item.flags() & ~Qt.ItemIsEditable)
                self.attachment_table.setItem(row, 0, filename_item)

                # 大小
                size = attachment.get('size', 0)
                size_str = self._format_file_size(size)
                size_item = QTableWidgetItem(size_str)
                size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
                self.attachment_table.setItem(row, 1, size_item)

            self.attachment_table.resizeRowsToContents()

            if attachments:
                self.attachment_label.setText(f"附件列表 (共 {len(attachments)} 个附件):")
            else:
                self.attachment_label.setText("附件列表 (无附件)")

    def set_email_context(self, email_info, attachments, msg_file_path):
        """
        设置邮件上下文信息，用于重新选择附件

        Args:
            email_info: 邮件信息文本
            attachments: 附件列表
            msg_file_path: 邮件文件路径
        """
        # 设置为重新选择附件模式
        self.is_reselect_mode = True
        
        self.email_info_label.setText(email_info)
        self._current_attachments = attachments
        self.selected_msg_file = msg_file_path

        # 更新附件列表显示
        self.attachment_table.setRowCount(len(attachments))
        for row, attachment in enumerate(attachments):
            # 文件名
            filename_item = QTableWidgetItem(attachment.get('filename', ''))
            filename_item.setFlags(filename_item.flags() & ~Qt.ItemIsEditable)
            self.attachment_table.setItem(row, 0, filename_item)

            # 大小
            size = attachment.get('size', 0)
            size_str = self._format_file_size(size)
            size_item = QTableWidgetItem(size_str)
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
            self.attachment_table.setItem(row, 1, size_item)

        self.attachment_table.resizeRowsToContents()

        if attachments:
            self.attachment_label.setText(f"附件列表 (共 {len(attachments)} 个附件):")
        else:
            self.attachment_label.setText("附件列表 (无附件)")

        # 启用"申请LTR编号"按钮
        self.select_button.setEnabled(True)

    def _preview_attachment(self, index):
        """预览附件"""
        try:
            from src.utils.file_utils import get_file_extension
            row = index.row()
            attachments = self._get_current_attachments()

            if not attachments or row >= len(attachments):
                return

            attachment = attachments[row]
            filename = attachment.get('filename', '')

            # 创建临时文件
            import tempfile
            temp_dir = tempfile.gettempdir()
            logger.info(f"[EmailSelectorDialog] 预览附件使用临时目录: {temp_dir}")
            temp_file_path = os.path.join(temp_dir, filename)
            logger.info(f"[EmailSelectorDialog] 预览附件临时文件路径: {temp_file_path}")

            # 写入附件数据到临时文件
            content = attachment.get('content')
            if content:
                with open(temp_file_path, 'wb') as f:
                    f.write(content)

                # 根据文件类型选择打开方式
                self._open_file_by_type(temp_file_path)
            else:
                QMessageBox.warning(self, "警告", "附件内容为空，无法预览")

        except Exception as e:
            logger.error(f"预览附件时出错: {e}")
            QMessageBox.warning(self, "警告", f"无法预览附件: {str(e)}")

    def _get_current_attachments(self):
        """获取当前邮件的附件列表"""
        # 这里需要通过控制器获取当前邮件数据
        # 由于视图层无法直接访问控制器，我们需要通过信号传递或数据模型
        try:
            from src.features.email_extractor.controller.email_extractor_controller import EmailExtractorController
            # 获取当前附件数据（需要在控制器中设置）
            if hasattr(self, '_current_attachments'):
                return self._current_attachments
        except:
            pass
        return []

    def _open_file_by_type(self, file_path):
        """根据文件类型打开文件"""
        try:
            import platform
            import subprocess
            import os

            system = platform.system()

            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])
        except Exception as e:
            logger.error(f"打开文件时出错: {e}")
            QMessageBox.warning(self, "警告", f"无法打开文件: {str(e)}")

    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def clear_selection(self):
        """清空选择"""
        self.selected_msg_file = None
        self.email_info_label.setText("未选择邮件")
        self.attachment_table.setRowCount(0)
        self.select_button.setEnabled(False)
        
        # 清空附件列表
        if hasattr(self, '_current_attachments'):
            self._current_attachments = []