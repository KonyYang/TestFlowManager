"""
路由配置 - 集中管理主窗口的所有页面路由信息

注意：此模块目前处于预留状态。
当前主窗口导航采用内联实现（main_window_ui.py 的 _setup_navigation_pages）。

使用方式（未来扩展）：
    from src.shell.navigation import MAIN_WINDOW_ROUTES, RouteConfig
    
    # 在 main_window_ui.py 中
    def _setup_navigation_pages(self):
        for route in MAIN_WINDOW_ROUTES:
            page = self._create_page(route.page_id)
            self._register_nav_page(
                nav_title=route.title,
                breadcrumb_text=route.breadcrumb,
                page=page,
                subtitle=route.subtitle,
                page_id=route.page_id,
            )

当前状态：✅ 配置已定义，待集成到主窗口
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RouteConfig:
    """路由配置"""
    page_id: str
    title: str
    breadcrumb: str
    subtitle: str = ""
    icon: Optional[str] = None
    enabled: bool = True


# 主窗口路由配置
MAIN_WINDOW_ROUTES = [
    RouteConfig(
        page_id="matrix.main",
        title="Matrix",
        breadcrumb="首页 / Matrix",
        subtitle="测试矩阵编辑",
    ),
    RouteConfig(
        page_id="ltr.application",
        title="LTR 申请",
        breadcrumb="LTR / 申请处理",
        subtitle="LTR 申请单处理",
    ),
    RouteConfig(
        page_id="report.wizard",
        title="创建报告",
        breadcrumb="报告 / 创建",
        subtitle="报告生成向导",
    ),
    RouteConfig(
        page_id="report.updater",
        title="更新报告",
        breadcrumb="报告 / 更新",
        subtitle="报告更新管理",
    ),
    RouteConfig(
        page_id="report.customer",
        title="客户版报告",
        breadcrumb="报告 / 客户版",
        subtitle="客户版报告转换",
    ),
]
