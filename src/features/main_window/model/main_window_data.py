"""
主窗口数据模型模块
定义主窗口相关的数据模型
"""

from typing import Dict, List, Optional, Any
from src.core.logger import logger


class MainWindowData:
    """
    主窗口数据模型类
    管理主窗口相关的数据
    """

    def __init__(self):
        self._data: Dict[str, Any] = {
            "title": "TestFlow Manager",
            "status": "就绪",
            "recent_files": [],
            "settings": {}
        }

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        获取数据

        Args:
            key: 数据键名
            default: 默认值

        Returns:
            数据值或默认值
        """
        return self._data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """
        设置数据

        Args:
            key: 数据键名
            value: 数据值
        """
        self._data[key] = value
        logger.debug(f"MainWindowData updated: {key} = {value}")

    def get_all_data(self) -> Dict[str, Any]:
        """
        获取所有数据

        Returns:
            包含所有数据的字典
        """
        return self._data.copy()

    def add_recent_file(self, file_path: str) -> None:
        """
        添加最近打开的文件

        Args:
            file_path: 文件路径
        """
        recent_files = self._data.get("recent_files", [])
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        # 限制最近文件列表长度为10
        self._data["recent_files"] = recent_files[:10]
        logger.debug(f"Recent file added: {file_path}")

    def get_recent_files(self) -> List[str]:
        """
        获取最近打开的文件列表

        Returns:
            文件路径列表
        """
        return self._data.get("recent_files", []).copy()

    def clear_recent_files(self) -> None:
        """清空最近打开的文件列表"""
        self._data["recent_files"] = []
        logger.debug("Recent files cleared")

    def update_status(self, status: str) -> None:
        """
        更新状态信息

        Args:
            status: 状态信息
        """
        self._data["status"] = status
        logger.debug(f"Status updated: {status}")

    def get_status(self) -> str:
        """
        获取状态信息

        Returns:
            当前状态信息
        """
        return self._data.get("status", "未知")
