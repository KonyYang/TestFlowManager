# src/features/main_window/view/main_window_ui.py
"""
主窗口界面模块
定义主窗口的用户界面
"""
import os
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QMenuBar, QToolBar, QStatusBar, QLabel,
    QAction, QVBoxLayout, QWidget, QTabWidget, QMessageBox,
    QFileDialog, QApplication
)
from PyQt5.QtGui import QIcon, QFont, QScreen
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QRect, pyqtSignal
from src.core.logger import logger
from src.core.font_utils import FontUtils
from src.features.main_window.controller.main_window_controller import MainWindowController
from src.features.matrix.view.matrix_dialog import MatrixDialog
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController
from src.features.customer_report_generator.controller.customer_report_controller import CustomerReportController
from src.features.report_wizard.controller.report_wizard_controller import ReportWizardController
from src.features.document_parser.controller.document_parser_controller import DocumentParserController
from src.features.report_updater.controller.report_updater_controller import ReportUpdaterController


class MainWindow(QMainWindow):
    """
    主窗口类
    应用程序的主窗口界面
    """
    
    # 自定义信号，用于通知启动进度
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
        
        # 保存窗口状态信息
        self.is_custom_sized = False
        self.custom_geometry = None
        self.fullscreen_geometry = None
        
        # 分步初始化
        self._initialize_step_by_step()
        
        # 更新界面状态
        self._update_status()

    def _initialize_step_by_step(self):
        """分步初始化主窗口组件"""
        try:
            # 步骤1: 基础UI设置
            self._notify_progress(0, "正在初始化基础界面...")
            self._setup_basic_ui()
            
            # 步骤2: 控制器初始化
            self._notify_progress(1, "正在初始化控制器...")
            self._initialize_controllers()
            
            # 步骤3: 菜单和工具栏
            self._notify_progress(2, "正在设置菜单和工具栏...")
            self._setup_menu()
            self._setup_toolbar()
            self._setup_status_bar()
            
            # 步骤4: 标签页设置
            self._notify_progress(3, "正在设置功能标签页...")
            self._setup_tabs()
            
            # 步骤5: 初始化控制器
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
        """设置基础用户界面"""
        # 设置窗口属性
        self.setWindowTitle("TestFlow Manager")
        
        # 设置窗口图标
        self._set_window_icon()
        
        # 设置窗口为满屏显示
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen_geometry)
        self.fullscreen_geometry = screen_geometry
        
        # 应用全局字体
        global_font = FontUtils.get_scaled_font(9)  # 使用更小的基础字体大小
        self.setFont(global_font)

        # 创建中央部件
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距以最大化利用空间

        # 创建主内容区域 - 使用标签页组织不同功能模块
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(FontUtils.get_scaled_font(8))
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _initialize_controllers(self):
        """初始化控制器"""
        # 初始化主控制器
        self.controller = MainWindowController(self)
        
        # 初始化Matrix控制器
        self.matrix_project_controller = MatrixProjectController(self)
        self.matrix_controller = self.matrix_project_controller.matrix_controller
        
        # 初始化客户报告生成控制器
        self.customer_report_controller = CustomerReportController(self)
        
        # 初始化报告向导控制器
        self.report_wizard_controller = ReportWizardController(self)
        
        # 初始化文档解析控制器
        self.document_parser_controller = DocumentParserController(self)
        
        # 初始化报告更新控制器
        self.report_updater_controller = ReportUpdaterController(self)

    def _setup_tabs(self):
        """设置标签页"""
        # 创建Matrix编辑器标签页
        self.matrix_tab = QWidget()
        self._setup_matrix_tab()
        self.tab_widget.addTab(self.matrix_tab, "Matrix编辑器")
        
        # 可以在这里添加更多标签页...

    def _setup_matrix_tab(self):
        """设置Matrix编辑器标签页"""
        layout = QVBoxLayout(self.matrix_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建Matrix对话框实例（嵌入到主窗口中而不是独立窗口）
        self.matrix_dialog = MatrixDialog(parent=self, service=self.matrix_controller.service)
        layout.addWidget(self.matrix_dialog)
        
    def _set_window_icon(self):
        """设置窗口图标"""
        try:
            # 获取图标文件路径
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "app", "resources", "icons", "app_icon.ico")
            icon_path = os.path.normpath(icon_path)
            
            # 检查图标文件是否存在
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                logger.debug(f"成功设置窗口图标: {icon_path}")
            else:
                logger.warning(f"窗口图标文件不存在: {icon_path}")
        except Exception as e:
            logger.error(f"设置窗口图标时出错: {e}")
        
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)

    def changeEvent(self, event):
        """处理窗口状态变化事件"""
        if event.type() == event.WindowStateChange:
            # 检查窗口状态变化
            if self.isMaximized() and self.is_custom_sized:
                # 如果是从自定义大小恢复到最大化状态，重置标志
                self.is_custom_sized = False
        super().changeEvent(event)

    def resizeEvent(self, event):
        """处理窗口大小变化事件"""
        super().resizeEvent(event)
        
    def showNormal(self):
        """重写showNormal方法，实现自定义窗口大小"""
        if self.isMaximized():
            # 如果当前是最大化状态，切换到自定义大小
            self.is_custom_sized = True
            if not self.custom_geometry:
                # 计算30%大小的窗口几何信息
                screen_geometry = QApplication.primaryScreen().availableGeometry()
                width = int(screen_geometry.width() * 0.3)
                height = int(screen_geometry.height() * 0.3)
                x = (screen_geometry.width() - width) // 2
                y = (screen_geometry.height() - height) // 2
                self.custom_geometry = QRect(x, y, width, height)
            
            # 设置为自定义大小
            super().showNormal()
            self.setGeometry(self.custom_geometry)
        else:
            # 如果已经是普通窗口状态，则恢复正常
            super().showNormal()
            
    def showMaximized(self):
        """重写showMaximized方法"""
        self.is_custom_sized = False
        super().showMaximized()
        
    def showMinimized(self):
        """重写showMinimized方法"""
        self.is_custom_sized = False
        super().showMinimized()

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
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self._on_open_project)
        open_project_action.setFont(global_font)
        file_menu.addAction(open_project_action)

        # 添加导出窗口矩阵菜单项
        export_matrix_action = QAction("导出窗口矩阵", self)
        export_matrix_action.setShortcut("Ctrl+S")  # 将Ctrl+S快捷键分配给导出功能
        export_matrix_action.triggered.connect(self._on_export_matrix)
        export_matrix_action.setFont(global_font)
        file_menu.addAction(export_matrix_action)

        file_menu.addSeparator()

        # 添加查看LTR菜单项
        view_ltr_action = QAction("查看LTR", self)
        view_ltr_action.setShortcut("Ctrl+F")
        view_ltr_action.triggered.connect(self._on_view_ltr)
        view_ltr_action.setFont(global_font)
        file_menu.addAction(view_ltr_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self._on_exit)
        exit_action.setFont(global_font)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        edit_menu.setFont(global_font)

        # 测试表格菜单
        test_table_menu = menubar.addMenu("测试表格")
        test_table_menu.setFont(global_font)

        # 添加LLCR子菜单项
        llcr_action = QAction("LLCR", self)
        llcr_action.triggered.connect(self._on_export_llcr)
        llcr_action.setFont(global_font)
        test_table_menu.addAction(llcr_action)

        # 添加CR子菜单项
        cr_action = QAction("CR", self)
        cr_action.triggered.connect(self._on_export_cr)
        cr_action.setFont(global_font)
        test_table_menu.addAction(cr_action)

        # 报告菜单
        report_menu = menubar.addMenu("报告")
        report_menu.setFont(global_font)

        # 添加创建报告菜单项
        create_report_action = QAction("创建报告", self)
        create_report_action.triggered.connect(self._on_create_report)
        create_report_action.setFont(global_font)
        report_menu.addAction(create_report_action)

        # 添加更新报告菜单项
        update_report_action = QAction("更新报告", self)
        update_report_action.triggered.connect(self._on_update_report)
        update_report_action.setFont(global_font)
        report_menu.addAction(update_report_action)

        # 添加转客户版菜单项
        convert_customer_version_action = QAction("转客户版", self)
        convert_customer_version_action.triggered.connect(self._on_convert_customer_version)
        convert_customer_version_action.setFont(global_font)
        report_menu.addAction(convert_customer_version_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")
        view_menu.setFont(global_font)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        tools_menu.setFont(global_font)
        
        # 添加正文内容编辑菜单项
        body_content_action = QAction("正文内容编辑", self)
        body_content_action.triggered.connect(self._on_edit_body_content)
        body_content_action.setFont(global_font)
        tools_menu.addAction(body_content_action)

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

        # 移除了工具栏上的按钮，按照用户要求全部取消

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

    def _on_open_project(self) -> None:
        """处理打开项目事件"""
        logger.debug("Open project action triggered")
        if self.controller.handle_open_project():
            self._update_status()

    def _on_export_matrix(self) -> None:
        """处理导出窗口矩阵事件"""
        logger.debug("Export matrix action triggered")
        # 调用matrix控制器，处理才能获取到更新后的数据
        if self.matrix_controller.handle_export_matrix_to_excel():
            self._update_status()

    def _on_export_llcr(self) -> None:
        """处理导出LLCR事件"""
        logger.debug("Export LLCR action triggered")
        # 调用matrix控制器处理LLCR导出
        if self.matrix_controller.handle_export_llcr():
            self._update_status()

    def _on_export_cr(self) -> None:
        """处理导出CR事件"""
        logger.debug("Export CR action triggered")
        # 调用matrix控制器处理CR导出
        if self.matrix_controller.handle_export_cr():
            self._update_status()

    def _on_create_report(self) -> None:
        """处理创建报告事件"""
        logger.debug("Create report action triggered")
        # 获取当前项目路径
        current_project_path = getattr(self.controller, '_current_project_path', None)
        # 设置项目路径到报告向导控制器
        self.report_wizard_controller.set_project_path(current_project_path)
        # 设置Matrix服务到报告向导控制器
        self.report_wizard_controller.set_matrix_service(self.matrix_controller.service)
        # 显示报告向导对话框
        self.report_wizard_controller.show_wizard()
        self._update_status()

    def _on_update_report(self) -> None:
        """处理更新报告事件"""
        logger.debug("Update report action triggered")
        
        # 获取当前项目路径
        current_project_path = getattr(self.controller, '_current_project_path', None)
        
        # 设置项目路径到报告更新控制器
        self.report_updater_controller.set_project_path(current_project_path)
        
        # 显示报告更新对话框
        self.report_updater_controller.show_report_updater_dialog()
        
        self._update_status()

    def _on_convert_customer_version(self) -> None:
        """处理转客户版事件"""
        logger.debug("Convert to customer version action triggered")
        # 获取当前项目路径
        current_project_path = getattr(self.controller, '_current_project_path', None)
        # 调用客户报告控制器处理生成客户报告
        if self.customer_report_controller.handle_generate_customer_report(current_project_path):
            self._update_status()
        else:
            self._update_status()

    def _on_edit_body_content(self) -> None:
        """处理正文内容编辑事件"""
        logger.debug("Edit body content action triggered")
        # 调用文档解析控制器显示正文内容编辑器
        # 这里可以先弹出文件选择对话框让用户选择Word文档
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Word文档", "", "Word文档 (*.doc *.docx)"
        )
        if file_path:
            logger.info(f"用户选择了文件: {file_path}")
            self.document_parser_controller.show_body_content_editor(file_path)
        else:
            logger.info("用户取消了文件选择")
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