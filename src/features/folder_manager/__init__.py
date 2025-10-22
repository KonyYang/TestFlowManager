# src/features/folder_manager/__init__.py
"""
项目文件夹管理模块
负责项目文件夹的创建、管理和维护
"""

from .controller.folder_manager_controller import FolderManagerController
from .service.folder_manager_service import FolderManagerService

__all__ = ['FolderManagerController', 'FolderManagerService']