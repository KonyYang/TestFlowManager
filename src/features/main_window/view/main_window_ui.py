# src/features/main_window/view/main_window_ui.py
"""
主窗口界面模块
定义主窗口的用户界面（Lims 式：顶栏 + 左侧导航 + 主内容区）
"""
import os
from typing import Optional, List, Tuple

from PyQt5.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QLabel,
    QAction,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QApplication,
    QHBoxLayout,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QToolButton,
    QMenu,
    QFrame,
    QSizePolicy,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QRect, pyqtSignal, Qt

from src.core.logger import logger
from src.core.font_utils import FontUtils
from src.features.main_window.controller.main_window_controller import MainWindowController
from src.features.matrix.view.matrix_dialog import MatrixDialog
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController
from src.features.customer_report_generator.controller.customer_report_controller import CustomerReportController
from src.features.report_wizard.controller.report_wizard_controller import ReportWizardController
from src.features.document_parser.controller.document_parser_controller import DocumentParserController
from src.features.report_updater.controller.report_updater_controller import ReportUpdaterController


# 主窗口 Lims 风格全局样式（与参考项目色板对齐）
_LIMS_APP_STYLESHEET = """
QWidget#LimsAppHeader {
    background-color: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
    min-height: 48px;
    max-height: 48px;
}
QLabel#LimsBrandLabel {
    color: #1a3a5c;
    font-weight: bold;
}
QLabel#LimsBreadcrumbLabel {
    color: #757575;
    font-size: 13px;
}
QWidget#LimsSidebar {
    background-color: #1a3a5c;
    min-width: 200px;
    max-width: 200px;
}
QLabel#LimsSidebarSection {
    color: #90caf9;
    font-size: 12px;
    padding: 8px 16px 4px 16px;
}
QListWidget#LimsNavList {
    background-color: #1a3a5c;
    color: #e3f2fd;
    border: none;
    outline: none;
    font-size: 13px;
}
QListWidget#LimsNavList::item {
    padding: 8px 16px 8px 24px;
}
QListWidget#LimsNavList::item:hover {
    background-color: rgba(255, 255, 255, 0.06);
}
QListWidget#LimsNavList::item:selected {
    background-color: #0d47a1;
    color: #e3f2fd;
}
QWidget#LimsMainColumn {
    background-color: #fafafa;
}
QWidget#LimsPagePaper {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}
QLabel#LimsPageTitle {
    color: #1a3a5c;
    font-size: 15px;
    font-weight: bold;
    padding: 0 0 8px 0;
}
QToolButton#LimsHeaderMenuButton {
    color: #757575;
    font-size: 13px;
    border: none;
    padding: 4px 8px;
    background: transparent;
}
QToolButton#LimsHeaderMenuButton:hover {
    background-color: rgba(0, 0, 0, 0.05);
    border-radius: 3px;
}
QToolButton#LimsHeaderMenuButton::menu-indicator {
    image: none;
    width: 0px;
}
QStatusBar {
    background-color: #f5f5f5;
    border-top: 1px solid #e0e0e0;
    color: #333333;
}
"""


class MainWindow(QMainWindow):
    """
    主窗口类
    应用程序的主窗口界面
    """

    startup_progress = pyqtSignal(int, str)

    def __init__(self, splash_screen=None):
        super().__init__()
        self.splash_screen = splash_screen
        self.controller = None
        self.matrix_project_controller = None
        self.matrix_controller = None
        self.customer_report_controller = None
        self.report_wizard_controller = None
        self.document_parser_controller = None
        self.report_updater_controller = None

        self.is_custom_sized = False
        self.custom_geometry = None
        self.fullscreen_geometry = None

        self._breadcrumb_label: Optional[QLabel] = None
        self._page_title_label: Optional[QLabel] = None
        self._nav_list: Optional[QListWidget] = None
        self._page_stack: Optional[QStackedWidget] = None
        self._nav_entries: List[Tuple[str, str]] = []
        
        # 侧栏导航动作映射（索引 -> 动作函数）
        self._nav_actions = {}

        self._initialize_step_by_step()
        self._update_status()

    def _initialize_step_by_step(self):
        """分步初始化主窗口组件"""
        try:
            self._notify_progress(0, "正在初始化基础界面...")
            self._setup_basic_ui()

            self._notify_progress(1, "正在初始化控制器...")
            self._initialize_controllers()

            self._notify_progress(2, "正在设置菜单与顶栏...")
            self._setup_header_menus()
            self._setup_status_bar()

            self._notify_progress(3, "正在设置主导航与页面...")
            self._setup_navigation_pages()

            self._notify_progress(4, "正在初始化业务逻辑...")
            if self.controller:
                self.controller.initialize()

            logger.info("主窗口分步初始化完成")

        except Exception as e:
            logger.error(f"主窗口初始化过程中出错: {e}")
            raise

    def _notify_progress(self, step, message):
        """通知启动进度"""
        if self.splash_screen:
            self.splash_screen.update_progress(step, message)
        self.startup_progress.emit(step, message)

    def _setup_basic_ui(self):
        """设置基础用户界面（Lims 式壳层）"""
        self.setWindowTitle("TestFlow Manager")
        self._set_window_icon()

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen_geometry)
        self.fullscreen_geometry = screen_geometry

        global_font = FontUtils.get_scaled_font(9)
        self.setFont(global_font)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._app_header = self._create_app_header()
        root_layout.addWidget(self._app_header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar = self._create_sidebar()
        body_layout.addWidget(self._sidebar)

        self._main_column = QWidget()
        self._main_column.setObjectName("LimsMainColumn")
        main_layout = QVBoxLayout(self._main_column)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)

        self._page_title_label = QLabel("")
        self._page_title_label.setObjectName("LimsPageTitle")

        self._page_stack = QStackedWidget()
        self._page_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        paper = QFrame()
        paper.setObjectName("LimsPagePaper")
        paper_layout = QVBoxLayout(paper)
        paper_layout.setContentsMargins(12, 12, 12, 12)
        paper_layout.addWidget(self._page_stack, 1)

        main_layout.addWidget(self._page_title_label)
        main_layout.addWidget(paper, 1)

        body_layout.addWidget(self._main_column, 1)
        root_layout.addWidget(body, 1)

        self.setCentralWidget(root)
        self.setStyleSheet(_LIMS_APP_STYLESHEET)

        native_menubar = self.menuBar()
        if native_menubar is not None:
            native_menubar.hide()

    def _create_app_header(self) -> QWidget:
        """创建顶栏：品牌和面包屑（已移除菜单按钮）。"""
        header = QWidget()
        header.setObjectName("LimsAppHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        brand = QLabel("TestFlow Manager")
        brand.setObjectName("LimsBrandLabel")
        brand.setFont(FontUtils.get_scaled_font(11))

        self._breadcrumb_label = QLabel("项目管理 / Matrix 编辑器")
        self._breadcrumb_label.setObjectName("LimsBreadcrumbLabel")
        self._breadcrumb_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(brand)
        layout.addWidget(self._breadcrumb_label, 1)
        return header

    def _create_sidebar(self) -> QWidget:
        """创建左侧导航容器。"""
        side = QWidget()
        side.setObjectName("LimsSidebar")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(0)

        sec1 = QLabel("项目管理")
        sec1.setObjectName("LimsSidebarSection")

        self._nav_list = QListWidget()
        self._nav_list.setObjectName("LimsNavList")
        self._nav_list.setFrameShape(QFrame.NoFrame)
        self._nav_list.setSpacing(0)
        self._nav_list.currentRowChanged.connect(self._on_nav_row_changed)

        sec2 = QLabel("报告管理")
        sec2.setObjectName("LimsSidebarSection")

        sec3 = QLabel("测试表格")
        sec3.setObjectName("LimsSidebarSection")

        sec4 = QLabel("工具箱")
        sec4.setObjectName("LimsSidebarSection")

        layout.addWidget(sec1)
        layout.addWidget(self._nav_list, 1)
        layout.addWidget(sec2)
        layout.addWidget(sec3)
        layout.addWidget(sec4)
        layout.addStretch(0)
        return side

    def _register_action_shortcuts(self, *actions: QAction) -> None:
        """将 QAction 注册到主窗口以保留无菜单栏时的快捷键。"""
        for a in actions:
            self.addAction(a)

    def _setup_header_menus(self):
        """构建原菜单栏功能为侧栏导航项（已移除顶栏菜单按钮）。"""
        # 所有菜单功能已迁移到侧栏导航，此处仅保留快捷键注册
        menu_font = FontUtils.get_scaled_font(8)

        # 文件菜单相关动作
        new_action = QAction("新建项目", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_file)
        new_action.setFont(menu_font)

        open_project_action = QAction("打开项目", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self._on_open_project)
        open_project_action.setFont(menu_font)

        export_matrix_action = QAction("导出窗口矩阵", self)
        export_matrix_action.setShortcut("Ctrl+S")
        export_matrix_action.triggered.connect(self._on_export_matrix)
        export_matrix_action.setFont(menu_font)

        view_ltr_action = QAction("查看LTR", self)
        view_ltr_action.setShortcut("Ctrl+F")
        view_ltr_action.triggered.connect(self._on_view_ltr)
        view_ltr_action.setFont(menu_font)

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self._on_exit)
        exit_action.setFont(menu_font)

        # 测试表格菜单相关动作
        llcr_action = QAction("LLCR", self)
        llcr_action.triggered.connect(self._on_export_llcr)
        llcr_action.setFont(menu_font)

        cr_action = QAction("CR", self)
        cr_action.triggered.connect(self._on_export_cr)
        cr_action.setFont(menu_font)

        # 报告菜单相关动作
        create_report_action = QAction("创建报告", self)
        create_report_action.triggered.connect(self._on_create_report)
        create_report_action.setFont(menu_font)

        update_report_action = QAction("更新报告", self)
        update_report_action.triggered.connect(self._on_update_report)
        update_report_action.setFont(menu_font)

        convert_customer_version_action = QAction("转客户版", self)
        convert_customer_version_action.triggered.connect(self._on_convert_customer_version)
        convert_customer_version_action.setFont(menu_font)

        # 工具菜单相关动作
        body_content_action = QAction("正文内容编辑", self)
        body_content_action.triggered.connect(self._on_edit_body_content)
        body_content_action.setFont(menu_font)

        encrypt_files_action = QAction("测试文件加密", self)
        encrypt_files_action.triggered.connect(self._on_encrypt_test_files)
        encrypt_files_action.setFont(menu_font)

        # 帮助菜单相关动作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        about_action.setFont(menu_font)

        # 注册快捷键（无菜单栏时仍需注册）
        self._register_action_shortcuts(
            new_action,
            open_project_action,
            export_matrix_action,
            view_ltr_action,
            exit_action,
            llcr_action,
            cr_action,
            create_report_action,
            update_report_action,
            convert_customer_version_action,
            body_content_action,
            encrypt_files_action,
            about_action,
        )

    def _initialize_controllers(self):
        """初始化控制器"""
        self.controller = MainWindowController(self)
        self.matrix_project_controller = MatrixProjectController(self)
        self.matrix_controller = self.matrix_project_controller.matrix_controller
        self.customer_report_controller = CustomerReportController(self)
        self.report_wizard_controller = ReportWizardController(self)
        self.document_parser_controller = DocumentParserController(self)
        self.report_updater_controller = ReportUpdaterController(self)

    def _setup_navigation_pages(self):
        """注册侧栏条目与堆叠页面（所有菜单项改为侧栏直达）。"""
        # === 项目管理组 ===
        self._register_nav_page(
            "➕ 新建项目", 
            "项目管理 / 新建项目", 
            self._create_placeholder_page("新建项目"),
            action=self._on_new_file
        )
        self._register_nav_page(
            "📂 打开项目", 
            "项目管理 / 打开项目", 
            self._create_placeholder_page("打开项目"),
            action=self._on_open_project
        )
        self._register_nav_page(
            "📋 查看LTR", 
            "项目管理 / 查看LTR", 
            self._create_placeholder_page("查看LTR"),
            action=self._on_view_ltr
        )
        
        # === Matrix 编辑器（默认首页）===
        self.matrix_tab = QWidget()
        self._setup_matrix_tab()
        self._register_nav_page("📊 Matrix 编辑器", "项目管理 / Matrix 编辑器", self.matrix_tab)
        
        # === 报告管理组 ===
        self._register_nav_page(
            "🆕 创建报告", 
            "报告管理 / 创建报告", 
            self._create_placeholder_page("创建报告"),
            action=self._on_create_report
        )
        self._register_nav_page(
            "🔄 更新报告", 
            "报告管理 / 更新报告", 
            self._create_placeholder_page("更新报告"),
            action=self._on_update_report
        )
        self._register_nav_page(
            "👥 转客户版", 
            "报告管理 / 转客户版", 
            self._create_placeholder_page("转客户版"),
            action=self._on_convert_customer_version
        )
        
        # === 测试表格组 ===
        self._register_nav_page(
            "📤 导出窗口矩阵", 
            "测试表格 / 导出窗口矩阵", 
            self._create_placeholder_page("导出窗口矩阵"),
            action=self._on_export_matrix
        )
        self._register_nav_page(
            "📊 LLCR", 
            "测试表格 / LLCR", 
            self._create_placeholder_page("LLCR"),
            action=self._on_export_llcr
        )
        self._register_nav_page(
            "📋 CR", 
            "测试表格 / CR", 
            self._create_placeholder_page("CR"),
            action=self._on_export_cr
        )
        
        # === 工具箱组 ===
        self._register_nav_page(
            "📝 正文内容编辑", 
            "工具箱 / 正文内容编辑", 
            self._create_placeholder_page("正文内容编辑"),
            action=self._on_edit_body_content
        )
        self._register_nav_page(
            "🔐 测试文件加密", 
            "工具箱 / 测试文件加密", 
            self._create_placeholder_page("测试文件加密"),
            action=self._on_encrypt_test_files
        )
        
        # === 其他 ===
        self._register_nav_page(
            "ℹ️ 关于", 
            "关于 TestFlow Manager", 
            self._create_placeholder_page("关于"),
            action=self._on_about
        )

    def _register_nav_page(self, nav_title: str, breadcrumb_text: str, page: QWidget, action=None) -> None:
        """
        添加侧栏一项并放入堆叠控件。
        
        Args:
            nav_title: 侧栏显示标题
            breadcrumb_text: 面包屑文本
            page: 页面对象
            action: 可选的触发动作函数（点击时执行）
        """
        if self._nav_list is None or self._page_stack is None:
            return
        index = len(self._nav_entries)
        self._nav_entries.append((nav_title, breadcrumb_text))
        item = QListWidgetItem(nav_title)
        self._nav_list.addItem(item)
        self._page_stack.addWidget(page)
        
        # 注册动作映射
        if action:
            self._nav_actions[index] = action

        if self._nav_list.count() == 1:
            self._nav_list.setCurrentRow(0)
            self._apply_nav_index(0)

    def _on_nav_row_changed(self, row: int) -> None:
        """侧栏选中行变化。"""
        if row < 0:
            return
        
        # 如果有注册的动作，先执行动作
        if row in self._nav_actions:
            action_func = self._nav_actions[row]
            try:
                action_func()
            except Exception as e:
                logger.error(f"执行侧栏动作失败: {e}", exc_info=True)
        
        # 然后切换页面
        self._apply_nav_index(row)

    def _apply_nav_index(self, index: int) -> None:
        """同步堆叠页、页标题与面包屑。"""
        if self._page_stack is None or not self._nav_entries or index >= len(self._nav_entries):
            return
        self._page_stack.setCurrentIndex(index)
        nav_title, breadcrumb = self._nav_entries[index]
        if self._page_title_label is not None:
            self._page_title_label.setText(nav_title)
        if self._breadcrumb_label is not None:
            self._breadcrumb_label.setText(breadcrumb)

    def _create_placeholder_page(self, title: str) -> QWidget:
        """创建占位页面（后续可替换为实际功能页面）。"""
        from PyQt5.QtWidgets import QLabel, QVBoxLayout
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel(f"🚧 {title} 功能开发中...")
        label.setStyleSheet("""
            font-size: 16pt;
            color: #757575;
            padding: 40px;
        """)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

    def _setup_matrix_tab(self):
        """Matrix 主内容页"""
        layout = QVBoxLayout(self.matrix_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.matrix_dialog = MatrixDialog(parent=self, service=self.matrix_controller.service)
        layout.addWidget(self.matrix_dialog)

    def _set_window_icon(self):
        """设置窗口图标"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "app", "resources", "icons", "app_icon.ico")
            icon_path = os.path.normpath(icon_path)
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logger.debug(f"成功设置窗口图标: {icon_path}")
            else:
                logger.warning(f"窗口图标文件不存在: {icon_path}")
        except Exception as e:
            logger.error(f"设置窗口图标时出错: {e}")

    def showEvent(self, event):
        super().showEvent(event)

    def changeEvent(self, event):
        if event.type() == event.WindowStateChange:
            if self.isMaximized() and self.is_custom_sized:
                self.is_custom_sized = False
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def showNormal(self):
        if self.isMaximized():
            self.is_custom_sized = True
            if not self.custom_geometry:
                screen_geometry = QApplication.primaryScreen().availableGeometry()
                width = int(screen_geometry.width() * 0.3)
                height = int(screen_geometry.height() * 0.3)
                x = (screen_geometry.width() - width) // 2
                y = (screen_geometry.height() - height) // 2
                self.custom_geometry = QRect(x, y, width, height)
            super().showNormal()
            self.setGeometry(self.custom_geometry)
        else:
            super().showNormal()

    def showMaximized(self):
        self.is_custom_sized = False
        super().showMaximized()

    def showMinimized(self):
        self.is_custom_sized = False
        super().showMinimized()

    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        status_font = FontUtils.get_scaled_font(8)
        self.status_bar.setFont(status_font)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(status_font)
        self.status_bar.addWidget(self.status_label)

    def _on_view_ltr(self) -> None:
        logger.debug("View LTR action triggered")
        if self.controller.handle_view_ltr():
            self._update_status()

    def _on_new_file(self) -> None:
        logger.debug("New file action triggered")
        if self.controller.handle_new_file():
            self._update_status()

    def _on_open_project(self) -> None:
        logger.debug("Open project action triggered")
        if self.controller.handle_open_project():
            self._update_status()

    def _on_export_matrix(self) -> None:
        logger.debug("Export matrix action triggered")
        if self.matrix_controller.handle_export_matrix_to_excel():
            self._update_status()

    def _on_export_llcr(self) -> None:
        logger.debug("Export LLCR action triggered")
        if self.matrix_controller.handle_export_llcr():
            self._update_status()

    def _on_export_cr(self) -> None:
        logger.debug("Export CR action triggered")
        if self.matrix_controller.handle_export_cr():
            self._update_status()

    def _on_create_report(self) -> None:
        logger.debug("Create report action triggered")
        current_project_path = getattr(self.controller, "_current_project_path", None)
        self.report_wizard_controller.set_project_path(current_project_path)
        self.report_wizard_controller.set_matrix_service(self.matrix_controller.service)
        self.report_wizard_controller.show_wizard()
        self._update_status()

    def _on_update_report(self) -> None:
        logger.debug("Update report action triggered")
        current_project_path = getattr(self.controller, "_current_project_path", None)
        self.report_updater_controller.set_project_path(current_project_path)
        self.report_updater_controller.show_report_updater_dialog()
        self._update_status()

    def _on_convert_customer_version(self) -> None:
        logger.debug("Convert to customer version action triggered")
        current_project_path = getattr(self.controller, "_current_project_path", None)
        if self.customer_report_controller.handle_generate_customer_report(current_project_path):
            self._update_status()
        else:
            self._update_status()

    def _on_edit_body_content(self) -> None:
        logger.debug("Edit body content action triggered")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Word 文档", "", "Word 文档 (*.doc *.docx)"
        )
        if file_path:
            logger.info(f"用户选择了文件：{file_path}")
            self.document_parser_controller.show_body_content_editor(file_path)
        else:
            logger.info("用户取消了文件选择")
        self._update_status()

    def _on_encrypt_test_files(self) -> None:
        logger.debug("Encrypt test files action triggered")
        try:
            from src.features.file_encryption.controller.file_encryption_controller import FileEncryptionController

            encryption_controller = FileEncryptionController(self)
            folder_path = encryption_controller.show_folder_selection()
            if folder_path:
                encryption_controller.start_encryption_task(folder_path)
            self._update_status()
        except Exception as e:
            logger.error(f"加密功能执行失败：{e}", exc_info=True)

    def _on_exit(self) -> None:
        logger.debug("Exit action triggered")
        self.close()

    def _on_about(self) -> None:
        logger.debug("About action triggered")
        self.controller.handle_about()

    def _update_status(self) -> None:
        """更新状态栏"""
        status = self.controller.get_status()
        self.status_label.setText(status)

    def closeEvent(self, event) -> None:
        logger.info("MainWindow closing")
        self.controller.shutdown()
        event.accept()
