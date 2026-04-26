# src/shell/main_window/components/page_factory.py
"""
页面工厂模块
统一创建各类页面组件，提供可复用的页面构建方法
"""
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class PageFactory:
    """页面工厂 - 统一创建各类页面组件"""

    @staticmethod
    def create_placeholder_page(
        title: str,
        description: str = "",
    ) -> QWidget:
        """
        创建简洁的占位页面（无 emoji 装饰）

        Args:
            title: 页面标题
            description: 页面描述文本（可选）

        Returns:
            QWidget: 配置好的占位页面对象
        """
        page = QWidget()
        page.setStyleSheet("background-color: #fafbfc;")

        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        # 卡片容器
        card = QWidget()
        card.setStyleSheet("""
            background: white;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(60, 60, 60, 60)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignCenter)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #2d3748;
        """)
        title_label.setAlignment(Qt.AlignCenter)

        # 分隔线
        divider = QWidget()
        divider.setFixedSize(80, 3)
        divider.setStyleSheet("""
            background: #3182ce;
            border-radius: 2px;
        """)

        # 描述
        desc_text = description if description else "此功能正在开发中，敬请期待..."
        desc_label = QLabel(desc_text)
        desc_label.setStyleSheet("""
            font-size: 20px;
            color: #718096;
        """)
        desc_label.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(title_label)
        card_layout.addWidget(divider)
        card_layout.addWidget(desc_label)

        layout.addWidget(card)
        return page

    @staticmethod
    def create_ltr_application_page(
        application_data: Optional[Dict[str, Any]] = None,
        parent_controller: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> QWidget:
        """
        创建 LTR 申请单页面

        Args:
            application_data: 包含申请单数据的字典（可选）
            parent_controller: 父级控制器（可选）
            parent: 父窗口

        Returns:
            QWidget: LTRApplicationPage 实例
        """
        from src.features.ltr_manager.view.ltr_application_page import LTRApplicationPage
        return LTRApplicationPage(
            application_data=application_data,
            parent_controller=parent_controller,
            parent=parent,
        )

    @staticmethod
    def create_ltr_editor_page(
        dl_data: Optional[Dict[str, Any]] = None,
        update_callback: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> QWidget:
        """
        创建 LTR 编辑页面

        Args:
            dl_data: 包含DL编号和相关数据的字典（可选）
            update_callback: 更新回调函数（可选）
            parent: 父窗口

        Returns:
            QWidget: LTREditorPage 实例
        """
        from src.features.ltr_manager.view.ltr_editor_page import LTREditorPage
        return LTREditorPage(
            dl_data=dl_data,
            update_callback=update_callback,
            parent=parent,
        )

    @staticmethod
    def create_project_info_page(
        project_data: Optional[Dict[str, Any]] = None,
        project_data_file_path: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> QWidget:
        """
        创建项目信息页面

        Args:
            project_data: 包含项目数据的字典（可选）
            project_data_file_path: 项目数据文件路径（可选）
            parent: 父窗口

        Returns:
            QWidget: ProjectInfoPage 实例
        """
        from src.features.project_creator.view.project_info_page import ProjectInfoPage
        return ProjectInfoPage(
            project_data=project_data,
            project_data_file_path=project_data_file_path,
            parent=parent,
        )

    @staticmethod
    def create_report_wizard_page(
        project_context=None,
        matrix_provider=None,
        matrix_controller=None,
        create_report_callback=None,
        parent: Optional[QWidget] = None,
    ) -> QWidget:
        """
        创建报告生成向导页面

        Args:
            project_context: 项目上下文
            matrix_provider: Matrix 数据提供者
            matrix_controller: Matrix 控制器
            create_report_callback: 创建报告的回调函数
            parent: 父窗口

        Returns:
            QWidget: ReportWizardPage 实例
        """
        from src.features.report_wizard.view.report_wizard_page import ReportWizardPage
        return ReportWizardPage(
            project_context=project_context,
            matrix_provider=matrix_provider,
            matrix_controller=matrix_controller,
            create_report_callback=create_report_callback,
            parent=parent,
        )
