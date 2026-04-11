"""
Report wizard dialog.
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
)

from src.core.logger import logger
from src.features.report_wizard.service.report_generation_service import ReportGenerationService
from src.features.report_wizard.view.body_content_page import BodyContentPage
from src.features.report_wizard.view.header_info_page import HeaderInfoPage
from src.features.report_wizard.view.test_spec_tables_page import TestSpecTablesPage


class ReportWizardDialog(QDialog):
    wizard_finished = pyqtSignal(str)

    def __init__(self, parent=None, project_path=None, project_context=None):
        super().__init__(parent)
        self.setWindowTitle("报告生成向导")
        self.setGeometry(200, 200, 800, 600)

        self.current_page_index = 0
        self.pages = []
        self.matrix_controller = None
        self.project_path = project_path
        self.project_context = project_context

        self.init_ui()
        self.add_header_info_page()
        self.add_body_content_page()
        self.add_test_spec_tables_page()

    def init_ui(self):
        main_layout = QVBoxLayout()
        title_label = QLabel("创建标准化测试报告")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)

        self.progress_label = QLabel("步骤 1/3: 页眉信息")
        self.progress_label.setStyleSheet("font-size: 14px; margin: 5px;")
        main_layout.addWidget(self.progress_label)

        self.page_container = QStackedLayout()
        main_layout.addLayout(self.page_container)

        button_layout = QHBoxLayout()
        self.next_button = QPushButton("下一步")
        self.next_button.clicked.connect(self.go_to_next_page)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.next_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def add_header_info_page(self):
        page = HeaderInfoPage()
        self.pages.append(page)
        self.page_container.addWidget(page)
        self.update_navigation_buttons()

    def add_body_content_page(self):
        page = BodyContentPage()
        self.pages.append(page)
        self.page_container.addWidget(page)
        page.content_updated.connect(self._on_content_updated)
        self.update_navigation_buttons()

    def add_test_spec_tables_page(self):
        document_path = None
        if len(self.pages) > 1 and hasattr(self.pages[1], "get_document_path"):
            document_path = self.pages[1].get_document_path()

        page = TestSpecTablesPage(
            document_path=document_path,
            matrix_controller=self.matrix_controller,
            project_context=self.project_context,
        )
        self.pages.append(page)
        self.page_container.addWidget(page)
        self.update_navigation_buttons()

    def _on_content_updated(self, document_path: str):
        logger.info(f"正文内容已更新: {document_path}")

    def go_to_next_page(self):
        if self.current_page_index >= len(self.pages) - 1:
            return

        if self.current_page_index == 0:
            header_page = self.pages[0]
            header_data = header_page.get_header_data()
            service = ReportGenerationService()
            try:
                document_path = service.create_report_from_template(
                    header_data,
                    project_path=self.project_path,
                    project_context=self.project_context,
                )
                body_page = self.pages[1]
                body_page.set_document_path(document_path)
            except Exception as exc:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.critical(self, "错误", f"创建报告文档失败: {exc}")
                return

        self.current_page_index += 1
        if self.current_page_index == 2:
            body_page = self.pages[1]
            document_path = body_page.get_document_path() if hasattr(body_page, "get_document_path") else None
            if document_path:
                test_spec_page = self.pages[2]
                if hasattr(test_spec_page, "set_document_path"):
                    test_spec_page.set_document_path(document_path)
                if self.matrix_controller and hasattr(test_spec_page, "set_matrix_controller"):
                    test_spec_page.set_matrix_controller(self.matrix_controller)
                if hasattr(test_spec_page, "set_project_context"):
                    test_spec_page.set_project_context(self.project_context)
            else:
                logger.warning("无法获取文档路径")

        self.page_container.setCurrentIndex(self.current_page_index)
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.progress_label.setText(f"步骤 {self.current_page_index + 1}/{len(self.pages)}: {self.get_page_title()}")
        self.next_button.setEnabled(self.current_page_index < len(self.pages) - 1)

    def get_page_title(self) -> str:
        if self.current_page_index == 0:
            return "页眉信息"
        if self.current_page_index == 1:
            return "正文内容编辑"
        if self.current_page_index == 2:
            return "填充Test表格"
        return f"步骤 {self.current_page_index + 1}"

    def get_all_data(self):
        data = {}
        if len(self.pages) > 0 and hasattr(self.pages[0], "get_header_data"):
            data["header_data"] = self.pages[0].get_header_data()
        if len(self.pages) > 2 and hasattr(self.pages[2], "get_current_data"):
            data["test_spec_data"] = self.pages[2].get_current_data()
        return data

    def set_matrix_controller(self, matrix_controller):
        logger.info(f"ReportWizardDialog接收到Matrix控制器: {matrix_controller is not None}")
        self.matrix_controller = matrix_controller

    def set_project_context(self, project_context):
        self.project_context = project_context
