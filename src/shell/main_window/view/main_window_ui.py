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
from src.common.ui.font_utils import FontUtils
from src.shell.main_window.controller.main_window_controller import MainWindowController
from src.shell.main_window.integration.main_window_feature_facade import MainWindowFeatureFacade
from src.shell.main_window.components.header_components import HeaderComponents
from src.shell.main_window.components.sidebar_components import SidebarComponents
from src.shell.main_window.components.page_factory import PageFactory
from src.shell.main_window.components.layout_builder import MainWindowLayoutBuilder
from src.shell.main_window.components.startup_profiler import StartupProfiler
from src.shell.main_window.view.window_chrome_manager import WindowChromeManager
from src.shell.main_window.view.handlers.file_handlers import FileActionHandlers
from src.shell.main_window.view.handlers.export_handlers import ExportActionHandlers
from src.shell.main_window.view.handlers.report_handlers import ReportActionHandlers
from src.shell.main_window.view.handlers.tool_handlers import ToolActionHandlers
from src.shell.navigation import NavigationManager, NavigationEntry, NavigationRegistry, ShortcutRegistry

from src.features.matrix.workspace.matrix_workspace_facade import MatrixWorkspaceFacade


# 主窗口 Lims 风格全局样式（从 constants 模块导入）
from src.shell.main_window.constants.main_window_styles import LIMS_APP_STYLESHEET


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
        project_session_coordinator=None,  # Phase 4: 从 Assembler 注入
        project_session_app_service=None,  # S1-2: 应用层编排器
    ):
        super().__init__()
        self.splash_screen = splash_screen
        self.controller = None
        self._project_session_coordinator = project_session_coordinator  # Phase 4
        self._project_session_app_service = project_session_app_service  # S1-2

        # 通过 facade 统一访问所有 Matrix session 对象（私有属性，不对外暴露）
        self._workspace_facade = matrix_workspace_facade or MatrixWorkspaceFacade(parent_view=self)

        # Feature registry for shell-triggered feature controllers
        self._feature_registry = None

        self.is_custom_sized = False
        self.custom_geometry = None
        self.fullscreen_geometry = None

        # UI 组件管理器（Step 7.x: 抽取 UI 组件）
        self._header_components = HeaderComponents(self)
        self._sidebar_components = SidebarComponents(self)

        # Action Handlers（Step P1: 抽取动作处理器）
        self._file_handlers = FileActionHandlers(self)
        self._export_handlers = ExportActionHandlers(self)
        self._report_handlers = ReportActionHandlers(self)
        self._tool_handlers = ToolActionHandlers(self)

        # 窗口行为管理器（Phase 2: 抽取窗口行为）
        self._chrome_manager = WindowChromeManager(self)

        # 导航管理器（✅ 使用通用的 NavigationManager）
        self._nav_controller: Optional[NavigationManager] = None

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
        # Step 8: matrix_page 由 facade 创建，shell 只持有引用
        self.matrix_tab: Optional[QWidget] = None
        self.matrix_page: Optional[QWidget] = None  # 实际是 MatrixPage，但避免直接导入

        self._initialize_step_by_step()
        self._update_status()

    def _initialize_step_by_step(self):
        """
        分步初始化主窗口组件（使用 StartupProfiler 性能监控）。
        
        架构说明：
        - ✅ 已集成 StartupProfiler，统一管理性能监控
        - ✅ 自动记录各阶段耗时并生成性能报告
        - ✅ 支持启动画面进度更新和 Qt 信号通知
        """
        # 创建性能分析器
        profiler = StartupProfiler(
            splash_screen=self.splash_screen,
            progress_signal=self.startup_progress,
        )
        profiler.start()
        
        try:
            # === 第1阶段：基础 UI 初始化 ===
            with profiler.phase("基础UI初始化", "正在初始化基础界面..."):
                self._setup_basic_ui()

            # === 第2阶段：控制器初始化 ===
            with profiler.phase("控制器初始化", "正在初始化控制器..."):
                self._initialize_controllers()

            # === 第3阶段：快捷键和状态栏 ===
            with profiler.phase("快捷键和状态栏", "正在设置快捷键与状态栏..."):
                self._setup_global_shortcuts()
                self._setup_status_bar()

            # === 第4阶段：导航和页面 ===
            with profiler.phase("导航和页面", "正在设置主导航与页面..."):
                self._setup_navigation_pages()

            # === 第5阶段：业务逻辑 ===
            with profiler.phase("业务逻辑", "正在初始化业务逻辑..."):
                if self.controller:
                    self.controller.initialize()

            # === 记录性能摘要 ===
            profiler.log_summary()

        except Exception as e:
            logger.error(f"主窗口初始化过程中出错: {e}")
            raise

    def _notify_progress(self, step, message):
        """通知启动进度"""
        if self.splash_screen:
            self.splash_screen.update_progress(step, message)
        self.startup_progress.emit(step, message)

    def _on_navigation_changed(self, title: str, breadcrumb: str, subtitle: str) -> None:
        """
        导航变化回调（由 NavigationManager 触发）
        
        Args:
            title: 页面标题
            breadcrumb: 面包屑文本
            subtitle: 副标题描述
        """
        if self._page_title_label is not None:
            self._page_title_label.setText(title)
        if self._breadcrumb_label is not None:
            self._breadcrumb_label.setText(f"📁 {breadcrumb}")
        if self._page_subtitle_label is not None:
            self._page_subtitle_label.setText(subtitle)
        
        # 触发页面可见性事件（通过当前选中的条目获取 page_id）
        if self._nav_controller:
            current_entry = self._nav_controller.get_current_entry()
            if current_entry and current_entry.page_id:
                old_page_id = self._current_page_id
                new_page_id = current_entry.page_id
                
                # 保存当前页面 ID
                self._current_page_id = new_page_id
                
                # 触发旧页面隐藏事件
                if old_page_id and old_page_id != new_page_id:
                    if self.controller:
                        self.controller.on_page_hidden(old_page_id)
                
                # 触发新页面可见事件
                self._on_page_visible(new_page_id)

    def _setup_basic_ui(self):
        """
        设置基础用户界面（委托给 LayoutBuilder）。
        
        架构说明：
        - ✅ 已集成 MainWindowLayoutBuilder，集中管理布局组装逻辑
        - ✅ 布局结构与主窗口解耦，易于维护和测试
        - ✅ 样式统一由 constants/main_window_styles.py 管理
        """
        # === 第1步：配置窗口基础属性 ===
        self._configure_window_properties()
        
        # === 第2步：创建核心组件 ===
        header = self._header_components.create_app_header()
        sidebar = self._sidebar_components.create_sidebar()
        page_stack = QStackedWidget()
        page_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # === 第3步：通过 LayoutBuilder 组装布局 ===
        central_widget, components = MainWindowLayoutBuilder.build_main_layout(
            header_widget=header,
            sidebar_widget=sidebar,
            page_stack=page_stack,
        )
        
        # === 第4步：保存组件引用 ===
        self._page_stack = page_stack
        self._main_column = components['main_column']
        self._page_title_label = self._main_column._page_title_label
        self._page_subtitle_label = self._main_column._page_subtitle_label
        
        # === 第5步：设置中央部件和样式 ===
        self.setCentralWidget(central_widget)
        self.setStyleSheet(LIMS_APP_STYLESHEET)
        
        # === 第6步：隐藏原生菜单栏 ===
        native_menubar = self.menuBar()
        if native_menubar is not None:
            native_menubar.hide()

    def _configure_window_properties(self):
        """
        配置窗口基础属性
        
        包括：
        - 无边框窗口模式
        - 窗口标题和图标
        - 窗口尺寸和位置
        - 全局字体
        """
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



    def _toggle_maximize(self):
        """切换最大化状态"""
        self._chrome_manager._toggle_maximize()

    def _toggle_fullscreen(self):
        """切换全屏模式"""
        self._chrome_manager.toggle_fullscreen()
    
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
        self._chrome_manager.handle_mouse_press(event)

    def _on_header_mouse_move(self, event: QMouseEvent):
        """鼠标移动：拖拽窗口"""
        self._chrome_manager.handle_mouse_move(event)

    def _on_header_mouse_release(self, event: QMouseEvent):
        """鼠标释放：结束拖拽"""
        self._chrome_manager.handle_mouse_release(event)

    def _on_header_double_click(self, event: QMouseEvent):
        """双击顶栏：切换最大化"""
        self._chrome_manager.handle_double_click(event)

    def _setup_global_shortcuts(self):
        """
        注册全局快捷键（通过 ShortcutRegistry）。
        
        架构说明：
        - ✅ 已集成 ShortcutRegistry，集中管理所有全局快捷键
        - ✅ 快捷键配置与 UI 层解耦，易于维护和测试
        - ✅ 支持条件性注册（如 Pilot 功能）
        """
        ShortcutRegistry.register_all_shortcuts(
            window=self,
            file_handlers=self._file_handlers,
            export_handlers=self._export_handlers,
            report_handlers=self._report_handlers,
            tool_handlers=self._tool_handlers,
            workspace_facade=self._workspace_facade,
        )

    def _initialize_controllers(self):
        """初始化控制器 - 采用延迟加载策略"""
        # Phase 4: 使用从 Assembler 注入的 ProjectSessionCoordinator
        # S1-2: 传递应用层编排器
        self.controller = MainWindowController(
            self,
            matrix_workspace_facade=self._workspace_facade,
            project_session_coordinator=self._project_session_coordinator,
            project_session_app_service=self._project_session_app_service,
        )

        # Feature registry: shell-triggered feature controller assembly
        self._feature_registry = MainWindowFeatureFacade(self)

        # Matrix project controller remains lazy (accessed via controller)
        self._matrix_project_controller = None

    @property
    def matrix_project_controller(self):
        """获取Matrix项目控制器 - 从主窗口控制器中获取"""
        if self.controller and hasattr(self.controller, 'matrix_project_controller'):
            return self.controller.matrix_project_controller
        return None

    def _setup_navigation_pages(self):
        """
        注册侧栏条目与堆叠页面（使用 NavigationManager + NavigationRegistry）。
        
        架构说明：
        - ✅ 已集成 NavigationManager，简化导航管理逻辑
        - ✅ 已集成 NavigationRegistry，集中管理导航条目配置
        - ✅ 导航管理器位于 src/shell/navigation/，可被其他窗口复用
        - ✅ 通过 NavigationEntry 数据类统一管理导航条目
        """
        # 初始化导航控制器
        if self._nav_list is not None and self._page_stack is not None:
            self._nav_controller = NavigationManager(
                nav_list=self._nav_list,
                page_stack=self._page_stack,
                entry_callback=self._on_navigation_changed,
            )
        else:
            logger.error("导航控件未初始化，无法创建 NavigationManager")
            return
        
        # === Matrix 编辑器（默认首页）===
        self._setup_matrix_tab()
        
        # === 通过注册表注册所有导航条目 ===
        NavigationRegistry.register_all_entries(
            nav_controller=self._nav_controller,
            matrix_tab=self.matrix_tab,
            file_handlers=self._file_handlers,
            export_handlers=self._export_handlers,
            report_handlers=self._report_handlers,
            tool_handlers=self._tool_handlers,
            placeholder_factory=PageFactory.create_placeholder_page,
        )

    def _on_page_visible(self, page_id: str) -> None:
        """
        页面变为可见时调用 - Shell 只转发页面 ID，不含 Matrix 可见性策略。
        
        注意：此方法由 NavigationManager 的回调间接调用。
        """
        if not self.controller:
            return
        self.controller.on_page_visible(page_id)



    def _setup_matrix_tab(self):
        """Matrix 主内容页 - 通过 Facade 获取 MatrixPage。

        Step 8: Shell 不再直接构造 MatrixPage，而是通过 facade 获取。
        Facade 成为 page 的拥有者，shell 只负责将 widget 放入 UI。
        """
        if self.matrix_page is None:
            # 通过 controller 获取 matrix_controller，避免直接依赖
            matrix_controller = self.controller.get_matrix_controller() if self.controller else None
            self.matrix_page = self._workspace_facade.get_or_create_matrix_page(
                self,
                matrix_controller,
            )

        self.matrix_tab = self.matrix_page

    def sync_to_model(self) -> None:
        """Step 8: 通过 facade 代理调用"""
        self._workspace_facade.sync_matrix_to_model()

    def refresh_table(self) -> None:
        """Step 8: 通过 facade 代理调用"""
        self._workspace_facade.refresh_matrix_table()

    def save_merged_cells_info(self) -> None:
        """Step 8: 通过 facade 代理调用"""
        self._workspace_facade.save_matrix_merged_cells_info()

    def auto_import_from_project(self) -> None:
        """Step 8: 通过 facade 代理调用"""
        self._workspace_facade.auto_import_matrix_from_project()

    def set_matrix_project_context(self, project_context) -> None:
        """Step 8: 通过 facade 代理调用"""
        self._workspace_facade.set_matrix_project_context(project_context)

    def has_matrix_workspace(self) -> bool:
        return self.matrix_page is not None

    def activate_matrix_workspace(self) -> bool:
        if self.matrix_page is None:
            return False

        if self._nav_list is not None:
            self._nav_list.setCurrentRow(0)
            return True

        if self._page_stack is not None:
            self._apply_nav_index(0)
            return True

        return False

    def _set_window_icon(self):
        """设置窗口图标（兼容开发和打包模式）"""
        try:
            from src.core.path_utils import get_resource_path
            icon_path = get_resource_path("resources", "icons", "app_icon.png")
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
        self._chrome_manager.handle_window_state_change(event)
        if event.type() == event.WindowStateChange and hasattr(self, '_maximize_btn') and self._maximize_btn:
            if self.isMaximized():
                self._maximize_btn.icon = "❐"
            else:
                self._maximize_btn.icon = "□"
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def showNormal(self):
        """显示正常大小窗口"""
        self._chrome_manager.show_normal()

    def showMaximized(self):
        """显示最大化窗口"""
        self._chrome_manager.show_maximized()

    def nativeEvent(self, event_type, message):
        """在 Windows 无边框模式下启用系统边缘缩放（委托给 WindowChromeManager）"""
        handled, result = self._chrome_manager.native_event(event_type, message)
        if handled:
            return True, result
        return super().nativeEvent(event_type, message)

    def showMinimized(self):
        """显示最小化窗口"""
        self._chrome_manager.show_minimized()

    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        status_font = FontUtils.get_scaled_font(8)
        self.status_bar.setFont(status_font)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(status_font)
        self.status_bar.addWidget(self.status_label)

    def _update_status(self) -> None:
        """更新状态栏"""
        status = self.controller.get_status()
        self.status_label.setText(status)

    def _initialize_matrix_table(self):
        """初始化Matrix表格数据 - 启动时调用

        Step 8: 通过 facade 代理调用
        """
        try:
            self._workspace_facade.initialize_matrix_table()
        except Exception as e:
            logger.error(f"初始化Matrix表格失败: {e}", exc_info=True)

    def closeEvent(self, event) -> None:
        logger.info("MainWindow closing")
        self.controller.shutdown()
        event.accept()
