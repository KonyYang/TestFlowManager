"""
Test spec tables page.
"""

import weakref
from typing import List, Tuple

from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGroupBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.domain.project.project_document_context import ProjectDocumentContext
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from src.features.report_wizard.protocols.matrix_snapshot_provider import (
    MatrixSnapshotProvider,
)
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

    def __init__(
        self,
        document_path,
        matrix_provider: MatrixSnapshotProvider = None,
        matrix_controller=None,
        project_context: ProjectContext = None,
    ):
        logger.info(f"TestSpecTablesWorker.__init__ started")
        super().__init__()
        self.document_path = document_path
        self.matrix_provider = matrix_provider or matrix_controller
        self.project_context = project_context
        self.project_json_data = self._resolve_project_json_data()
        
        logger.info("Calling _resolve_matrix_table_data...")
        try:
            headers, rows = self._resolve_matrix_table_data()
            logger.info(f"_resolve_matrix_table_data returned: headers={len(headers)}, rows={len(rows)}")
        except Exception as e:
            logger.error(f"Error in _resolve_matrix_table_data: {e}", exc_info=True)
            headers, rows = [], []
        
        self.matrix_headers = headers
        self.matrix_rows = rows
        
        logger.info("Calling _build_matrix_data_structure...")
        try:
            self.matrix_data_structure = _build_matrix_data_structure(
                headers=headers,
                rows=rows,
                project_context=self._resolve_project_context(),
            )
            logger.info("_build_matrix_data_structure completed successfully")
        except Exception as e:
            logger.error(f"Error in _build_matrix_data_structure: {e}", exc_info=True)
            # 创建一个空的结构以避免后续崩溃
            from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
            self.matrix_data_structure = MatrixDataStructure()
        
        logger.info("TestSpecTablesWorker.__init__ completed")

    def _resolve_project_context(self):
        if self.project_context:
            return self.project_context
        if self.matrix_provider and hasattr(self.matrix_provider, "get_project_context"):
            return self.matrix_provider.get_project_context()
        return None

    def _resolve_project_json_data(self):
        project_context = self._resolve_project_context()
        if not project_context:
            return {}
        return ProjectDocumentContext.from_project_context(project_context).project_data

    def _resolve_matrix_table_data(self) -> Tuple[List[str], List[List[str]]]:
        if not self.matrix_provider:
            return [], []
        headers = (
            self.matrix_provider.get_matrix_headers()
            if hasattr(self.matrix_provider, "get_matrix_headers")
            else []
        )
        rows = (
            self.matrix_provider.get_matrix_rows()
            if hasattr(self.matrix_provider, "get_matrix_rows")
            else []
        )
        return list(headers or []), list(rows or [])

    def run(self):
        logger.info("=" * 80)
        logger.info("TestSpecTablesWorker.run() ENTERED")
        logger.info("=" * 80)
        try:
            logger.info(
                f"Start filling Test Spec tables. document={self.document_path}, rows={len(self.matrix_rows)}"
            )
            logger.info("Creating TestSpecTablesService...")
            service = TestSpecTablesService()
            logger.info("TestSpecTablesService created, calling fill_all_test_spec_tables...")
            success = service.fill_all_test_spec_tables(
                self.document_path,
                self.matrix_data_structure,
                self.matrix_headers,
                self.matrix_rows,
                project_json_data=self.project_json_data,
                progress_callback=self.progress_updated,
                status_callback=self.status_updated,
            )
            logger.info(f"fill_all_test_spec_tables returned: {success}")
            logger.info(f"Emitting finished signal with value: {bool(success)}")
            self.finished.emit(bool(success))
            logger.info("finished signal emitted successfully")
        except Exception as exc:
            logger.error(f"Failed to fill Test Spec tables: {exc}", exc_info=True)
            try:
                self.status_updated.emit(f"错误: {exc}")
            except:
                pass
            logger.info("Emitting finished signal with False due to exception")
            try:
                self.finished.emit(False)
            except:
                pass
            logger.info("finished signal emitted (False) after exception")
        finally:
            logger.info("=" * 80)
            logger.info("TestSpecTablesWorker.run() EXITING")
            logger.info("=" * 80)


class TestSpecTablesPage(QFrame):
    content_updated = pyqtSignal(str)
    finish_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(
        self,
        parent=None,
        document_path=None,
        matrix_provider: MatrixSnapshotProvider = None,
        matrix_controller=None,
        project_context: ProjectContext = None,
    ):
        super().__init__(parent)
        self.document_path = document_path
        self.matrix_provider = matrix_provider or matrix_controller
        self.project_context = project_context
        self.project_json_data = self._resolve_project_json_data()
        self.worker = None
        self.matrix_data_structure = None
        self._processing_started = False  # 防止重复启动

        self.init_ui()
        self._refresh_matrix_data_structure()
        self._auto_start_if_ready()

    def _resolve_project_context(self):
        if self.project_context:
            return self.project_context
        if self.matrix_provider and hasattr(self.matrix_provider, "get_project_context"):
            return self.matrix_provider.get_project_context()
        return None

    def _resolve_project_json_data(self):
        project_context = self._resolve_project_context()
        if not project_context:
            return {}
        return ProjectDocumentContext.from_project_context(project_context).project_data

    def _resolve_matrix_table_data(self) -> Tuple[List[str], List[List[str]]]:
        if not self.matrix_provider:
            return [], []
        headers = (
            self.matrix_provider.get_matrix_headers()
            if hasattr(self.matrix_provider, "get_matrix_headers")
            else []
        )
        rows = (
            self.matrix_provider.get_matrix_rows()
            if hasattr(self.matrix_provider, "get_matrix_rows")
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

    def set_matrix_provider(self, matrix_provider: MatrixSnapshotProvider):
        logger.info(f"Set matrix provider for Test Spec page: {matrix_provider is not None}")
        self.matrix_provider = matrix_provider
        self.project_json_data = self._resolve_project_json_data()
        self._refresh_matrix_data_structure()
        # 不在这里启动处理，等待用户明确触发或文档路径设置时启动
        # if self.document_path and self.progress_bar.value() == 0:
        #     self.start_processing()

    def set_matrix_controller(self, matrix_controller):
        self.set_matrix_provider(matrix_controller)

    def set_project_context(self, project_context: ProjectContext):
        self.project_context = project_context
        self.project_json_data = self._resolve_project_json_data()
        self._refresh_matrix_data_structure()

    def start_processing(self):
        if not self.document_path:
            self.status_label.setText("错误: 未指定文档路径")
            return

        # 防止重复启动
        if self._processing_started:
            logger.warning("Processing already started, ignoring duplicate call")
            return

        logger.info(f"start_processing called with document_path: {self.document_path}")
        self._processing_started = True
        
        self.progress_bar.setValue(0)
        self.status_label.setText("正在开始处理...")

        self.worker = TestSpecTablesWorker(
            self.document_path,
            matrix_provider=self.matrix_provider,
            project_context=self.project_context,
        )
        logger.info("TestSpecTablesWorker created")
        
        # 使用 Qt.QueuedConnection 确保槽函数在主线程执行
        self.worker.progress_updated.connect(self.update_progress, Qt.QueuedConnection)
        self.worker.status_updated.connect(self.update_status, Qt.QueuedConnection)
        self.worker.finished.connect(self.processing_finished, Qt.QueuedConnection)
        logger.info("Signals connected with QueuedConnection")
        
        self.worker.start()
        logger.info("Worker thread started")

    @pyqtSlot(int)
    def update_progress(self, value):
        logger.debug(f"update_progress called with value={value}, self alive: {bool(self)}")
        try:
            self.progress_bar.setValue(value)
        except Exception as e:
            logger.error(f"Error in update_progress: {e}")

    @pyqtSlot(str)
    def update_status(self, status):
        logger.debug(f"update_status called with status={status[:50] if status else None}...")
        try:
            self.status_label.setText(status)
        except Exception as e:
            logger.error(f"Error in update_status: {e}")

    @pyqtSlot(bool)
    def processing_finished(self, success):
        logger.info(f"processing_finished called: success={success}")
        logger.info(f"Current page object: {self}")
        logger.info(f"Current page parent: {self.parent()}")
        
        if success:
            self.status_label.setText("处理完成，表格已成功填充。")
            self.progress_bar.setValue(100)
            logger.info("Set status to success and progress to 100%")
        else:
            self.status_label.setText("处理失败，请检查日志。")
            logger.info("Set status to failure")

        # 重置处理标志，允许重新处理（如果需要）
        self._processing_started = False
        logger.info("Reset _processing_started flag")

        # 只关闭报告向导对话框，不影响主窗口
        logger.info("Starting to find ReportWizardDialog in parent hierarchy...")
        parent_wizard = self.parent()
        level = 0
        while parent_wizard is not None:
            level += 1
            logger.info(f"Level {level}: parent type = {type(parent_wizard).__name__}, parent = {parent_wizard}")
            
            # 找到 ReportWizardDialog 并关闭它
            if isinstance(parent_wizard, QDialog):
                logger.info(f"Level {level}: Found QDialog type")
                # (循环导入已移除，改用 duck typing)
                if hasattr(parent_wizard, "wizard_finished"):
                    logger.info(f"Level {level}: Found ReportWizardDialog! Scheduling accept()...")
                    try:
                        # 使用 QTimer.singleShot 延迟关闭，避免在信号槽回调中
                        # 直接调用 accept() 导致的 Qt 重入析构崩溃 (0xC0000409)
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(0, parent_wizard.accept)
                        logger.info("ReportWizardDialog.accept() scheduled via singleShot")
                    except Exception as e:
                        logger.error(f"Error scheduling parent_wizard.accept(): {e}", exc_info=True)
                    break
                else:
                    logger.info(f"Level {level}: QDialog but not ReportWizardDialog, continuing...")
            else:
                logger.info(f"Level {level}: Not a QDialog, continuing...")
            
            parent_wizard = parent_wizard.parent()
        
        if parent_wizard is None:
            logger.warning("Reached top of parent hierarchy without finding ReportWizardDialog!")
        else:
            logger.info(f"Finished parent hierarchy traversal at level {level}")

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
