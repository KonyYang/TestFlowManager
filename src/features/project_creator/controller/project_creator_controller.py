from __future__ import annotations

# src/features/project_creator/controller/project_creator_controller.py
import os

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QDialog, QMessageBox
from src.core.logger import logger
from src.features.project_creator.service.project_creator_service import ProjectCreatorService
from src.features.project_creator.service.project_creation_application_service import (
    ProjectCreationApplicationService,
)
from src.features.project_creator.controller.runtime.project_creator_email_flow_coordinator import (
    ProjectCreatorEmailFlowCoordinator,
)
from src.features.project_creator.controller.runtime.project_creator_ltr_result_coordinator import (
    ProjectCreatorLtrResultCoordinator,
)
from src.features.project_creator.controller.runtime.project_creator_attachment_ltr_flow_coordinator import (
    ProjectCreatorAttachmentLtrFlowCoordinator,
)
from src.features.project_creator.model.project_creator_data import ProjectCreationContext
# 添加LTR项目集成服务
from src.features.project_creator.service.ltr_project_integration_service import LTRProjectIntegrationService
# 添加Matrix会话工厂
from src.features.matrix.service.session.matrix_session_factory import MatrixSessionFactory
# 添加事件调度器
from src.core.event_dispatcher import event_dispatcher, EventTopics
from src.core.project_context import ProjectContext
from src.app.composition.project_session_application_service import project_session_app_service

if TYPE_CHECKING:
    from src.features.matrix.service.session.matrix_session_registry import MatrixSessionRegistry


class ProjectCreatorController:
    """
    项目创建控制器类
    处理项目创建流程，包括邮件提取、文档解析等
    """

    def __init__(
        self,
        parent_view=None,
        matrix_session_registry: "MatrixSessionRegistry" = None,
        matrix_session_mode: str = "shared",
        matrix_session_id: str = None,
    ):
        """
        初始化项目创建控制器

        Args:
            parent_view: 父窗口视图实例
        """
        self.parent_view = parent_view
        self.matrix_session_registry = matrix_session_registry
        self.matrix_session_mode = matrix_session_mode
        self.matrix_session_id = matrix_session_id
        self._matrix_session_scope = None
        if self.matrix_session_mode not in ("shared", "isolated"):
            raise ValueError(f"Unsupported matrix session mode: {self.matrix_session_mode}")
        self.context = ProjectCreationContext()
        self.email_extractor_controller = None  # 添加这一行来保存controller引用
        self.selected_attachment = None  # 用于存储选中的附件
        self.email_flow_coordinator = ProjectCreatorEmailFlowCoordinator(self)
        self.ltr_result_coordinator = ProjectCreatorLtrResultCoordinator(self)
        # 附件处理 + LTR 对话框启动协调器
        self._attachment_ltr_flow_coordinator = ProjectCreatorAttachmentLtrFlowCoordinator(self)
        # 添加LTR项目集成服务
        self.ltr_integration_service = LTRProjectIntegrationService()
        if (
            self.matrix_session_mode == "isolated"
            and self.matrix_session_registry is not None
            and self.matrix_session_id
            and hasattr(self.matrix_session_registry, "open_scope")
        ):
            self._matrix_session_scope = self.matrix_session_registry.open_scope(
                self.matrix_session_id,
                mode=self.matrix_session_mode,
            )
        # 添加Matrix项目控制器
        if self.matrix_session_mode == "isolated":
            matrix_session = MatrixSessionFactory.create(
                parent_view,
                mode="isolated",
                registry=self.matrix_session_registry,
                session_id=self.matrix_session_id,
            )
        else:
            matrix_session = MatrixSessionFactory.create(
                parent_view,
                mode="shared",
                registry=self.matrix_session_registry,
                session_id=self.matrix_session_id,
            )
        self.matrix_project_controller = matrix_session.matrix_project_controller
        self.project_creation_service = ProjectCreationApplicationService(
            self.ltr_integration_service,
            self.matrix_project_controller,
        )
        # S1-3: 移除直接构造的 ProjectSessionCoordinator。
        # 项目会话副作用统一通过 project_session_app_service (S1-2) 编排，
        # 不再由 feature controller 本地兜底。
        # 添加标志以避免重复订阅事件
        self._event_subscribed = False
        # 订阅LTR申请处理完成事件
        self._subscribe_to_events()
        # 注册 shutdown 清理（priority 45：在 MatrixController 之后、应用退出前）
        from src.core.shutdown_registry import shutdown_registry
        shutdown_registry.register(
            name="ProjectCreatorController.cleanup",
            cleanup_fn=self.cleanup,
            priority=45,
        )

    def _subscribe_to_events(self):
        """订阅事件，确保不会重复订阅"""
        if not self._event_subscribed:
            event_dispatcher.subscribe(EventTopics.LTR_APPLICATION_PROCESSED, self._on_ltr_application_processed)
            self._event_subscribed = True
            logger.info("Subscribed to ltr.application.processed event")
        else:
            logger.warning("Already subscribed to ltr.application.processed event, skipping subscription")

    def cleanup(self):
        """清理资源，取消事件订阅"""
        if self._event_subscribed:
            event_dispatcher.unsubscribe(EventTopics.LTR_APPLICATION_PROCESSED, self._on_ltr_application_processed)
            self._event_subscribed = False
            logger.info("Unsubscribed from ltr.application.processed event")
        scope = getattr(self, "_matrix_session_scope", None)
        if scope is not None and hasattr(scope, "close"):
            scope.close()
            self._matrix_session_scope = None
            return
        if (
            self.matrix_session_mode == "isolated"
            and self.matrix_session_registry is not None
            and self.matrix_session_id
            and hasattr(self.matrix_session_registry, "release_session")
        ):
            self.matrix_session_registry.release_session(self.matrix_session_id)

    def handle_create_new_project(self) -> bool:
        """
        处理创建新项目事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("Handling create new project request")

            # 显示邮件选择对话框并处理邮件数据
            success = self._show_email_selector_dialog()

            if success:
                logger.info("Successfully processed email data")
                # 继续项目创建流程
                self._continue_project_creation()
            else:
                logger.info("User cancelled or failed to process email data")

            return success
        except Exception as e:
            logger.error(f"Failed to create new project: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"创建新项目失败: {str(e)}")
            return False

    def _show_email_selector_dialog(self) -> bool:
        """
        显示邮件选择对话框

        Returns:
            是否成功获取邮件数据
        """
        return self.email_flow_coordinator.show_email_selector_dialog()

    def _continue_project_creation(self):
        """
        继续项目创建流程

        委托给附件LTR流程协调器处理附件解析、Word提取和LTR对话框启动。
        """
        self._attachment_ltr_flow_coordinator.continue_project_creation()

    def _get_attachments(self):
        """
        获取附件列表

        Returns:
            附件列表
        """
        # 这里需要从email_extractor_controller获取附件
        # 由于我们已经有了email_data，可以直接从中提取
        if self.context.email_data:
            # 转换回字典格式供服务层使用
            return [
                {
                    'filename': att.filename,
                    'content': att.content,
                    'content_type': att.content_type,
                    'size': att.size
                }
                for att in self.context.email_data.attachments
            ]
        return []

    def _show_ltr_application_dialog(self, application_data, selected_filename=''):
        """显示LTR申请窗口 — 委托给附件LTR流程协调器"""
        self._attachment_ltr_flow_coordinator.show_ltr_application_dialog(
            application_data, selected_filename
        )

    def _get_selected_attachment(self):
        """
        获取选中的附件

        Returns:
            选中的附件或None
        """
        return self.email_flow_coordinator.get_selected_attachment()

    def _handle_failed_extraction(self):
        """
        处理提取失败的情况，询问用户选择
        """
        self.email_flow_coordinator.handle_failed_extraction()

    def _reselect_attachment(self):
        """
        重新选择附件，但保持邮件信息不变
        """
        self.email_flow_coordinator.reselect_attachment()
            
    def set_project_path(self, project_path):
        """
        设置项目路径并加载LTR项目数据
        
        Args:
            project_path (str): 项目路径
        """
        # 加载LTR项目数据
        self.ltr_integration_service.load_ltr_project(project_path)
        
        # 只在LTR集成服务未设置或需要更新时才设置
        if self.matrix_project_controller.ltr_integration_service != self.ltr_integration_service:
            # 设置Matrix项目控制器中的LTR集成服务
            self.matrix_project_controller.set_ltr_integration_service(self.ltr_integration_service)

        project_context = ProjectContext.from_project_path(project_path)
        self._apply_matrix_project_context(project_context)
        
    def open_matrix_editor(self):
        """
        打开Matrix编辑器
        
        Returns:
            bool: 是否成功打开
        """
        return self.matrix_project_controller.open_matrix_workspace()

    def _apply_matrix_project_context(self, project_context: ProjectContext) -> None:
        matrix_controller = self.matrix_project_controller.matrix_controller
        matrix_controller.set_project_context(project_context)

        if self.parent_view and hasattr(self.parent_view, "set_matrix_project_context"):
            self.parent_view.set_matrix_project_context(project_context)

    def _on_ltr_application_processed(self, data):
        """
        处理LTR申请单处理完成事件，打开Matrix编辑器窗口
        
        Args:
            data: 事件数据，包含处理结果
        """
        self.ltr_result_coordinator.on_ltr_application_processed(data)

    def _open_matrix_editor_with_ltr_number(self, dl_number, project_path=None):
        """
        更新Matrix编辑器中的LTR编号和项目数据
        
        Args:
            dl_number: LTR编号
            project_path: 项目路径
        """
        self.ltr_result_coordinator.open_matrix_editor_with_ltr_number(
            dl_number,
            project_path,
        )

    def _safe_open_matrix_workspace(self, dl_number):
        """
        安全地打开Matrix工作区
        
        Args:
            dl_number: LTR编号
        """
        try:
            logger.info(f"Attempting to open Matrix editor for LTR: {dl_number}")
            
            # 打开Matrix编辑器
            if self.matrix_project_controller:
                logger.debug("Calling matrix_project_controller.open_matrix_workspace()")
                success = self.matrix_project_controller.open_matrix_workspace()
                if success:
                    logger.info(f"Successfully opened Matrix editor for LTR: {dl_number}")
                else:
                    logger.error(f"Failed to open Matrix editor for LTR: {dl_number}")
        except Exception as e:
            logger.error(f"Error opening Matrix editor with LTR number: {e}", exc_info=True)
            # 显示错误消息给用户
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"打开Matrix编辑器时出错: {str(e)}")

    def _trigger_matrix_update_after_project_creation(self, project_path):
        """
        在项目创建完成后触发 Matrix 更新
        
        Args:
            project_path: 项目路径
        """
        try:
            logger.info(f"Triggering Matrix update after project creation: {project_path}")
            project_context = ProjectContext.from_project_path(project_path)
            # S1-2: 统一入口完成状态写入 + 事件派发 + UI 副作用编排
            project_session_app_service.activate_existing_context(
                project_context,
                trigger_matrix_auto_import=False,  # Matrix import 由事件消费者处理
            )

        except Exception as e:
            logger.error(f"Failed to trigger Matrix update after project creation: {e}", exc_info=True)
    
    def _switch_to_matrix_page(self):
        """切换到 Matrix 编辑器页面"""
        try:
            if hasattr(self.parent_view, '_nav_list') and self.parent_view._nav_list:
                self.parent_view._nav_list.setCurrentRow(0)
                logger.debug("Switched to Matrix editor page after project creation")
        except Exception as e:
            logger.error(f"Failed to switch to Matrix page: {e}")
