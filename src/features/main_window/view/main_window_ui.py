# src/features/main_window/view/main_window_ui.py
"""
主窗口界面模块
定义主窗口的用户界面（Lims 式：顶栏 + 左侧导航 + 主内容区）
"""
import os
import ctypes
import ctypes.wintypes
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
    QMessageBox,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QRect, QPoint, pyqtSignal, Qt
from PyQt5.QtGui import QMouseEvent

from src.core.logger import logger
from src.core.font_utils import FontUtils
from src.features.main_window.controller.main_window_controller import MainWindowController
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController
from src.features.customer_report_generator.controller.customer_report_controller import CustomerReportController
from src.features.report_wizard.controller.report_wizard_controller import ReportWizardController
from src.features.document_parser.controller.document_parser_controller import DocumentParserController
from src.features.report_updater.controller.report_updater_controller import ReportUpdaterController
from src.features.matrix.view.matrix_page import MatrixPage
from src.features.main_window.facade.matrix_workspace_facade import MatrixWorkspaceFacade
from src.features.matrix.service.matrix_session_entry_facade import MatrixSessionEntryFacade


# 主窗口 Lims 风格全局样式（高分辨率屏幕优化版）
_LIMS_APP_STYLESHEET = """
/* ==================== 顶栏样式 ==================== */
QWidget#LimsAppHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a3a5c, stop:1 #2c5282);
    border-bottom: none;
    min-height: 70px;
    max-height: 70px;
}
QLabel#LimsBrandLabel {
    color: #ffffff;
    font-weight: bold;
    font-size: 26px;
    letter-spacing: 0.5px;
}
QLabel#LimsBreadcrumbLabel {
    color: rgba(255, 255, 255, 0.9);
    font-size: 18px;
}
QWidget#LimsHeaderActions {
    background: transparent;
}

/* ==================== 侧边栏样式 ==================== */
QWidget#LimsSidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a3a5c, stop:1 #152a45);
    min-width: 260px;
    max-width: 260px;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
QLabel#LimsSidebarSection {
    color: #90caf9;
    font-size: 15px;
    font-weight: bold;
    padding: 18px 18px 10px 24px;
    letter-spacing: 1px;
}
QLabel#LimsSidebarSection:first-child {
    padding-top: 24px;
}
QListWidget#LimsNavList {
    background-color: transparent;
    color: #e3f2fd;
    border: none;
    outline: none;
    font-size: 18px;
}
QListWidget#LimsNavList::item {
    padding: 14px 18px 14px 28px;
    margin: 4px 12px;
    border-radius: 8px;
}
QListWidget#LimsNavList::item:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
QListWidget#LimsNavList::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #2c5282);
    color: #ffffff;
    font-weight: 600;
}

/* ==================== 主内容区样式 ==================== */
QWidget#LimsMainColumn {
    background-color: #f0f4f8;
}
QWidget#LimsPagePaper {
    background-color: #ffffff;
    border-radius: 10px;
    border: none;
    /* 添加阴影效果 */
    border-top: 1px solid rgba(0, 0, 0, 0.05);
}
QLabel#LimsPageTitle {
    color: #1a3a5c;
    font-size: 28px;
    font-weight: bold;
    padding: 12px 0 20px 6px;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 6px;
}
QLabel#LimsPageSubtitle {
    color: #718096;
    font-size: 18px;
    padding-left: 6px;
}

/* ==================== 顶栏按钮样式 ==================== */
QToolButton#LimsHeaderMenuButton {
    color: rgba(255, 255, 255, 0.9);
    font-size: 18px;
    border: none;
    padding: 10px 16px;
    background: transparent;
    border-radius: 6px;
}
QToolButton#LimsHeaderMenuButton:hover {
    background-color: rgba(255, 255, 255, 0.15);
    color: #ffffff;
}
QToolButton#LimsHeaderMenuButton::menu-indicator {
    image: none;
    width: 0px;
}

/* ==================== 状态栏样式 ==================== */
QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f7fafc);
    border-top: 1px solid #e2e8f0;
    color: #4a5568;
    font-size: 16px;
}
QStatusBar::item {
    border: none;
}

/* ==================== Matrix 表格样式 ==================== */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #edf2f7;
    selection-background-color: #bee3f8;
    selection-color: #1a3a5c;
    font-size: 16px;
}
QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #edf2f7;
}
QTableWidget::item:alternate {
    background-color: #f7fafc;
}
QTableWidget::item:selected {
    background-color: #bee3f8;
    color: #1a3a5c;
}
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7fafc, stop:1 #edf2f7);
    color: #4a5568;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #cbd5e0;
    font-weight: bold;
    font-size: 16px;
}
QHeaderView::section:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #edf2f7, stop:1 #e2e8f0);
}
"""


class MainWindow(QMainWindow):
    """
    主窗口类
    应用程序的主窗口界面
    """

    startup_progress = pyqtSignal(int, str)

    def __init__(
        self,
        splash_screen=None,
        *,
        matrix_workspace_facade: Optional[MatrixWorkspaceFacade] = None,
    ):
        super().__init__()
        self.splash_screen = splash_screen
        self.controller = None

        # 通过 facade 统一访问所有 Matrix session 对象（私有属性，不对外暴露）
        self._workspace_facade = matrix_workspace_facade or MatrixWorkspaceFacade(parent_view=self)
        
        # 延迟加载的控制器使用私有属性
        self._customer_report_controller = None
        self._report_wizard_controller = None
        self._document_parser_controller = None
        self._report_updater_controller = None

        self.is_custom_sized = False
        self.custom_geometry = None
        self.fullscreen_geometry = None

        self._breadcrumb_label: Optional[QLabel] = None
        self._page_title_label: Optional[QLabel] = None
        self._page_subtitle_label: Optional[QLabel] = None
        self._nav_list: Optional[QListWidget] = None
        self._page_stack: Optional[QStackedWidget] = None
        # 元组格式: (nav_title, breadcrumb, subtitle, page_id)
        self._nav_entries: List[Tuple[str, str, str, str]] = []
        self._current_page_id: str = ""  # 当前页面 ID
        
        # DL编号显示标签
        self._dl_number_label: Optional[QLabel] = None
        
        # 侧栏导航动作映射（索引 -> 动作函数）
        self._nav_actions = {}
        
        # 初始化期间禁止自动触发动作
        self._initializing_nav = False
        
        # Matrix 页面与兼容访问口
        self.matrix_tab: Optional[QWidget] = None
        self.matrix_page: Optional[MatrixPage] = None

        self._initialize_step_by_step()
        self._update_status()

    def _initialize_step_by_step(self):
        """分步初始化主窗口组件"""
        import time
        start_time = time.time()
        try:
            self._notify_progress(0, "正在初始化基础界面...")
            t1 = time.time()
            self._setup_basic_ui()
            logger.info(f"[性能] 基础UI初始化耗时: {time.time() - t1:.3f}秒")

            self._notify_progress(1, "正在初始化控制器...")
            t2 = time.time()
            self._initialize_controllers()
            logger.info(f"[性能] 控制器初始化耗时: {time.time() - t2:.3f}秒")

            self._notify_progress(2, "正在设置菜单与顶栏...")
            t3 = time.time()
            self._setup_header_menus()
            self._setup_status_bar()
            logger.info(f"[性能] 菜单和状态栏设置耗时: {time.time() - t3:.3f}秒")

            self._notify_progress(3, "正在设置主导航与页面...")
            t4 = time.time()
            self._setup_navigation_pages()
            logger.info(f"[性能] 导航和页面设置耗时: {time.time() - t4:.3f}秒")

            self._notify_progress(4, "正在初始化业务逻辑...")
            t5 = time.time()
            if self.controller:
                self.controller.initialize()
            logger.info(f"[性能] 业务逻辑初始化耗时: {time.time() - t5:.3f}秒")

            total_time = time.time() - start_time
            logger.info(f"[性能] 主窗口总初始化耗时: {total_time:.3f}秒")

        except Exception as e:
            logger.error(f"主窗口初始化过程中出错: {e}")
            raise

    def _notify_progress(self, step, message):
        """通知启动进度"""
        if self.splash_screen:
            self.splash_screen.update_progress(step, message)
        self.startup_progress.emit(step, message)

    def _setup_basic_ui(self):
        """设置基础用户界面（现代化 Lims 风格，无边框自定义标题栏）"""
        # 设置无边框窗口模式
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._resize_border_width = 8
        
        self.setWindowTitle("TestFlow Manager")
        self._set_window_icon()

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen_geometry)
        self.fullscreen_geometry = screen_geometry
        self.setMinimumSize(1024, 640)

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
        main_layout.setContentsMargins(24, 24, 24, 16)
        main_layout.setSpacing(0)

        # 页面标题区域
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 16)
        title_layout.setSpacing(4)
        
        self._page_title_label = QLabel("")
        self._page_title_label.setObjectName("LimsPageTitle")
        
        # 副标题/描述区域
        self._page_subtitle_label = QLabel("")
        self._page_subtitle_label.setStyleSheet("""
            color: #718096;
            font-size: 18px;
            padding-left: 6px;
        """)
        
        title_layout.addWidget(self._page_title_label)
        title_layout.addWidget(self._page_subtitle_label)
        main_layout.addWidget(title_widget)

        self._page_stack = QStackedWidget()
        self._page_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        paper = QFrame()
        paper.setObjectName("LimsPagePaper")
        paper.setStyleSheet("""
            QWidget#LimsPagePaper {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }
        """)
        paper_layout = QVBoxLayout(paper)
        paper_layout.setContentsMargins(16, 16, 16, 16)
        paper_layout.addWidget(self._page_stack, 1)

        main_layout.addWidget(paper, 1)

        body_layout.addWidget(self._main_column, 1)
        root_layout.addWidget(body, 1)

        self.setCentralWidget(root)
        self.setStyleSheet(_LIMS_APP_STYLESHEET)

        native_menubar = self.menuBar()
        if native_menubar is not None:
            native_menubar.hide()



    def _create_app_header(self) -> QWidget:
        """创建现代化顶栏：简洁图标 + 面包屑 + 快捷操作（支持拖拽和双击最大化）"""
        header = QWidget()
        header.setObjectName("LimsAppHeader")
        header.setMouseTracking(True)
        # 设置顶栏为可拖拽区域
        header.mousePressEvent = self._on_header_mouse_press
        header.mouseMoveEvent = self._on_header_mouse_move
        header.mouseReleaseEvent = self._on_header_mouse_release
        header.mouseDoubleClickEvent = self._on_header_double_click
        self._header_drag_start_pos: QPoint = None
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(16)

        # 左侧：应用图标 + DL编号
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        brand_icon = QLabel()
        brand_icon.setText("🔬")
        brand_icon.setStyleSheet("font-size: 36px;")
        brand_icon.setToolTip("TestFlow Manager")
        left_layout.addWidget(brand_icon)
        
        # DL编号标签（初始为空）
        self._dl_number_label = QLabel("")
        self._dl_number_label.setObjectName("LimsDLNumberLabel")
        self._dl_number_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 20px;
            font-weight: bold;
            padding: 4px 12px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
        """)
        self._dl_number_label.setVisible(False)  # 初始隐藏
        left_layout.addWidget(self._dl_number_label)
        
        layout.addWidget(left_widget)

        # 中间面包屑
        self._breadcrumb_label = QLabel("📁 项目管理 / Matrix 编辑器")
        self._breadcrumb_label.setObjectName("LimsBreadcrumbLabel")
        self._breadcrumb_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._breadcrumb_label, 1)

        # 右侧快捷操作区
        actions_widget = QWidget()
        actions_widget.setObjectName("LimsHeaderActions")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # 快捷按钮：全屏切换
        fullscreen_btn = QToolButton()
        fullscreen_btn.setObjectName("LimsHeaderMenuButton")
        fullscreen_btn.setText("⛶")
        fullscreen_btn.setToolTip("切换全屏模式 (F11)")
        fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        
        # 快捷按钮：最小化
        minimize_btn = QToolButton()
        minimize_btn.setObjectName("LimsHeaderMenuButton")
        minimize_btn.setText("─")
        minimize_btn.setToolTip("最小化窗口")
        minimize_btn.clicked.connect(self.showMinimized)
        
        # 快捷按钮：最大化
        self._maximize_btn = QToolButton()
        self._maximize_btn.setObjectName("LimsHeaderMenuButton")
        self._maximize_btn.setText("□")
        self._maximize_btn.setToolTip("最大化窗口")
        self._maximize_btn.clicked.connect(self._toggle_maximize)
        
        # 快捷按钮：关闭
        close_btn = QToolButton()
        close_btn.setObjectName("LimsHeaderMenuButton")
        close_btn.setText("✕")
        close_btn.setToolTip("关闭应用")
        close_btn.clicked.connect(self.close)
        
        actions_layout.addWidget(fullscreen_btn)
        actions_layout.addWidget(minimize_btn)
        actions_layout.addWidget(self._maximize_btn)
        actions_layout.addWidget(close_btn)
        layout.addWidget(actions_widget)
        
        return header
    
    def _toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def _toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()
    
    def update_dl_number_display(self, dl_number: str) -> None:
        """
        更新顶栏左侧的DL编号显示
        
        Args:
            dl_number: DL编号，如果为空则隐藏标签
        """
        if self._dl_number_label:
            if dl_number and dl_number.strip():
                self._dl_number_label.setText(f"📋 {dl_number}")
                self._dl_number_label.setVisible(True)
                self._dl_number_label.setToolTip(f"当前项目: {dl_number}")
            else:
                self._dl_number_label.setText("")
                self._dl_number_label.setVisible(False)

    def _on_header_mouse_press(self, event: QMouseEvent):
        """鼠标按下：开始拖拽"""
        if event.button() == Qt.LeftButton:
            self._header_drag_start_pos = event.globalPos()
            self._header_drag_started = True

    def _on_header_mouse_move(self, event: QMouseEvent):
        """鼠标移动：拖拽窗口"""
        if hasattr(self, '_header_drag_started') and self._header_drag_started and self._header_drag_start_pos:
            if event.buttons() & Qt.LeftButton:
                delta = event.globalPos() - self._header_drag_start_pos
                self.move(self.pos() + delta)
                self._header_drag_start_pos = event.globalPos()

    def _on_header_mouse_release(self, event: QMouseEvent):
        """鼠标释放：结束拖拽"""
        if event.button() == Qt.LeftButton:
            self._header_drag_start_pos = None
            self._header_drag_started = False

    def _on_header_double_click(self, event: QMouseEvent):
        """双击顶栏：切换最大化"""
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()

    def _create_sidebar(self) -> QWidget:
        """创建现代化侧边栏：分组导航"""
        side = QWidget()
        side.setObjectName("LimsSidebar")
        layout = QVBoxLayout(side)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(0)



        # 导航列表
        self._nav_list = QListWidget()
        self._nav_list.setObjectName("LimsNavList")
        self._nav_list.setFrameShape(QFrame.NoFrame)
        self._nav_list.setSpacing(4)
        self._nav_list.currentRowChanged.connect(self._on_nav_row_changed)
        self._nav_list.itemClicked.connect(self._on_nav_item_clicked)
        
        # 导航分组容器
        nav_container = QWidget()
        nav_container_layout = QVBoxLayout(nav_container)
        nav_container_layout.setContentsMargins(0, 8, 0, 0)
        nav_container_layout.setSpacing(0)

        # 分组1: 项目管理
        sec1 = QLabel("📁 项目管理")
        sec1.setObjectName("LimsSidebarSection")
        nav_container_layout.addWidget(sec1)
        nav_container_layout.addWidget(self._nav_list, 1)
        
        # 占位分组标签（将在 _setup_navigation_pages 中填充）
        self._sidebar_sections = {}
        
        # 分隔线和更多分组（预留位置给动态导航项）
        separator = QWidget()
        separator.setStyleSheet("""
            background: rgba(255, 255, 255, 0.1);
            min-height: 1px;
            margin: 12px 16px;
        """)
        nav_container_layout.addWidget(separator)

        # 底部版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.5);
            font-size: 15px;
            padding: 10px 24px;
        """)
        nav_container_layout.addWidget(version_label)
        
        layout.addWidget(nav_container, 1)
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

        # Pilot: isolated matrix preview entry (non-default, env-gated)
        preview_pilot_action = QAction("[PILOT] 打开隔离 Matrix 预览", self)
        preview_pilot_action.setShortcut("Ctrl+Alt+Shift+P")
        preview_pilot_action.triggered.connect(self._on_open_isolated_matrix_preview_pilot)
        preview_pilot_action.setFont(menu_font)
        close_preview_pilot_action = QAction("[PILOT] 关闭隔离 Matrix 预览", self)
        close_preview_pilot_action.setShortcut("Ctrl+Alt+Shift+L")
        close_preview_pilot_action.triggered.connect(self._on_close_isolated_matrix_preview_pilot)
        close_preview_pilot_action.setFont(menu_font)
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
        if MatrixSessionEntryFacade.is_preview_pilot_enabled(os.environ):
            self._register_action_shortcuts(preview_pilot_action, close_preview_pilot_action)

    def _initialize_controllers(self):
        """初始化控制器 - 采用延迟加载策略"""
        self.controller = MainWindowController(
            self,
            matrix_workspace_facade=self._workspace_facade,
        )
        
        # 其他控制器改为懒加载,在实际使用时才创建
        self._matrix_project_controller = None
        self._customer_report_controller = None
        self._report_wizard_controller = None
        self._document_parser_controller = None
        self._report_updater_controller = None

    @property
    def matrix_project_controller(self):
        """获取Matrix项目控制器 - 从主窗口控制器中获取"""
        if self.controller and hasattr(self.controller, 'matrix_project_controller'):
            return self.controller.matrix_project_controller
        return None
    
    @property
    def matrix_controller(self):
        """获取Matrix控制器 - 从主窗口控制器中获取"""
        if self.controller and hasattr(self.controller, 'matrix_project_controller'):
            return self.controller.matrix_project_controller.matrix_controller
        return None
    
    @property
    def customer_report_controller(self):
        """延迟加载客户报告控制器"""
        if self._customer_report_controller is None:
            logger.debug("Lazy loading CustomerReportController")
            self._customer_report_controller = CustomerReportController(self)
        return self._customer_report_controller
    
    @property
    def report_wizard_controller(self):
        """延迟加载报告向导控制器"""
        if self._report_wizard_controller is None:
            logger.debug("Lazy loading ReportWizardController")
            self._report_wizard_controller = ReportWizardController(self)
        return self._report_wizard_controller
    
    @property
    def document_parser_controller(self):
        """延迟加载文档解析控制器"""
        if self._document_parser_controller is None:
            logger.debug("Lazy loading DocumentParserController")
            self._document_parser_controller = DocumentParserController(self)
        return self._document_parser_controller
    
    @property
    def report_updater_controller(self):
        """延迟加载报告更新控制器"""
        if self._report_updater_controller is None:
            logger.debug("Lazy loading ReportUpdaterController")
            self._report_updater_controller = ReportUpdaterController(self)
        return self._report_updater_controller

    def _get_matrix_page_attr(self, attr_name: str):
        if self.matrix_page is None:
            return None
        return getattr(self.matrix_page, attr_name, None)

    @property
    def matrix_toolbar(self):
        return self._get_matrix_page_attr("matrix_toolbar")

    @property
    def matrix_table_widget(self):
        return self._get_matrix_page_attr("matrix_table_widget")

    @property
    def matrix_table_manager(self):
        return self._get_matrix_page_attr("matrix_table_manager")

    @property
    def matrix_data_sync_manager(self):
        return self._get_matrix_page_attr("matrix_data_sync_manager")

    @property
    def matrix_import_export_manager(self):
        return self._get_matrix_page_attr("matrix_import_export_manager")

    @property
    def matrix_event_handlers(self):
        return self._get_matrix_page_attr("matrix_event_handlers")

    @property
    def matrix_context_menus(self):
        return self._get_matrix_page_attr("matrix_context_menus")

    @property
    def matrix_copied_row_data(self):
        return self._get_matrix_page_attr("matrix_copied_row_data")

    @property
    def matrix_copied_col_data(self):
        return self._get_matrix_page_attr("matrix_copied_col_data")

    def _setup_navigation_pages(self):
        """注册侧栏条目与堆叠页面（所有菜单项改为侧栏直达）。"""
        # === Matrix 编辑器（默认首页）===
        self._setup_matrix_tab()
        self._register_nav_page(
            "📊 Matrix 编辑器",
            "项目管理 / Matrix 编辑器",
            self.matrix_tab,
            subtitle="编辑和管理测试流程矩阵",
            page_id="matrix.main",
        )
        
        # === 项目管理组 ===
        self._register_nav_page(
            "📁 新建项目", 
            "项目管理 / 新建项目", 
            self._create_placeholder_page("新建项目", "创建一个新的测试流程项目"),
            action=self._on_new_file,
            subtitle="创建一个新的测试流程项目"
        )
        self._register_nav_page(
            "📂 打开项目", 
            "项目管理 / 打开项目", 
            self._create_placeholder_page("打开项目", "从本地文件夹加载现有项目"),
            action=self._on_open_project,
            subtitle="从本地文件夹加载现有项目"
        )
        self._register_nav_page(
            "📋 查看LTR", 
            "项目管理 / 查看LTR", 
            self._create_placeholder_page("查看LTR", "浏览本地测试报告"),
            action=self._on_view_ltr,
            subtitle="浏览本地测试报告"
        )
        
        # === 报告管理组 ===
        self._register_nav_page(
            "✨ 创建报告", 
            "报告管理 / 创建报告", 
            self._create_placeholder_page("创建报告", "使用向导生成新的测试报告"),
            action=self._on_create_report,
            subtitle="使用向导生成新的测试报告"
        )
        self._register_nav_page(
            "🔄 更新报告", 
            "报告管理 / 更新报告", 
            self._create_placeholder_page("更新报告", "基于最新Matrix更新现有报告"),
            action=self._on_update_report,
            subtitle="基于最新Matrix更新现有报告"
        )
        self._register_nav_page(
            "👥 转客户版", 
            "报告管理 / 转客户版", 
            self._create_placeholder_page("转客户版", "生成去除敏感信息的客户版本"),
            action=self._on_convert_customer_version,
            subtitle="生成去除敏感信息的客户版本"
        )
        
        # === 测试表格组 ===
        self._register_nav_page(
            "📤 导出窗口矩阵", 
            "测试表格 / 导出窗口矩阵", 
            self._create_placeholder_page("导出窗口矩阵", "将Matrix导出为Excel文件"),
            action=self._on_export_matrix,
            subtitle="将Matrix导出为Excel文件"
        )
        self._register_nav_page(
            "📊 LLCR记录表", 
            "测试表格 / LLCR记录表", 
            self._create_placeholder_page("LLCR记录表", "导出LLCR格式记录表"),
            action=self._on_export_llcr,
            subtitle="导出LLCR格式记录表"
        )
        self._register_nav_page(
            "📄 CR记录表", 
            "测试表格 / CR记录表", 
            self._create_placeholder_page("CR记录表", "导出CR格式记录表"),
            action=self._on_export_cr,
            subtitle="导出CR格式记录表"
        )
        
        # === 工具箱组 ===
        self._register_nav_page(
            "📝 正文编辑器", 
            "工具箱 / 正文编辑器", 
            self._create_placeholder_page("正文编辑器", "编辑Word文档正文内容"),
            action=self._on_edit_body_content,
            subtitle="编辑Word文档正文内容"
        )
        self._register_nav_page(
            "🔐 文件加密", 
            "工具箱 / 文件加密", 
            self._create_placeholder_page("文件加密", "对测试文件进行加密保护"),
            action=self._on_encrypt_test_files,
            subtitle="对测试文件进行加密保护"
        )
        
        # === 其他 ===
        self._register_nav_page(
            "ℹ️ 关于", 
            "关于 TestFlow Manager", 
            self._create_placeholder_page("关于", "了解TestFlow Manager的更多信息"),
            action=self._on_about,
            subtitle="了解TestFlow Manager的更多信息"
        )

    def _register_nav_page(
        self,
        nav_title: str,
        breadcrumb_text: str,
        page: QWidget,
        *,
        action=None,
        subtitle: str = "",
        page_id: str = "",
    ) -> None:
        """
        添加侧栏一项并放入堆叠控件。

        Args:
            nav_title: 侧栏显示标题
            breadcrumb_text: 面包屑文本
            page: 页面对象
            action: 可选的触发动作函数（点击时执行）
            subtitle: 页面副标题描述
            page_id: 页面唯一标识符，用于页面可见性路由
        """
        if self._nav_list is None or self._page_stack is None:
            return
        index = len(self._nav_entries)
        self._nav_entries.append((nav_title, breadcrumb_text, subtitle, page_id))
        item = QListWidgetItem(nav_title)
        self._nav_list.addItem(item)
        self._page_stack.addWidget(page)

        # 注册动作映射
        if action:
            self._nav_actions[index] = action

        if self._nav_list.count() == 1:
            # 初始化期间设置默认选中，但不触发动作
            self._initializing_nav = True
            try:
                self._nav_list.setCurrentRow(0)
                self._apply_nav_index(0)
            finally:
                self._initializing_nav = False

    def _on_nav_row_changed(self, row: int) -> None:
        """侧栏选中行变化。"""
        if row < 0:
            return

        # 行变化只负责页面同步，动作统一交给点击事件触发。
        self._apply_nav_index(row)

    def _on_nav_item_clicked(self, item: QListWidgetItem) -> None:
        """侧栏点击事件：每次点击都执行动作（含重复点击同一项）。"""
        if self._initializing_nav:
            return
        if self._nav_list is None:
            return

        row = self._nav_list.row(item)
        if row < 0:
            return

        action_func = self._nav_actions.get(row)
        if not action_func:
            return

        try:
            action_func()
        except Exception as e:
            logger.error(f"执行侧栏动作失败: {e}", exc_info=True)

    def _apply_nav_index(self, index: int) -> None:
        """同步堆叠页、页标题与面包屑，并触发页面可见性事件。"""
        if self._page_stack is None or not self._nav_entries or index >= len(self._nav_entries):
            return
        self._page_stack.setCurrentIndex(index)
        entry = self._nav_entries[index]
        nav_title = entry[0]
        breadcrumb = entry[1]
        subtitle = entry[2] if len(entry) > 2 else ""
        page_id = entry[3] if len(entry) > 3 else ""

        # 保存当前页面 ID
        old_page_id = self._current_page_id
        self._current_page_id = page_id

        if self._page_title_label is not None:
            self._page_title_label.setText(nav_title)
        if self._breadcrumb_label is not None:
            self._breadcrumb_label.setText(f"📁 {breadcrumb}")
        if self._page_subtitle_label is not None:
            self._page_subtitle_label.setText(subtitle)

        # 触发页面可见性事件（Shell 只转发，Matrix 逻辑在 Facade 中处理）
        if old_page_id and old_page_id != page_id:
            # 旧页面隐藏
            if self.controller:
                self.controller.on_page_hidden(old_page_id)
        if page_id:
            self._on_page_visible(page_id)

    def _on_page_visible(self, page_id: str) -> None:
        """
        页面变为可见时调用 - Shell 只转发页面 ID，不含 Matrix 可见性策略。
        """
        if not self.controller:
            return
        self.controller.on_page_visible(page_id)

    def _create_placeholder_page(self, title: str, description: str = "") -> QWidget:
        """创建现代化的占位页面"""
        from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
        
        page = QWidget()
        page.setStyleSheet("""
            background-color: #fafbfc;
        """)
        
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        
        # 图标
        icon_label = QLabel("🚧")
        icon_label.setStyleSheet("""
            font-size: 72px;
            padding: 24px;
            background: white;
            border-radius: 50%;
            border: 2px solid #e2e8f0;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # 标题
        title_label = QLabel(f"{title}")
        title_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #2d3748;
            padding: 0px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 描述
        desc_text = description if description else "此功能正在开发中，敬请期待..."
        desc_label = QLabel(desc_text)
        desc_label.setStyleSheet("""
            font-size: 20px;
            color: #718096;
            padding: 0px;
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        
        # 卡片容器
        card = QWidget()
        card.setStyleSheet("""
            background: white;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            padding: 60px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(60, 60, 60, 60)
        card_layout.setSpacing(20)
        card_layout.setAlignment(Qt.AlignCenter)
        
        card_layout.addWidget(icon_label)
        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        
        layout.addWidget(card)
        return page

    def _setup_matrix_tab(self):
        """Matrix 主内容页 - 通过 MatrixPage 接入主窗口。

        MatrixPage 由 Facade 注入，Shell 不直接操作 session 绑定。
        """
        if self.matrix_page is None:
            self.matrix_page = MatrixPage(self.matrix_controller, self)
            # 通过 controller 设置 MatrixPage 引用，打破直接依赖
            if self.controller and hasattr(self.controller, "set_matrix_page"):
                self.controller.set_matrix_page(self.matrix_page)

        self.matrix_tab = self.matrix_page

        if hasattr(self, '_page_stack') and self._page_stack:
            self._page_stack.currentChanged.connect(self._on_page_changed_for_matrix)
    
    def sync_to_model(self) -> None:
        if self.matrix_page:
            self.matrix_page.sync_to_model()
    
    def refresh_table(self) -> None:
        if self.matrix_page:
            self.matrix_page.refresh_table()
    
    def save_merged_cells_info(self) -> None:
        if self.matrix_page:
            self.matrix_page.save_merged_cells_info()
    
    def auto_import_from_project(self) -> None:
        if self.matrix_page:
            self.matrix_page.auto_import_from_project()

    def set_matrix_project_context(self, project_context) -> None:
        if self.matrix_page:
            self.matrix_page.set_project_context(project_context)

    def has_matrix_workspace(self) -> bool:
        return self.matrix_page is not None

    def activate_matrix_workspace(self) -> bool:
        """
        激活 Matrix 工作区 - 通过 page_id 查找而非硬编码索引。
        
        Returns:
            是否成功激活
        """
        if self.matrix_page is None:
            return False
        
        # 通过 page_id 查找 Matrix 页面索引
        matrix_index = None
        for i, entry in enumerate(self._nav_entries):
            if len(entry) > 3 and entry[3] == "matrix.main":
                matrix_index = i
                break
        
        if matrix_index is None:
            return False

        if self._nav_list is not None:
            self._nav_list.setCurrentRow(matrix_index)
            return True

        if self._page_stack is not None:
            self._apply_nav_index(matrix_index)
            return True

        return False

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

    def nativeEvent(self, event_type, message):
        """在 Windows 无边框模式下启用系统边缘缩放。"""
        if (
            os.name != "nt"
            or self.isMaximized()
            or self.isFullScreen()
            or event_type != "windows_generic_MSG"
        ):
            return super().nativeEvent(event_type, message)

        msg = ctypes.wintypes.MSG.from_address(int(message))
        WM_NCHITTEST = 0x0084
        if msg.message != WM_NCHITTEST:
            return super().nativeEvent(event_type, message)

        HTLEFT = 10
        HTRIGHT = 11
        HTTOP = 12
        HTTOPLEFT = 13
        HTTOPRIGHT = 14
        HTBOTTOM = 15
        HTBOTTOMLEFT = 16
        HTBOTTOMRIGHT = 17

        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
        pos = self.mapFromGlobal(QPoint(x, y))
        rect = self.rect()
        border = self._resize_border_width

        on_left = pos.x() <= border
        on_right = pos.x() >= rect.width() - border
        on_top = pos.y() <= border
        on_bottom = pos.y() >= rect.height() - border

        if on_top and on_left:
            return True, HTTOPLEFT
        if on_top and on_right:
            return True, HTTOPRIGHT
        if on_bottom and on_left:
            return True, HTBOTTOMLEFT
        if on_bottom and on_right:
            return True, HTBOTTOMRIGHT
        if on_left:
            return True, HTLEFT
        if on_right:
            return True, HTRIGHT
        if on_top:
            return True, HTTOP
        if on_bottom:
            return True, HTBOTTOM

        return super().nativeEvent(event_type, message)

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
        result = self.matrix_controller.handle_export_matrix_to_excel()
        if result.get("success"):
            self._update_status()
        elif result.get("message"):
            QMessageBox.warning(self, "错误", result["message"])

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
        self.report_wizard_controller.set_project_context(self.controller.project_context)
        self.report_wizard_controller.set_matrix_controller(self.matrix_controller)
        self.report_wizard_controller.show_wizard()
        self._update_status()

    def _on_update_report(self) -> None:
        logger.debug("Update report action triggered")
        self.report_updater_controller.set_project_context(self.controller.project_context)
        self.report_updater_controller.show_report_updater_dialog()
        self._update_status()

    def _on_convert_customer_version(self) -> None:
        logger.debug("Convert to customer version action triggered")
        if self.customer_report_controller.handle_generate_customer_report_with_context(self.controller.project_context):
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

    def _on_open_isolated_matrix_preview_pilot(self) -> None:
        logger.debug("Open isolated matrix preview pilot action triggered")
        if self.controller and hasattr(self.controller, "handle_open_isolated_matrix_preview_pilot"):
            session_id = self.controller.handle_open_isolated_matrix_preview_pilot()
            if session_id:
                self._update_status()

    def _on_close_isolated_matrix_preview_pilot(self) -> None:
        logger.debug("Close isolated matrix preview pilot action triggered")
        if self.controller and hasattr(self.controller, "handle_close_isolated_matrix_preview_pilot"):
            if self.controller.handle_close_isolated_matrix_preview_pilot():
                self._update_status()

    def _update_status(self) -> None:
        """更新状态栏"""
        status = self.controller.get_status()
        self.status_label.setText(status)

    def _on_page_changed_for_matrix(self, index: int) -> None:
        """
        页面切换信号处理 - Shell 只转发页面 ID，不含 Matrix 可见性策略。

        页面可见性逻辑已移至 MatrixWorkspaceFacade.on_page_visible()。
        """
        # 获取当前页面 ID（通过索引查找）
        page_id = ""
        if 0 <= index < len(self._nav_entries):
            entry = self._nav_entries[index]
            page_id = entry[3] if len(entry) > 3 else ""

        # Shell 只转发页面变更，不直接操作 Matrix
        if page_id and self.controller:
            self.controller.on_page_visible(page_id)
        elif not page_id and self.controller:
            # 非 Matrix 页面，通知隐藏
            self.controller.on_page_hidden(self._current_page_id)
    
    def _initialize_matrix_table(self):
        """初始化Matrix表格数据 - 启动时调用"""
        try:
            if self.matrix_page:
                self.matrix_page.initialize_table()
        except Exception as e:
            logger.error(f"初始化Matrix表格失败: {e}", exc_info=True)

    def closeEvent(self, event) -> None:
        logger.info("MainWindow closing")
        self.controller.shutdown()
        event.accept()
