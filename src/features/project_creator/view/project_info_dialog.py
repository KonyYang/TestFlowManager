"""
项目信息对话框模块
提供一个对话框用于显示和编辑项目基本信息
"""

import logging
import json
import os
from PyQt5.QtWidgets import QDialog

from src.features.ltr_manager.view.ltr_form_dialog_base import LTRFormDialogBase

logger = logging.getLogger(__name__)


class ProjectInfoDialog(LTRFormDialogBase):
    """
    ProjectInfoDialog
    项目信息对话框类
    用于显示和编辑项目基本信息
    """

    def __init__(self, project_data, parent=None, project_data_file_path=None):
        """
        初始化项目信息对话框

        Args:
            project_data: 包含项目数据的字典
            parent: 父窗口
        """
        logger.info(f"创建项目信息对话框，初始数据: {project_data}")
        super().__init__("项目基本信息", project_data, parent)

        self.project_data_file_path = project_data_file_path
        if not self.project_data_file_path and parent and hasattr(parent, "resolve_project_data_file_path"):
            self.project_data_file_path = parent.resolve_project_data_file_path()

    def accept(self):
        """重写accept方法，保存修改后的数据到JSON文件"""
        try:
            logger.info("用户确认了项目信息对话框，准备保存数据")

            modified_data = self._collect_form_data()
            logger.debug(f"收集到的修改后数据: {modified_data}")

            if self.project_data_file_path and os.path.exists(os.path.dirname(self.project_data_file_path)):
                logger.debug(f"正在保存数据到文件: {self.project_data_file_path}")

                try:
                    with open(self.project_data_file_path, 'r', encoding='utf-8') as f:
                        original_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    logger.warning(f"读取原始数据文件时出错: {e}")
                    original_data = {}

                original_data.update(modified_data)

                with open(self.project_data_file_path, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, ensure_ascii=False, indent=4)

                logger.info(f"成功保存数据到文件: {self.project_data_file_path}")
            else:
                logger.warning("未找到有效的项目数据文件路径，无法保存修改后的数据")

        except Exception as e:
            logger.error(f"保存项目信息时出错: {e}")

        super().accept()
