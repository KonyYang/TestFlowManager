"""
工具操作处理器
处理工具箱相关的动作
"""

from typing import Any
from PyQt5.QtWidgets import QFileDialog

from src.core.logger import logger


class ToolActionHandlers:
    """工具操作动作处理器"""

    def __init__(self, main_window: Any):
        self._main_window = main_window

    def on_edit_body_content(self) -> None:
        """正文内容编辑"""
        logger.debug("Edit body content action triggered")
        file_path, _ = QFileDialog.getOpenFileName(
            self._main_window, "选择 Word 文档", "", "Word 文档 (*.doc *.docx)"
        )
        if file_path:
            logger.info(f"用户选择了文件：{file_path}")
            self._main_window._feature_registry.run_edit_body_content(file_path)
        else:
            logger.info("用户取消了文件选择")
        self._update_status()

    def on_encrypt_test_files(self) -> None:
        """测试文件加密"""
        logger.debug("Encrypt test files action triggered")
        try:
            self._main_window._feature_registry.run_encrypt_test_files()
            self._update_status()
        except Exception as e:
            logger.error(f"加密功能执行失败：{e}", exc_info=True)

    def on_open_isolated_matrix_preview(self) -> None:
        """Pilot: 打开隔离 Matrix 预览 session"""
        logger.debug("Open isolated matrix preview pilot action triggered")
        if self._main_window._workspace_facade:
            session_id = self._main_window._workspace_facade.open_preview_pilot()
            if session_id:
                self._update_status()

    def on_close_isolated_matrix_preview(self) -> None:
        """Pilot: 关闭隔离 Matrix 预览 session"""
        logger.debug("Close isolated matrix preview pilot action triggered")
        if self._main_window._workspace_facade:
            if self._main_window._workspace_facade.close_preview_pilot():
                self._update_status()

    def _update_status(self) -> None:
        """更新状态栏"""
        self._main_window._update_status()
