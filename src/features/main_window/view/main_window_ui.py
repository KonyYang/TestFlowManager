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
    QMessageBox,
    QTableWidget,
    QHeaderView,
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
# Matrix UI 组件直接集成
from src.features.matrix.view.components.matrix_toolbar import MatrixToolbar
from src.features.matrix.view.components.matrix_context_menus import MatrixContextMenus
from src.features.matrix.view.managers.table_manager import TableManager
from src.features.matrix.view.managers.data_sync_manager import DataSyncManager
from src.features.matrix.view.managers.import_export_manager import ImportExportManager
from src.features.matrix.view.handlers.matrix_event_handlers import MatrixEventHandlers


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

    def __init__(self, splash_screen=None):
        super().__init__()
        self.splash_screen = splash_screen
        self.controller = None
        
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
        self._nav_entries: List[Tuple[str, str, str]] = []
        
        # DL编号显示标签
        self._dl_number_label: Optional[QLabel] = None
        
        # 侧栏导航动作映射（索引 -> 动作函数）
        self._nav_actions = {}
        
        # 初始化期间禁止自动触发动作
        self._initializing_nav = False
        
        # Matrix UI 组件（直接集成到主窗口）
        self.matrix_tab: Optional[QWidget] = None
        self.matrix_toolbar: Optional[MatrixToolbar] = None
        self.matrix_table_widget: Optional[QTableWidget] = None
        self.matrix_table_manager: Optional[TableManager] = None
        self.matrix_data_sync_manager: Optional[DataSyncManager] = None
        self.matrix_import_export_manager: Optional[ImportExportManager] = None
        self.matrix_event_handlers: Optional[MatrixEventHandlers] = None
        self.matrix_context_menus: Optional[MatrixContextMenus] = None
        self.matrix_copied_row_data = None
        self.matrix_copied_col_data = None

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
        """初始化控制器 - 采用延迟加载策略"""
        # 只初始化核心控制器
        self.controller = MainWindowController(self)
        
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

    def _setup_navigation_pages(self):
        """注册侧栏条目与堆叠页面（所有菜单项改为侧栏直达）。"""
        # === Matrix 编辑器（默认首页）===
        self.matrix_tab = QWidget()
        self._setup_matrix_tab()
        self._register_nav_page(
            "📊 Matrix 编辑器", 
            "项目管理 / Matrix 编辑器",
            self.matrix_tab,
            subtitle="编辑和管理测试流程矩阵"
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
            "📊 LLCR报告", 
            "测试表格 / LLCR报告", 
            self._create_placeholder_page("LLCR报告", "导出LLCR格式报告"),
            action=self._on_export_llcr,
            subtitle="导出LLCR格式报告"
        )
        self._register_nav_page(
            "📄 CR报告", 
            "测试表格 / CR报告", 
            self._create_placeholder_page("CR报告", "导出CR格式报告"),
            action=self._on_export_cr,
            subtitle="导出CR格式报告"
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

    def _register_nav_page(self, nav_title: str, breadcrumb_text: str, page: QWidget, 
                           action=None, subtitle: str = "") -> None:
        """
        添加侧栏一项并放入堆叠控件。
        
        Args:
            nav_title: 侧栏显示标题
            breadcrumb_text: 面包屑文本
            page: 页面对象
            action: 可选的触发动作函数（点击时执行）
            subtitle: 页面副标题描述
        """
        if self._nav_list is None or self._page_stack is None:
            return
        index = len(self._nav_entries)
        self._nav_entries.append((nav_title, breadcrumb_text, subtitle))
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
        
        # 初始化期间不执行动作函数
        if not self._initializing_nav:
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
        entry = self._nav_entries[index]
        nav_title = entry[0]
        breadcrumb = entry[1]
        subtitle = entry[2] if len(entry) > 2 else ""
        
        if self._page_title_label is not None:
            self._page_title_label.setText(nav_title)
        if self._breadcrumb_label is not None:
            self._breadcrumb_label.setText(f"📁 {breadcrumb}")
        if self._page_subtitle_label is not None:
            self._page_subtitle_label.setText(subtitle)

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
        """Matrix 主内容页 - 直接集成 Matrix UI 组件（现代化样式）"""
        layout = QVBoxLayout(self.matrix_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 使用外部工具栏组件
        self.matrix_toolbar = MatrixToolbar(self.matrix_controller.service, self)
        layout.addWidget(self.matrix_toolbar.get_widget())
        
        # 表格区域
        self.matrix_table_widget = QTableWidget()
        
        # 设置表格样式
        self.matrix_table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #edf2f7;
                selection-background-color: #bee3f8;
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
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f7fafc, stop:1 #edf2f7);
                color: #4a5568;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #cbd5e0;
                font-weight: bold;
                font-size: 16px;
            }
            QHeaderView::section:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #edf2f7, stop:1 #e2e8f0);
            }
        """)
        
        # 设置水平表头可以手动调整列宽
        self.matrix_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 设置垂直表头可以手动调整行高
        self.matrix_table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.matrix_table_widget.verticalHeader().setVisible(True)  # 显示行号
        self.matrix_table_widget.setAlternatingRowColors(True)  # 交替行颜色
        
        # 初始化组件管理器
        self.matrix_table_manager = TableManager(self, self.matrix_controller.service)
        self.matrix_data_sync_manager = DataSyncManager(self, self.matrix_controller.service)
        self.matrix_import_export_manager = ImportExportManager(self, self.matrix_controller.service)
        self.matrix_event_handlers = MatrixEventHandlers(self, self.matrix_controller.service)
        self.matrix_context_menus = MatrixContextMenus(self, self.matrix_controller.service)
        
        # 启用单元格的右键菜单
        self.matrix_table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.matrix_table_widget.customContextMenuRequested.connect(self.matrix_context_menus.show_cell_context_menu)
        # 连接行头和列头的右键菜单事件
        self.matrix_table_widget.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.matrix_table_widget.verticalHeader().customContextMenuRequested.connect(self.matrix_context_menus.show_row_context_menu)
        self.matrix_table_widget.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.matrix_table_widget.horizontalHeader().customContextMenuRequested.connect(self.matrix_context_menus.show_col_context_menu)
        # 连接选择变化信号以更新菜单状态
        self.matrix_table_widget.itemSelectionChanged.connect(self._on_matrix_item_selection_changed)
        # 设置选择模式为连续选择
        self.matrix_table_widget.setSelectionMode(QTableWidget.ContiguousSelection)
        self.matrix_table_widget.setSelectionBehavior(QTableWidget.SelectItems)
        
        # 设置表格初始状态 - 延迟到首次访问时再更新
        # self.matrix_table_manager.update_table()  # 注释掉启动时的立即更新
        
        # 连接信号到事件处理器
        self.matrix_toolbar.connect_signals(self.matrix_event_handlers)
        
        # 添加表格到布局
        layout.addWidget(self.matrix_table_widget)
        
        # 监听页面切换,首次显示Matrix页面时才更新表格
        if hasattr(self, '_page_stack') and self._page_stack:
            self._page_stack.currentChanged.connect(self._on_page_changed_for_matrix)
        
        # 连接表格项变更信号
        self.matrix_table_widget.itemChanged.connect(self._on_item_changed)
        
        # Matrix是默认首页，需要立即加载数据
        # 使用QTimer延迟执行，确保UI完全初始化后再加载数据
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._initialize_matrix_table)
        
        # 在初始化后自动导入项目中的matrix.xlsx文件（如果存在）
        # 注意：auto_import已在_initialize_matrix_table中调用，这里注释掉避免重复
        # self.matrix_import_export_manager.auto_import_matrix_from_project()
    
    def _on_matrix_item_selection_changed(self):
        """Matrix 表格选择项变化时的处理"""
        logger.debug("Matrix 表格选择项发生变化")
        # 更新菜单状态
        if hasattr(self.matrix_context_menus, 'update_cell_menu_actions'):
            self.matrix_context_menus.update_cell_menu_actions()
    
    def _matrix_sync_table_to_model(self):
        """同步 Matrix 表格数据到模型"""
        self.matrix_data_sync_manager.sync_table_to_model()
    
    def _matrix_update_table(self):
        """更新 Matrix 表格显示"""
        self.matrix_table_manager.update_table()
    
    def _matrix_save_merged_cells_info(self):
        """保存 Matrix 合并单元格信息"""
        self.matrix_data_sync_manager.save_merged_cells_info()
    
    def _matrix_auto_import_from_project(self):
        """从项目文件夹自动导入 matrix.xlsx 文件"""
        self.matrix_import_export_manager.auto_import_matrix_from_project()

    # --- Matrix 事件处理委托 (Delegate to handlers) ---
    def _on_item_changed(self, item):
        """处理表格项变更事件"""
        try:
            row = item.row()
            col = item.column()
            value = item.text()
            logger.debug(f"Matrix 表格项变更: [{row},{col}] = '{value}'")
            # 更新数据模型
            self.matrix_controller.service.set_cell_value(row, col, value)
        except Exception as e:
            logger.error(f"处理 Matrix 表格项变更时出错: {e}", exc_info=True)

    def _merge_or_split_cells(self):
        """根据选中单元格的状态执行合并或拆分操作"""
        from src.features.matrix.service.matrix_cell_service import MatrixCellService
        cell_service = MatrixCellService(self.matrix_controller.service)
        cell_service.merge_or_split_cells(self.matrix_table_widget)

    def _undo_cell_operation(self):
        """撤销单元格操作"""
        self.matrix_controller.service.undo_cell_operation()

    def _redo_cell_operation(self):
        """重做单元格操作"""
        self.matrix_controller.service.redo_cell_operation()

    # --- Matrix 行/列操作委托 (Delegate to table_manager) ---
    def _add_row(self):
        self._matrix_sync_table_to_model()
        self.matrix_table_manager.add_row()

    def _insert_row(self):
        selected_rows = self.matrix_table_widget.selectionModel().selectedRows()
        if selected_rows:
            self._matrix_sync_table_to_model()
            self.matrix_table_manager.insert_row(selected_rows[0].row())
        else:
            QMessageBox.warning(self, "操作失败", "请选择一行")

    def _move_row_at(self, row):
        self._matrix_sync_table_to_model()
        self.matrix_table_manager.move_row(row)

    def _copy_row(self, row):
        self.matrix_copied_row_data = self.matrix_table_manager.copy_row(row)

    def _paste_row(self, row):
        self._matrix_sync_table_to_model()
        self.matrix_table_manager.paste_row(row)

    def _remove_row(self):
        selected_rows = self.matrix_table_widget.selectionModel().selectedRows()
        if selected_rows:
            self._matrix_sync_table_to_model()
            self.matrix_table_manager.remove_row(selected_rows[0].row())
        else:
            QMessageBox.warning(self, "操作失败", "请选择一行")

    def _add_column(self):
        self._matrix_sync_table_to_model()
        self.matrix_table_manager.add_column()

    def _insert_column(self):
        selected_cols = self.matrix_table_widget.selectionModel().selectedColumns()
        if selected_cols:
            self._matrix_sync_table_to_model()
            self.matrix_table_manager.insert_column(selected_cols[0].column())
        else:
            QMessageBox.warning(self, "操作失败", "请选择一列")

    def _move_column(self, col):
        self._matrix_sync_table_to_model()
        self.matrix_table_manager.move_column(col)

    def _copy_column(self, col):
        self.matrix_copied_col_data = self.matrix_table_manager.copy_column(col)

    def _paste_column(self, col):
        self._matrix_sync_table_to_model()
        self.matrix_table_manager.paste_column(col)

    def _remove_column(self):
        selected_cols = self.matrix_table_widget.selectionModel().selectedColumns()
        if selected_cols:
            self._matrix_sync_table_to_model()
            self.matrix_table_manager.remove_column(selected_cols[0].column())
        else:
            QMessageBox.warning(self, "操作失败", "请选择一列")

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

    def _on_page_changed_for_matrix(self, index: int) -> None:
        """页面切换时延迟加载Matrix表格数据"""
        # Matrix页面是索引0
        if index == 0 and hasattr(self, 'matrix_table_manager'):
            # 检查是否已经初始化过
            if not getattr(self, '_matrix_table_initialized', False):
                logger.debug("首次显示Matrix页面，延迟加载表格数据")
                try:
                    self.matrix_table_manager.update_table()
                    self._matrix_table_initialized = True
                    logger.debug("Matrix表格数据加载完成")
                except Exception as e:
                    logger.error(f"延迟加载Matrix表格失败: {e}")
    
    def _initialize_matrix_table(self):
        """初始化Matrix表格数据 - 启动时调用"""
        try:
            logger.debug("开始初始化Matrix表格数据")
            # 先更新表格结构
            self.matrix_table_manager.update_table()
            # 标记为已初始化
            self._matrix_table_initialized = True
            # 尝试自动导入项目中的matrix.xlsx
            self.matrix_import_export_manager.auto_import_matrix_from_project()
            logger.debug("Matrix表格初始化完成")
        except Exception as e:
            logger.error(f"初始化Matrix表格失败: {e}", exc_info=True)

    def closeEvent(self, event) -> None:
        logger.info("MainWindow closing")
        self.controller.shutdown()
        event.accept()
