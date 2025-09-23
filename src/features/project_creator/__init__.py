"""
Project Creator模块
负责处理项目创建流程，包括邮件提取、文档解析等核心功能
"""

from .controller.project_creator_controller import ProjectCreatorController
from .service.project_creator_service import ProjectCreatorService
from .model.project_creator_data import (
    EmailAttachment,
    EmailData,
    ProjectData,
    WordProcessingResult,
    ProjectCreationContext
)

__all__ = [
    'ProjectCreatorController',
    'ProjectCreatorService',
    'EmailAttachment',
    'EmailData',
    'ProjectData',
    'WordProcessingResult',
    'ProjectCreationContext'
]
