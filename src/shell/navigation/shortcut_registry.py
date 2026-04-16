# src/shell/navigation/shortcut_registry.py
"""
快捷键注册表模块
集中管理所有全局快捷键配置，实现快捷键配置与 UI 层的解耦
"""
import os
from typing import Optional

from PyQt5.QtWidgets import QAction, QMainWindow
from PyQt5.QtGui import QFont

from src.core.font_utils import FontUtils


class ShortcutRegistry:
    """
    快捷键注册表 - 集中管理所有全局快捷键
    
    职责：
    - 统一管理所有全局快捷键的注册逻辑
    - 隔离快捷键配置与主窗口实现细节
    - 支持条件性注册（如 Pilot 功能）
    - 提供可扩展的快捷键注册接口
    """

    @staticmethod
    def register_all_shortcuts(
        window: QMainWindow,
        file_handlers,
        export_handlers,
        report_handlers,
        tool_handlers,
        workspace_facade,
        env: Optional[dict] = None,
    ) -> None:
        """
        注册所有全局快捷键
        
        Args:
            window: 主窗口实例
            file_handlers: 文件操作处理器
            export_handlers: 导出操作处理器
            report_handlers: 报告操作处理器
            tool_handlers: 工具操作处理器
            workspace_facade: Matrix Workspace Facade（用于检查 Pilot 功能）
            env: 环境变量字典（可选，默认为 os.environ）
        """
        if env is None:
            env = os.environ
        
        menu_font = FontUtils.get_scaled_font(8)
        
        # === 文件操作快捷键 ===
        new_action = QAction("新建项目", window)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(file_handlers.on_new_file)
        new_action.setFont(menu_font)
        window.addAction(new_action)

        open_project_action = QAction("打开项目", window)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(file_handlers.on_open_project)
        open_project_action.setFont(menu_font)
        window.addAction(open_project_action)

        export_matrix_action = QAction("导出窗口矩阵", window)
        export_matrix_action.setShortcut("Ctrl+S")
        export_matrix_action.triggered.connect(export_handlers.on_export_matrix)
        export_matrix_action.setFont(menu_font)
        window.addAction(export_matrix_action)

        view_ltr_action = QAction("查看LTR", window)
        view_ltr_action.setShortcut("Ctrl+F")
        view_ltr_action.triggered.connect(file_handlers.on_view_ltr)
        view_ltr_action.setFont(menu_font)
        window.addAction(view_ltr_action)

        exit_action = QAction("退出", window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(file_handlers.on_exit)
        exit_action.setFont(menu_font)
        window.addAction(exit_action)

        # === 测试表格快捷键 ===
        llcr_action = QAction("LLCR", window)
        llcr_action.triggered.connect(export_handlers.on_export_llcr)
        llcr_action.setFont(menu_font)
        window.addAction(llcr_action)

        cr_action = QAction("CR", window)
        cr_action.triggered.connect(export_handlers.on_export_cr)
        cr_action.setFont(menu_font)
        window.addAction(cr_action)

        # === 报告操作快捷键 ===
        create_report_action = QAction("创建报告", window)
        create_report_action.triggered.connect(report_handlers.on_create_report)
        create_report_action.setFont(menu_font)
        window.addAction(create_report_action)

        update_report_action = QAction("更新报告", window)
        update_report_action.triggered.connect(report_handlers.on_update_report)
        update_report_action.setFont(menu_font)
        window.addAction(update_report_action)

        convert_customer_version_action = QAction("转客户版", window)
        convert_customer_version_action.triggered.connect(report_handlers.on_convert_customer_version)
        convert_customer_version_action.setFont(menu_font)
        window.addAction(convert_customer_version_action)

        # === 工具箱快捷键 ===
        body_content_action = QAction("正文内容编辑", window)
        body_content_action.triggered.connect(tool_handlers.on_edit_body_content)
        body_content_action.setFont(menu_font)
        window.addAction(body_content_action)

        encrypt_files_action = QAction("测试文件加密", window)
        encrypt_files_action.triggered.connect(tool_handlers.on_encrypt_test_files)
        encrypt_files_action.setFont(menu_font)
        window.addAction(encrypt_files_action)

        # === 帮助快捷键 ===
        about_action = QAction("关于", window)
        about_action.triggered.connect(file_handlers.on_about)
        about_action.setFont(menu_font)
        window.addAction(about_action)

        # === Pilot 功能（条件注册）===
        if workspace_facade.is_preview_pilot_enabled(env):
            preview_pilot_action = QAction("[PILOT] 打开隔离 Matrix 预览", window)
            preview_pilot_action.setShortcut("Ctrl+Alt+Shift+P")
            preview_pilot_action.triggered.connect(tool_handlers.on_open_isolated_matrix_preview)
            preview_pilot_action.setFont(menu_font)
            window.addAction(preview_pilot_action)
            
            close_preview_pilot_action = QAction("[PILOT] 关闭隔离 Matrix 预览", window)
            close_preview_pilot_action.setShortcut("Ctrl+Alt+Shift+L")
            close_preview_pilot_action.triggered.connect(tool_handlers.on_close_isolated_matrix_preview)
            close_preview_pilot_action.setFont(menu_font)
            window.addAction(close_preview_pilot_action)
