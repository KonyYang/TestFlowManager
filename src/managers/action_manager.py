"""
动作管理器模块
负责管理应用程序中的各种动作（命令）
"""

from typing import Dict, Callable, List, Optional
from PyQt5.QtWidgets import QAction
from src.core.logger import logger


class ActionManager:
    """
    动作管理器类
    管理应用程序中的各种动作（命令），支持动作的注册、查找和执行
    """

    def __init__(self):
        self._actions: Dict[str, QAction] = {}
        self._action_groups: Dict[str, List[str]] = {}

    def register_action(self, name: str, action: QAction) -> None:
        """
        注册动作

        Args:
            name: 动作名称
            action: QAction实例
        """
        self._actions[name] = action
        logger.debug(f"Action '{name}' registered")

    def unregister_action(self, name: str) -> None:
        """
        注销动作

        Args:
            name: 动作名称
        """
        if name in self._actions:
            del self._actions[name]
            logger.debug(f"Action '{name}' unregistered")

            # 从所有动作组中移除
            for group_name, actions in self._action_groups.items():
                if name in actions:
                    actions.remove(name)

    def get_action(self, name: str) -> Optional[QAction]:
        """
        获取动作实例

        Args:
            name: 动作名称

        Returns:
            QAction实例或None
        """
        return self._actions.get(name)

    def create_action_group(self, group_name: str) -> None:
        """
        创建动作组

        Args:
            group_name: 动作组名称
        """
        if group_name not in self._action_groups:
            self._action_groups[group_name] = []
            logger.debug(f"Action group '{group_name}' created")

    def add_action_to_group(self, action_name: str, group_name: str) -> None:
        """
        将动作添加到动作组

        Args:
            action_name: 动作名称
            group_name: 动作组名称
        """
        if group_name not in self._action_groups:
            self.create_action_group(group_name)

        if action_name in self._actions:
            if action_name not in self._action_groups[group_name]:
                self._action_groups[group_name].append(action_name)
                logger.debug(f"Action '{action_name}' added to group '{group_name}'")
        else:
            logger.warning(f"Action '{action_name}' not found when adding to group '{group_name}'")

    def get_actions_in_group(self, group_name: str) -> List[QAction]:
        """
        获取动作组中的所有动作

        Args:
            group_name: 动作组名称

        Returns:
            QAction实例列表
        """
        actions = []
        if group_name in self._action_groups:
            for action_name in self._action_groups[group_name]:
                action = self.get_action(action_name)
                if action:
                    actions.append(action)
        return actions

    def execute_action(self, name: str) -> bool:
        """
        执行动作

        Args:
            name: 动作名称

        Returns:
            动作是否成功执行
        """
        action = self.get_action(name)
        if action and action.isEnabled():
            try:
                action.trigger()
                logger.debug(f"Action '{name}' executed")
                return True
            except Exception as e:
                logger.error(f"Error executing action '{name}': {e}")
                return False
        else:
            logger.warning(f"Action '{name}' not found or not enabled")
            return False


# 全局动作管理器实例
action_manager = ActionManager()
