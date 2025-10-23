"""
项目文件夹管理控制器模块
处理项目文件夹管理的业务逻辑和事件
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget

from src.core.logger import logger
from src.features.folder_manager.service.folder_manager_service import FolderManagerService


class FolderManagerController:
    """
    项目文件夹管理控制器类
    处理项目文件夹管理的业务逻辑和事件
    """

    def __init__(self, parent_view: Optional[QWidget] = None):
        """
        初始化项目文件夹管理控制器

        Args:
            parent_view: 父窗口视图实例
        """
        self.parent_view = parent_view
        self.service = FolderManagerService()

    def create_complete_project_structure(self, project_data: Dict[str, Any]) -> Optional[str]:
        """
        创建完整的项目结构，包括子文件夹、模板文件等

        Args:
            project_data: 项目数据，包含DL编号等信息

        Returns:
            项目子文件夹路径，如果失败则返回None
        """
        logger.info("开始创建完整项目结构")
        result = self.service.create_complete_project_structure(project_data, self.parent_view)

        if result:
            logger.info(f"完整项目结构创建成功: {result}")
        else:
            logger.error("完整项目结构创建失败")

        return result
