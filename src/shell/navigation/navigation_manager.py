"""
导航管理器 - Shell 级通用导航基础设施

职责：
- 管理侧栏导航列表和页面堆叠的绑定关系
- 处理导航选择和动作执行
- 提供统一的导航变化回调

适用范围：
- MainWindow（主窗口）
- SettingsWindow（设置窗口，未来）
- 任何需要侧栏导航的窗口

注意：这是纯 UI 管理器，不包含业务逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QStackedWidget, QWidget
from PyQt5.QtCore import Qt

from src.core.logger import logger


@dataclass(frozen=True)
class NavigationEntry:
    """
    导航条目数据类
    
    Attributes:
        title: 侧栏显示标题
        breadcrumb: 面包屑文本
        page: 页面对象
        subtitle: 副标题描述
        action: 点击时执行的可选动作
        page_id: 页面唯一标识符
        group: 所属分组名称（可选，用于侧栏视觉分组）
    """
    title: str
    breadcrumb: str
    page: QWidget
    subtitle: str = ""
    action: Optional[Callable[[], None]] = None
    page_id: str = ""
    group: Optional[str] = None


class NavigationManager:
    """
    导航管理器 - 通用的侧栏导航管理器
    
    负责将导航条目与页面注册到 UI，并触发动作/标题刷新。
    通过信号槽自动处理导航列表的行变化和点击事件。
    支持按 group 字段自动插入不可选中的分组标题项。
    
    使用示例：
        from src.shell.navigation import NavigationManager, NavigationEntry
        
        nav_manager = NavigationManager(
            nav_list=self._nav_list,
            page_stack=self._page_stack,
            entry_callback=self._on_navigation_changed,
        )
        
        nav_manager.register_entry(NavigationEntry(
            title="📊 Matrix",
            breadcrumb="首页 / Matrix",
            subtitle="测试矩阵编辑",
            page=matrix_page,
            page_id="matrix.main",
            group="项目管理",
        ))
    """

    def __init__(
        self,
        nav_list: QListWidget,
        page_stack: QStackedWidget,
        entry_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        """
        初始化导航管理器
        
        Args:
            nav_list: 导航列表控件（QListWidget）
            page_stack: 页面堆叠控件（QStackedWidget）
            entry_callback: 导航变化回调函数 (title, breadcrumb, subtitle)
        """
        self._nav_list = nav_list
        self._page_stack = page_stack
        self._entry_callback = entry_callback
        
        # 内部状态
        self._entries: List[NavigationEntry] = []
        self._actions: Dict[int, Callable[[], None]] = {}
        self._list_to_entry: List[int] = []  # 列表项索引 -> entry 索引（-1 表示分组标题）
        self._current_group: Optional[str] = None
        self._initializing = False
        self._skip_signal = False

        # 连接信号槽
        self._nav_list.currentRowChanged.connect(self._on_row_changed)
        self._nav_list.itemClicked.connect(self._on_item_clicked)

    def register_entry(self, entry: NavigationEntry) -> None:
        """
        注册一个导航条目和对应页面
        
        Args:
            entry: 导航条目数据对象
        """
        if self._nav_list is None or self._page_stack is None:
            logger.warning(f"导航控件为 None，跳过注册: {entry.title}")
            return

        # 当分组变化时，插入不可选中的分组标题项
        if entry.group and entry.group != self._current_group:
            header_item = QListWidgetItem(entry.group)
            header_item.setFlags(Qt.NoItemFlags)
            header_font = header_item.font()
            header_font.setBold(True)
            header_font.setPointSize(13)
            header_item.setFont(header_font)
            header_item.setForeground(QColor("#90caf9"))
            self._nav_list.addItem(header_item)
            self._list_to_entry.append(-1)
            self._current_group = entry.group

        entry_index = len(self._entries)
        self._entries.append(entry)
        list_index = self._nav_list.count()
        self._list_to_entry.append(entry_index)
        
        # 添加到导航列表
        item = QListWidgetItem(entry.title)
        self._nav_list.addItem(item)
        
        # 添加到页面堆叠
        self._page_stack.addWidget(entry.page)

        # 注册动作映射（按 entry_index）
        if entry.action:
            self._actions[entry_index] = entry.action

        # 自动选中第一个有效条目（跳过分组标题）
        valid_count = sum(1 for idx in self._list_to_entry if idx >= 0)
        if valid_count == 1:
            self._initializing = True
            try:
                for i, idx in enumerate(self._list_to_entry):
                    if idx >= 0:
                        self._nav_list.setCurrentRow(i)
                        break
            finally:
                self._initializing = False

    def _on_row_changed(self, row: int) -> None:
        """处理选中行变化（由信号槽触发）"""
        if row < 0 or row >= len(self._list_to_entry):
            return
        entry_index = self._list_to_entry[row]
        if entry_index < 0:
            # 选中分组标题时，自动跳转到下一个有效条目
            if not self._skip_signal:
                next_row = self._find_next_valid_row(row)
                if next_row >= 0:
                    self._skip_signal = True
                    self._nav_list.setCurrentRow(next_row)
                    self._skip_signal = False
            return
        self._apply_entry(entry_index)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """处理点击事件，统一执行动作（由信号槽触发）"""
        if self._initializing:
            return
        
        row = self._nav_list.row(item)
        if row < 0 or row >= len(self._list_to_entry):
            return
        
        entry_index = self._list_to_entry[row]
        if entry_index < 0:
            return  # 点击分组标题不执行动作
        
        action = self._actions.get(entry_index)
        if not action:
            return
        
        try:
            action()
        except Exception as exc:
            logger.error(f"导航动作执行失败: {exc}", exc_info=True)

    def _apply_entry(self, entry_index: int) -> None:
        """应用导航条目（切换页面并触发回调）"""
        if entry_index >= len(self._entries):
            return
        
        entry = self._entries[entry_index]
        
        # 切换页面
        self._page_stack.setCurrentIndex(entry_index)
        
        # 触发回调（更新标题、面包屑等）
        if self._entry_callback:
            self._entry_callback(entry.title, entry.breadcrumb, entry.subtitle)

    def _find_next_valid_row(self, from_row: int) -> int:
        """从指定行开始查找下一个有效的（非标题）列表项索引"""
        for i in range(from_row + 1, len(self._list_to_entry)):
            if self._list_to_entry[i] >= 0:
                return i
        # 向后没有，则向前查找
        for i in range(from_row - 1, -1, -1):
            if self._list_to_entry[i] >= 0:
                return i
        return -1

    def select_entry(self, entry_index: int) -> None:
        """
        显式设置当前页面（按 entry 索引）
        
        Args:
            entry_index: 导航条目索引
        """
        if 0 <= entry_index < len(self._entries):
            for list_idx, idx in enumerate(self._list_to_entry):
                if idx == entry_index:
                    self._nav_list.setCurrentRow(list_idx)
                    break

    def get_entry_count(self) -> int:
        """获取已注册条目数量"""
        return len(self._entries)

    def get_current_entry(self) -> Optional[NavigationEntry]:
        """
        获取当前选中的导航条目
        
        Returns:
            当前导航条目，如果没有选中则返回 None
        """
        current_row = self._nav_list.currentRow()
        if 0 <= current_row < len(self._list_to_entry):
            entry_index = self._list_to_entry[current_row]
            if entry_index >= 0:
                return self._entries[entry_index]
        return None
