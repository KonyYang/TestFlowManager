"""导航控制器：管理侧栏条目、堆叠页面与动作映射"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QStackedWidget, QWidget

from src.core.logger import logger


@dataclass(frozen=True)
class NavigationEntry:
    title: str
    breadcrumb: str
    page: QWidget
    subtitle: str = ""
    action: Optional[Callable[[], None]] = None


class NavigationController:
    """负责将导航条目与页面注册到 UI，并触发动作/标题刷新"""

    def __init__(
        self,
        nav_list: QListWidget,
        page_stack: QStackedWidget,
        entry_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        self._nav_list = nav_list
        self._page_stack = page_stack
        self._entry_callback = entry_callback
        self._entries: List[NavigationEntry] = []
        self._actions: Dict[int, Callable[[], None]] = {}
        self._initializing = False

        self._nav_list.currentRowChanged.connect(self._on_row_changed)
        self._nav_list.itemClicked.connect(self._on_item_clicked)

    def register_entry(self, entry: NavigationEntry) -> None:
        """注册一个导航条目和对应页面"""
        if not self._nav_list or not self._page_stack:
            return

        index = len(self._entries)
        self._entries.append(entry)
        item = QListWidgetItem(entry.title)
        self._nav_list.addItem(item)
        self._page_stack.addWidget(entry.page)

        if entry.action:
            self._actions[index] = entry.action

        if self._nav_list.count() == 1:
            self._initializing = True
            try:
                self._nav_list.setCurrentRow(0)
            finally:
                self._initializing = False

    def _on_row_changed(self, row: int) -> None:
        """处理选中页卡的变化"""
        if row < 0 or row >= len(self._entries):
            return
        self._apply_entry(row)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """处理点击事件，统一执行动作"""
        if self._initializing:
            return
        row = self._nav_list.row(item)
        if row < 0:
            return
        action = self._actions.get(row)
        if not action:
            return
        try:
            action()
        except Exception as exc:
            logger.error("导航动作执行失败", exc_info=exc)

    def _apply_entry(self, index: int) -> None:
        entry = self._entries[index]
        self._page_stack.setCurrentIndex(index)
        if self._entry_callback:
            self._entry_callback(entry.title, entry.breadcrumb, entry.subtitle)

    def select_entry(self, index: int) -> None:
        """显式设置当前页面"""
        if index < 0 or index >= self._nav_list.count():
            return
        self._nav_list.setCurrentRow(index)
