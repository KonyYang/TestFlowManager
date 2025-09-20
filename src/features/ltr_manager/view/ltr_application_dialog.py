"""
LTR申请单对话框模块
提供一个对话框用于显示和编辑LTR申请单信息
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QWidget, QScrollArea, QLabel, QLineEdit, QTextEdit, QFormLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDesktopWidget
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData


class LTRApplicationDialog(QDialog):
    """
    LTR申请单对话框类
    用于显示和编辑LTR申请单信息
    """

    def __init__(self, application_data, parent=None):
        """
        初始化LTR申请单对话框

        Args:
            application_data: 包含申请单数据的字典
            parent: 父窗口
        """
        super().__init__(parent)
        self.parent_window = parent
        self.application_data = application_data

        self.dl_number = application_data.get('dl_number', '')
        self.original_data = application_data.get('data', {})
        self.modified_data = self.original_data.copy()

        # 初始化数据模型
        self.data_model = LTRApplicationData.from_dict(self.original_data)

        self._setup_ui()
        self._populate_data()
        self._center_dialog()

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"LTR申请单: {self.dl_number}" if self.dl_number else "新LTR申请单")
        self.setMinimumSize(800, 600)

        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # 创建输入控件
        self._create_input_fields(form_layout)

        scroll_layout.addLayout(form_layout)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        main_layout.addWidget(scroll_area)

        # 创建按钮
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_input_fields(self, form_layout):
        """创建输入字段"""
        # 申请单基本信息
        self.requested_by_edit = QLineEdit()
        form_layout.addRow("申请人(*):", self.requested_by_edit)

        self.location_edit = QLineEdit()
        form_layout.addRow("制造地点(*):", self.location_edit)

        self.phone_edit = QLineEdit()
        form_layout.addRow("电话:", self.phone_edit)

        self.email_requestor_edit = QLineEdit()
        form_layout.addRow("邮箱:", self.email_requestor_edit)

        # 日期信息
        self.date_lab_received_samples_edit = QLineEdit()
        form_layout.addRow("实验室接收样品日期:", self.date_lab_received_samples_edit)

        self.estimated_completion_date_edit = QLineEdit()
        form_layout.addRow("预计完成日期:", self.estimated_completion_date_edit)

        # 项目信息
        self.project_type_edit = QLineEdit()
        form_layout.addRow("项目类型(*):", self.project_type_edit)

        self.test_type_edit = QLineEdit()
        form_layout.addRow("测试类型(*):", self.test_type_edit)

        self.sub_contract_edit = QLineEdit()
        form_layout.addRow("是否外包测试:", self.sub_contract_edit)

        # 样品信息
        self.sample_information_edit = QTextEdit()
        self.sample_information_edit.setMaximumHeight(100)
        form_layout.addRow("样品信息:", self.sample_information_edit)

        # 测试要求
        self.tests_to_be_performed_edit = QTextEdit()
        self.tests_to_be_performed_edit.setMaximumHeight(100)
        form_layout.addRow("待执行测试:", self.tests_to_be_performed_edit)

        self.applicable_specifications_edit = QTextEdit()
        self.applicable_specifications_edit.setMaximumHeight(100)
        form_layout.addRow("适用规范:", self.applicable_specifications_edit)

        # 其他信息
        self.project_leader_edit = QLineEdit()
        form_layout.addRow("项目负责人:", self.project_leader_edit)

        self.failed_item_edit = QLineEdit()
        form_layout.addRow("失效项目:", self.failed_item_edit)

        self.sample_deposition_edit = QLineEdit()
        form_layout.addRow("样品存放:", self.sample_deposition_edit)

        self.test_fee_edit = QLineEdit()
        form_layout.addRow("测试费用:", self.test_fee_edit)

        self.remarks_po_edit = QLineEdit()
        form_layout.addRow("备注/PO:", self.remarks_po_edit)

    def _create_buttons(self, main_layout):
        """创建按钮"""
        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 创建按钮
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")

        # 连接信号
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # 添加按钮到布局
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def _populate_data(self):
        """填充数据到控件"""
        # 填充基本信息
        self.requested_by_edit.setText(self.data_model.requested_by)
        self.location_edit.setText(self.data_model.location)
        self.phone_edit.setText(self.data_model.phone)
        self.email_requestor_edit.setText(self.data_model.email_requestor)

        # 填充日期信息
        self.date_lab_received_samples_edit.setText(self.data_model.date_lab_received_samples)
        self.estimated_completion_date_edit.setText(self.data_model.estimated_completion_date)

        # 填充项目信息
        self.project_type_edit.setText(self.data_model.project_type)
        self.test_type_edit.setText(self.data_model.test_type)
        self.sub_contract_edit.setText(self.data_model.sub_contract)

        # 填充样品信息
        self.sample_information_edit.setPlainText(self.data_model.sample_information)

        # 填充测试要求
        self.tests_to_be_performed_edit.setPlainText(self.data_model.tests_to_be_performed)
        self.applicable_specifications_edit.setPlainText(self.data_model.applicable_specifications)

        # 填充其他信息
        self.project_leader_edit.setText(self.data_model.project_leader)
        self.failed_item_edit.setText(self.data_model.failed_item)
        self.sample_deposition_edit.setText(self.data_model.sample_deposition)
        self.test_fee_edit.setText(self.data_model.test_fee)
        self.remarks_po_edit.setText(self.data_model.remarks_po)

    def _center_dialog(self):
        """居中对话框"""
        if self.parent_window:
            parent_center = self.parent_window.geometry().center()
            self.move(parent_center.x() - self.width() // 2,
                     parent_center.y() - self.height() // 2)
        else:
            # 如果没有父窗口，在屏幕中央显示
            qr = self.frameGeometry()
            cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())

    def get_modified_data(self) -> dict:
        """
        获取用户修改后的数据

        Returns:
            包含修改后数据的字典
        """
        modified_data = {
            'dl_number': self.dl_number,
            'requested_by': self.requested_by_edit.text(),
            'location': self.location_edit.text(),
            'phone': self.phone_edit.text(),
            'email_requestor': self.email_requestor_edit.text(),
            'date_lab_received_samples': self.date_lab_received_samples_edit.text(),
            'estimated_completion_date': self.estimated_completion_date_edit.text(),
            'project_type': self.project_type_edit.text(),
            'test_type': self.test_type_edit.text(),
            'sub_contract': self.sub_contract_edit.text(),
            'sample_information': self.sample_information_edit.toPlainText(),
            'tests_to_be_performed': self.tests_to_be_performed_edit.toPlainText(),
            'applicable_specifications': self.applicable_specifications_edit.toPlainText(),
            'project_leader': self.project_leader_edit.text(),
            'failed_item': self.failed_item_edit.text(),
            'sample_deposition': self.sample_deposition_edit.text(),
            'test_fee': self.test_fee_edit.text(),
            'remarks_po': self.remarks_po_edit.text()
        }

        return modified_data

    def accept(self):
        """重写accept方法，添加数据验证"""
        # 这里可以添加数据验证逻辑
        super().accept()
