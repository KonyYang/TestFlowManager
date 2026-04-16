"""
Shell Navigation 模块 - 通用导航基础设施

当前状态：
- ✅ NavigationManager: 正在使用（主窗口导航管理）
- ✅ NavigationRegistry: 正在使用（导航条目集中注册）
- ✅ ShortcutRegistry: 正在使用（全局快捷键集中注册）
- ⏸️ RouteConfig: 预留（未来配置化导航）
- ⏸️ PageRouter: 预留（未来高级路由功能）

注意：此模块提供 Shell 级的导航基础设施。
当前主窗口已集成 NavigationManager、NavigationRegistry 和 ShortcutRegistry，简化了导航和快捷键管理逻辑。

未来扩展方向：
- 当需要配置化导航时，可以使用 MAIN_WINDOW_ROUTES 替代硬编码
- 当需要支持多窗口导航同步时，可以启用 PageRouter 的路由引擎功能
- 当需要插件化架构时，可以基于此模块构建完整的导航服务
"""

from src.shell.navigation.navigation_manager import NavigationManager, NavigationEntry
from src.shell.navigation.navigation_registry import NavigationRegistry
from src.shell.navigation.shortcut_registry import ShortcutRegistry
from src.shell.navigation.page_router import PageRouter
from src.shell.navigation.route_config import RouteConfig, MAIN_WINDOW_ROUTES

__all__ = [
    "NavigationManager",    # ✅ 主要使用的类
    "NavigationEntry",      # ✅ 数据类
    "NavigationRegistry",   # ✅ 导航注册表
    "ShortcutRegistry",     # ✅ 快捷键注册表
    "PageRouter",           # ⏸️ 预留
    "RouteConfig",          # ⏸️ 预留
    "MAIN_WINDOW_ROUTES",   # ⏸️ 预留
]
