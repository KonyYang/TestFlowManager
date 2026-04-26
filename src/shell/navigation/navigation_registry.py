# src/shell/navigation/navigation_registry.py
"""
导航注册表模块
集中管理所有导航条目配置，实现导航配置与 UI 层的解耦
"""
from typing import Callable, Optional
from PyQt5.QtWidgets import QWidget

from .navigation_manager import NavigationManager, NavigationEntry


class NavigationRegistry:
    """
    导航注册表 - 集中管理所有导航条目配置
    
    职责：
    - 统一管理所有导航条目的注册逻辑
    - 隔离导航配置与主窗口实现细节
    - 提供可扩展的导航条目注册接口
    """

    @staticmethod
    def register_all_entries(
        nav_controller: NavigationManager,
        matrix_tab: Optional[QWidget],
        file_handlers,
        export_handlers,
        report_handlers,
        tool_handlers,
        placeholder_factory: Callable[[str, str], QWidget],
    ) -> None:
        """
        注册所有导航条目
        
        Args:
            nav_controller: 导航管理器实例
            matrix_tab: Matrix 编辑器页面（可选）
            file_handlers: 文件操作处理器
            export_handlers: 导出操作处理器
            report_handlers: 报告操作处理器
            tool_handlers: 工具操作处理器
            placeholder_factory: 占位页面工厂函数
        """
        # === Matrix 编辑器（默认首页）===
        if matrix_tab is not None:
            nav_controller.register_entry(NavigationEntry(
                title="📊 Matrix 编辑器",
                breadcrumb="项目管理 / Matrix 编辑器",
                subtitle="编辑和管理测试流程矩阵",
                page=matrix_tab,
                page_id="matrix.main",
                group="项目管理",
            ))
        
        # === 项目管理组 ===
        nav_controller.register_entry(NavigationEntry(
            title="📁 新建项目",
            breadcrumb="项目管理 / 新建项目",
            subtitle="创建一个新的测试流程项目",
            page=placeholder_factory("新建项目", "创建一个新的测试流程项目"),
            action=file_handlers.on_new_file,
            page_id="project.new",
            group="项目管理",
        ))
        nav_controller.register_entry(NavigationEntry(
            title="📂 打开项目",
            breadcrumb="项目管理 / 打开项目",
            subtitle="从本地文件夹加载现有项目",
            page=placeholder_factory("打开项目", "从本地文件夹加载现有项目"),
            action=file_handlers.on_open_project,
            page_id="project.open",
            group="项目管理",
        ))
        nav_controller.register_entry(NavigationEntry(
            title="📋 查看LTR",
            breadcrumb="项目管理 / 查看LTR",
            subtitle="浏览本地测试报告",
            page=placeholder_factory("查看LTR", "浏览本地测试报告"),
            action=file_handlers.on_view_ltr,
            page_id="ltr.view",
            group="项目管理",
        ))

        # === 报告管理组 ===
        nav_controller.register_entry(NavigationEntry(
            title="✨ 创建报告",
            breadcrumb="报告管理 / 创建报告",
            subtitle="使用向导生成新的测试报告",
            page=placeholder_factory("创建报告", "使用向导生成新的测试报告"),
            action=report_handlers.on_create_report,
            page_id="report.create",
            group="报告管理",
        ))
        nav_controller.register_entry(NavigationEntry(
            title="🔄 更新报告",
            breadcrumb="报告管理 / 更新报告",
            subtitle="基于最新Matrix更新现有报告",
            page=placeholder_factory("更新报告", "基于最新Matrix更新现有报告"),
            action=report_handlers.on_update_report,
            page_id="report.update",
            group="报告管理",
        ))
        nav_controller.register_entry(NavigationEntry(
            title="👥 转客户版",
            breadcrumb="报告管理 / 转客户版",
            subtitle="生成去除敏感信息的客户版本",
            page=placeholder_factory("转客户版", "生成去除敏感信息的客户版本"),
            action=report_handlers.on_convert_customer_version,
            page_id="report.customer",
            group="报告管理",
        ))

        # === 测试表格组 ===
        nav_controller.register_entry(NavigationEntry(
            title="📤 导出窗口矩阵",
            breadcrumb="测试表格 / 导出窗口矩阵",
            subtitle="将Matrix导出为Excel文件",
            page=placeholder_factory("导出窗口矩阵", "将Matrix导出为Excel文件"),
            action=export_handlers.on_export_matrix,
            page_id="export.matrix",
            group="测试表格",
        ))
        nav_controller.register_entry(NavigationEntry(
            title="📊 LLCR记录表",
            breadcrumb="测试表格 / LLCR记录表",
            subtitle="导出LLCR格式记录表",
            page=placeholder_factory("LLCR记录表", "导出LLCR格式记录表"),
            action=export_handlers.on_export_llcr,
            page_id="export.llcr",
            group="测试表格",
        ))
        nav_controller.register_entry(NavigationEntry(
            title="📄 CR记录表",
            breadcrumb="测试表格 / CR记录表",
            subtitle="导出CR格式记录表",
            page=placeholder_factory("CR记录表", "导出CR格式记录表"),
            action=export_handlers.on_export_cr,
            page_id="export.cr",
            group="测试表格",
        ))

        # === 工具箱组 ===
        nav_controller.register_entry(NavigationEntry(
            title="📝 正文编辑器",
            breadcrumb="工具箱 / 正文编辑器",
            subtitle="编辑Word文档正文内容",
            page=placeholder_factory("正文编辑器", "编辑Word文档正文内容"),
            action=tool_handlers.on_edit_body_content,
            page_id="tool.body_editor",
            group="工具箱",
        ))
        nav_controller.register_entry(NavigationEntry(
            title="🔐 文件加密",
            breadcrumb="工具箱 / 文件加密",
            subtitle="对测试文件进行加密保护",
            page=placeholder_factory("文件加密", "对测试文件进行加密保护"),
            action=tool_handlers.on_encrypt_test_files,
            page_id="tool.encrypt",
            group="工具箱",
        ))

        # === 其他 ===
        nav_controller.register_entry(NavigationEntry(
            title="ℹ️ 关于",
            breadcrumb="关于 TestFlow Manager",
            subtitle="了解TestFlow Manager的更多信息",
            page=placeholder_factory("关于", "了解TestFlow Manager的更多信息"),
            action=file_handlers.on_about,
            page_id="about",
        ))
