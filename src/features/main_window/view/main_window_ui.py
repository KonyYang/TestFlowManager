"""
主窗口UI模块
定义主窗口的用户界面
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenuBar, QMenu, QAction, QStatusBar, QToolBar
from PyQt5.QtCore import Qt

from src.core import config_manager
from src.core.logger import logger
from src.features.main_window.controller.main_window_controller import MainWindowController
from PyQt5.QtGui import QFont
from src.core.font_utils import FontUtils
from src.core.window_utils import WindowUtils  # 导入窗口工具类

class MainWindow(QMainWindow):
    """
    主窗口类
    应用程序的主窗口界面
    """

    def __init__(self):
        super().__init__()
        self.controller = MainWindowController(self)
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_status_bar()

        # 初始化控制器
        self.controller.initialize()

        # 更新界面状态
        self._update_status()

    def _setup_ui(self) -> None:
        """设置用户界面"""
        # 设置窗口属性
        self.setWindowTitle("TestFlow Manager")
        # 根据DPI调整窗口尺寸，使用更小的默认尺寸
        from src.core.config_manager import config_manager
        # print(f"[DEBUG] All config: {config_manager.get_all()}")
        base_width = config_manager.get("window.width", 800)
        base_height = config_manager.get("window.height", 600)
        # print(f"[DEBUG] Base window size from config: {base_width}x{base_height}")
        
        width = WindowUtils.get_scaled_size(base_width)
        height = WindowUtils.get_scaled_size(base_height)
        # print(f"[DEBUG] Scaled window size: {width}x{height}")
        
        self.resize(width, height)
        # 设置更小的最小尺寸限制
        min_width = WindowUtils.get_scaled_size(200)
        min_height = WindowUtils.get_scaled_size(150)
        # print(f"[DEBUG] Minimum window size: {min_width}x{min_height}")
        self.setMinimumSize(min_width, min_height)
        # 确保窗口不会被设置一个固定的大小
        self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX = 16777215
        
        # 添加调试信息，显示实际设置的窗口尺寸
        # print(f"[DEBUG] Setting main window size: {width}x{height}")

        # 应用全局字体
        global_font = FontUtils.get_scaled_font(9)  # 使用更小的基础字体大小
        self.setFont(global_font)

        # 创建中央部件
        central_widget = QWidget()
        layout = QVBoxLayout()

        # 欢迎标签
        welcome_label = QLabel("欢迎使用 TestFlow Manager")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-weight: bold; margin: 20px;")
        welcome_label.setFont(FontUtils.get_scaled_font(12))  # 使用更小的字体大小

        layout.addWidget(welcome_label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 显示实际窗口尺寸
        # actual_size = self.size()
        # print(f"[DEBUG] Main window actual size: {actual_size.width()}x{actual_size.height()}")

    def _setup_menu(self) -> None:
        """设置菜单栏"""
        # 应用全局字体
        global_font = FontUtils.get_scaled_font(8)  # 使用更小的基础字体大小

        # 创建菜单栏
        menubar = self.menuBar()
        menubar.setFont(global_font)

        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.setFont(global_font)

        new_action = QAction("新建项目", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_file)
        new_action.setFont(global_font)
        file_menu.addAction(new_action)

        # 添加打开项目菜单项
        open_project_action = QAction("打开项目", self)
        open_project_action.setShortcut("Ctrl+Shift+O")
        open_project_action.triggered.connect(self._on_open_project)
        open_project_action.setFont(global_font)
        file_menu.addAction(open_project_action)

        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)
        open_action.setFont(global_font)
        file_menu.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_file)
        save_action.setFont(global_font)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # 添加查看LTR菜单项
        view_ltr_action = QAction("查看LTR", self)
        view_ltr_action.triggered.connect(self._on_view_ltr)
        view_ltr_action.setFont(global_font)
        file_menu.addAction(view_ltr_action)

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self._on_exit)
        exit_action.setFont(global_font)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        edit_menu.setFont(global_font)

        # 视图菜单
        view_menu = menubar.addMenu("视图")
        view_menu.setFont(global_font)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        tools_menu.setFont(global_font)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.setFont(global_font)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        about_action.setFont(global_font)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """设置工具栏"""
        toolbar = self.addToolBar("主工具栏")

        # 获取缩放字体
        button_font = FontUtils.get_scaled_font(8)  # 使用更小的基础字体大小

        new_button = QPushButton("新建项目")
        new_button.clicked.connect(self._on_new_file)
        new_button.setFont(button_font)
        toolbar.addWidget(new_button)

        # 添加打开项目按钮
        open_project_button = QPushButton("打开项目")
        open_project_button.clicked.connect(self._on_open_project)
        open_project_button.setFont(button_font)
        toolbar.addWidget(open_project_button)

        open_button = QPushButton("打开")
        open_button.clicked.connect(self._on_open_file)
        open_button.setFont(button_font)
        toolbar.addWidget(open_button)

        save_button = QPushButton("保存")
        save_button.clicked.connect(self._on_save_file)
        save_button.setFont(button_font)
        toolbar.addWidget(save_button)

        view_ltr_button = QPushButton("查看LTR")
        view_ltr_button.clicked.connect(self._on_view_ltr)
        view_ltr_button.setFont(button_font)
        toolbar.addWidget(view_ltr_button)

    def _setup_status_bar(self) -> None:
        """设置状态栏"""
        self.status_bar = QStatusBar()
        status_font = FontUtils.get_scaled_font(8)  # 使用更小的基础字体大小
        self.status_bar.setFont(status_font)
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setFont(status_font)
        self.status_bar.addWidget(self.status_label)

    def _on_view_ltr(self) -> None:
        """处理查看LTR事件"""
        logger.debug("View LTR action triggered")
        if self.controller.handle_view_ltr():
            self._update_status()

    def _on_new_file(self) -> None:
        """处理新建文件事件"""
        logger.debug("New file action triggered")
        if self.controller.handle_new_file():
            self._update_status()

    def _on_open_file(self) -> None:
        """处理打开文件事件"""
        logger.debug("Open file action triggered")
        # TODO: 实现文件选择对话框
        # 这里只是一个示例，实际应该打开文件选择对话框
        file_path = "example.txt"  # 示例文件路径
        if self.controller.handle_open_file(file_path):
            self._update_status()

    def _on_open_project(self) -> None:
        """处理打开项目事件"""
        logger.debug("Open project action triggered")
        if self.controller.handle_open_project():
            self._update_status()

    def _on_save_file(self) -> None:
        """处理保存文件事件"""
        logger.debug("Save file action triggered")
        # TODO: 实现文件保存逻辑
        # 这里只是一个示例，实际应该获取当前文件路径
        file_path = "example.txt"  # 示例文件路径
        if self.controller.handle_save_file(file_path):
            self._update_status()

    def _on_exit(self) -> None:
        """处理退出事件"""
        logger.debug("Exit action triggered")
        self.close()

    def _on_about(self) -> None:
        """处理关于事件"""
        logger.debug("About action triggered")
        # 将处理交给Controller
        self.controller.handle_about()

    def _update_status(self) -> None:
        """更新状态栏"""
        status = self.controller.get_status()
        self.status_label.setText(status)

    def closeEvent(self, event) -> None:
        """
        处理窗口关闭事件

        Args:
            event: 关闭事件
        """
        logger.info("MainWindow closing")
        self.controller.shutdown()
        event.accept()