"""
Page Router - 路由引擎

注意：此模块目前处于预留状态。
当前主窗口导航采用内联实现，未使用 PageRouter 的路由功能。

保留原因：
- 提供页面注册和跳转的基础能力
- 支持未来的配置化导航系统
- 可用于多窗口导航同步场景

当前状态：✅ 核心功能保留，未使用的 go_back() 等方法已标记为待优化
"""
from typing import Callable, Dict, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal

from src.core.logger import logger


class PageRouter(QObject):
    """页面路由管理器"""
    
    page_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._page_factories: Dict[str, Callable] = {}
        self._current_page_id: Optional[str] = None
        self._history: list = []
    
    def register_page(self, page_id: str, factory: Callable[[], Any]) -> None:
        """注册页面工厂"""
        self._page_factories[page_id] = factory
        logger.debug(f"页面已注册: {page_id}")
    
    def navigate_to(self, page_id: str) -> Optional[Any]:
        """执行页面跳转"""
        if page_id not in self._page_factories:
            logger.warning(f"页面未注册: {page_id}")
            return None
        
        if self._current_page_id:
            self._history.append(self._current_page_id)
        
        factory = self._page_factories[page_id]
        page = factory()
        self._current_page_id = page_id
        self.page_changed.emit(page_id)
        return page
    
    def go_back(self) -> Optional[str]:
        """回退到上一个页面"""
        if not self._history:
            return None
        prev_page_id = self._history.pop()
        self.navigate_to(prev_page_id)
        return prev_page_id
    
    @property
    def current_page_id(self) -> Optional[str]:
        return self._current_page_id
