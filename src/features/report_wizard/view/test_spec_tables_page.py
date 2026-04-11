"""
Test spec tables page.
"""

from typing import List, Tuple

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.core.project_document_context import ProjectDocumentContext
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from src.features.report_wizard.service.test_spec_tables_service import TestSpecTablesService


def _build_matrix_data_structure(
    headers: List[str],
    rows: List[List[str]],
    project_context: ProjectContext = None,
) -> MatrixDataStructure:
    matrix_structure = MatrixDataStructure()
    document_context = ProjectDocumentContext.from_project_context(project_context)
    document_context.apply_to_matrix_data_structure(matrix_structure)
    matrix_structure.parse_matrix_to_structure(rows or [])
    return matrix_structure


class TestSpecTablesWorker(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, document_path, matrix_controller=None, project_context: ProjectContext = None):
        super().__init__()
        self.document_path = document_path
        self.matrix_controller = matrix_controller
        self.project_context = project_context
        headers, rows = self._resolve_matrix_table_data()
        self.matrix_headers = headers
        self.matrix_rows = rows
        self.matrix_data_structure = _build_matrix_data_structure(
            headers=headers,
            rows=rows,
            project_context=self._resolve_project_context(),
        )

    def _resolve_project_context(self):
        if self.project_context:
            return self.project_context
        if self.matrix_controller and hasattr(self.matrix_controller, "get_project_context"):
            return self.matrix_controller.get_project_context()
        return None

    def _resolve_matrix_table_data(self) -> Tuple[List[str], List[List[str]]]:
        if not self.matrix_controller:
            return [], []
        headers = (
            self.matrix_controller.get_matrix_headers()
            if hasattr(self.matrix_controller, "get_matrix_headers")
            else []
        )
        rows = (
            self.matrix_controller.get_matrix_rows()
            if hasattr(self.matrix_controller, "get_matrix_rows")
            else []
        )
        return list(headers or []), list(rows or [])

    def run(self):
        logger.info(
            "Start filling Test Spec tables. document=%s, rows=%s",
            self.document_path,
            len(self.matrix_rows),
        )
        try:
            service = TestSpecTablesService()
            success = service.fill_all_test_spec_tables(
                self.document_path,
                self.matrix_data_structure,
                self.matrix_headers,
                self.matrix_rows,
                self.progress_updated,
                self.status_updated,
            )
            self.finished.emit(bool(success))
        except Exception as exc:
            logger.error(f"Failed to fill Test Spec tables: {exc}", exc_info=True)
            self.status_updated.emit(f"错误: {exc}")
            self.finished.emit(False)


class TestSpecTablesPage(QFrame):
    content_updated = pyqtSignal(str)
    finish_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(
        self,
        parent=None,
        document_path=None,
        matrix_controller=None,
        project_context: ProjectContext = None,
    ):
        super().__init__(parent)
        self.document_path = document_path
        self.matrix_controller = matrix_controller
        self.project_context = project_context
        self.worker = None
        self.matrix_data_structure = None

        self.init_ui()
        self._refresh_matrix_data_structure()
        self._auto_start_if_ready()

    def _resolve_project_context(self):
        if self.project_context:
            return self.project_context
        if self.matrix_controller and hasattr(self.matrix_controller, "get_project_context"):
            return self.matrix_controller.get_project_context()
        return None

    def _resolve_matrix_table_data(self) -> Tuple[List[str], List[List[str]]]:
        if not self.matrix_controller:
            return [], []
        headers = (
            self.matrix_controller.get_matrix_headers()
            if hasattr(self.matrix_controller, "get_matrix_headers")
            else []
        )
        rows = (
            self.matrix_controller.get_matrix_rows()
            if hasattr(self.matrix_controller, "get_matrix_rows")
            else []
        )
        return list(headers or []), list(rows or [])

    def _refresh_matrix_data_structure(self):
        headers, rows = self._resolve_matrix_table_data()
        self.matrix_data_structure = _build_matrix_data_structure(
            headers=headers,
            rows=rows,
            project_context=self._resolve_project_context(),
        )

    def _auto_start_if_ready(self):
        if self.document_path and self.progress_bar.value() == 0:
            self.start_processing()
        elif not self.document_path:
            self.status_label.setText("等待文档路径设置...")

    def set_document_path(self, document_path):
        logger.info(f"Set Test Spec document path: {document_path}")
        self.document_path = document_path
        if self.document_path and self.progress_bar.value() == 0:
            self.start_processing()

    def set_matrix_controller(self, matrix_controller):
        logger.info(f"Set matrix controller for Test Spec page: {matrix_controller is not None}")
        self.matrix_controller = matrix_controller
        self._refresh_matrix_data_structure()
        if self.document_path and self.progress_bar.value() == 0:
            self.start_processing()

    def set_project_context(self, project_context: ProjectContext):
        self.project_context = project_context
        self._refresh_matrix_data_structure()

    def start_processing(self):
        if not self.document_path:
            self.status_label.setText("错误: 未指定文档路径")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("正在开始处理...")

        self.worker = TestSpecTablesWorker(
            self.document_path,
            matrix_controller=self.matrix_controller,
            project_context=self.project_context,
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.status_updated.connect(self.update_status)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def update_status(self, status):
        self.status_label.setText(status)

    @pyqtSlot(bool)
    def processing_finished(self, success):
        if success:
            self.status_label.setText("处理完成，表格已成功填充。")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText("处理失败，请检查日志。")

        parent_wizard = self.parent()
        if parent_wizard and hasattr(parent_wizard, "accept"):
            parent_wizard.accept()

    def get_current_data(self):
        return {
            "document_path": self.document_path,
            "matrix_data_structure": self.matrix_data_structure,
            "processing_completed": self.progress_bar.value() == 100,
        }

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("正在填充 Test Description 和 Test Method 表格")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        desc_label = QLabel("正在从当前 Matrix 快照提取数据并写入 Word 文档...")
        desc_label.setStyleSheet("font-size: 14px; color: #666666; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("准备开始处理...")
        self.status_label.setStyleSheet("font-size: 14px; color: #333333;")
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        info_label = QLabel("提示：处理完成后将自动关闭向导。")
        info_label.setStyleSheet("font-size: 14px; color: #666666; margin-top: 10px;")
        layout.addWidget(info_label)

        layout.addStretch()
        self.setLayout(layout)
