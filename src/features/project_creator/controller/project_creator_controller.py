# src/features/project_creator/controller/project_creator_controller.py
import os

from PyQt5.QtWidgets import QDialog, QMessageBox
from src.core.logger import logger
from src.features.project_creator.service.project_creator_service import ProjectCreatorService
from src.features.project_creator.model.project_creator_data import EmailData, EmailAttachment, ProjectCreationContext
from src.features.email_extractor.view.email_selector_dialog import EmailSelectorDialog
from src.features.email_extractor.controller.email_extractor_controller import EmailExtractorController
# 添加LTR项目集成服务
from src.features.project_creator.service.ltr_project_integration_service import LTRProjectIntegrationService
# 添加Matrix项目控制器
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController
# 添加事件调度器
from src.core.event_dispatcher import event_dispatcher
# 添加状态管理器
from src.core.state_manager import state_manager
from src.core.project_context import ProjectContext


class ProjectCreatorController:
    """
    项目创建控制器类
    处理项目创建流程，包括邮件提取、文档解析等
    """

    def __init__(self, parent_view=None):
        """
        初始化项目创建控制器

        Args:
            parent_view: 父窗口视图实例
        """
        self.parent_view = parent_view
        self.context = ProjectCreationContext()
        self.email_extractor_controller = None  # 添加这一行来保存controller引用
        self.selected_attachment = None  # 用于存储选中的附件
        # 添加LTR项目集成服务
        self.ltr_integration_service = LTRProjectIntegrationService()
        # 添加Matrix项目控制器
        self.matrix_project_controller = MatrixProjectController(parent_view)
        # 添加标志以避免重复订阅事件
        self._event_subscribed = False
        # 订阅LTR申请处理完成事件
        self._subscribe_to_events()

    def _subscribe_to_events(self):
        """订阅事件，确保不会重复订阅"""
        if not self._event_subscribed:
            event_dispatcher.subscribe("ltr.application.processed", self._on_ltr_application_processed)
            self._event_subscribed = True
            logger.info("Subscribed to ltr.application.processed event")
        else:
            logger.warning("Already subscribed to ltr.application.processed event, skipping subscription")

    def cleanup(self):
        """清理资源，取消事件订阅"""
        if self._event_subscribed:
            event_dispatcher.unsubscribe("ltr.application.processed", self._on_ltr_application_processed)
            self._event_subscribed = False
            logger.info("Unsubscribed from ltr.application.processed event")

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
        try:
            logger.info("正在初始化邮件提取控制器...")
            # 创建邮件选择对话框
            dialog = EmailSelectorDialog(self.parent_view)
            controller = EmailExtractorController(dialog)

            # 初始化控制器
            if controller.initialize():
                logger.info("邮件提取控制器初始化成功")
                # 显示对话框
                result = dialog.exec_()

                # 如果用户点击了"选择"按钮（即接受了对话框）
                if result == QDialog.Accepted:
                    logger.debug("Email selector dialog accepted")
                    # 保存controller引用以便后续使用
                    self.email_extractor_controller = controller
                    # 保存选中的附件
                    self.selected_attachment = controller.get_selected_attachment()
                    # 获取处理后的邮件数据
                    email_data_dict = controller.get_processed_email_data()
                    self.context.selected_file_path = controller.get_selected_file_path()

                    if email_data_dict:
                        # 转换为EmailData对象
                        attachments = [
                            EmailAttachment(
                                filename=att.get('filename', ''),
                                content=att.get('content', b''),
                                content_type=att.get('content_type'),
                                size=att.get('size')
                            )
                            for att in email_data_dict.get("attachments", [])
                        ]

                        self.context.email_data = EmailData(
                            subject=email_data_dict.get("subject", ""),
                            sender=email_data_dict.get("sender", ""),
                            received_time=email_data_dict.get("received_time", ""),
                            body=email_data_dict.get("body", ""),
                            attachments=attachments,
                            file_path=self.context.selected_file_path or ""
                        )

                        logger.info("Successfully obtained email data")
                        return True
                else:
                    # 用户点击了取消按钮
                    logger.info("User cancelled email selection")
                    return False  # 明确返回False表示取消操作

            return False

        except Exception as e:
            logger.error(f"Error showing email selector dialog: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"无法打开邮件选择对话框: {str(e)}")
            return False

    def _continue_project_creation(self):
        """
        继续项目创建流程
        """
        try:
            logger.debug("Continuing project creation process")

            # 创建项目创建服务实例
            project_service = ProjectCreatorService()

            # 获取来自EmailExtractor的临时文件夹路径
            temp_folder = None
            if hasattr(self, 'email_extractor_controller') and self.email_extractor_controller:
                temp_folder = self.email_extractor_controller.get_temp_folder_path()
                logger.info(f"使用EmailExtractor提供的临时文件夹路径: {temp_folder}")

            self.context.temp_folder = temp_folder

            # 只处理用户选中的附件
            selected_attachment = self._get_selected_attachment()
            word_attachment = None

            if selected_attachment:
                # 检查选中的附件是否为Word文档
                filename = selected_attachment.get('filename', '').lower()
                if filename.endswith(('.doc', '.docx')):
                    word_attachment = selected_attachment
                    logger.info(f"Using selected attachment: {filename}")
                else:
                    # 选中的附件不是Word文档
                    logger.info(f"Selected attachment is not a Word document: {filename}")
            else:
                # 没有选中的附件
                logger.info("No attachment selected by user")

            if word_attachment:
                # 处理Word附件
                result = project_service.process_word_attachment(word_attachment)

                if result and not result.get("error"):
                    # 成功提取数据，显示LTR申请窗口
                    logger.debug("Successfully processed Word attachment, showing LTR application dialog")
                    self._show_ltr_application_dialog(result, selected_attachment.get('filename', ''))
                else:
                    # 未能提取数据，询问用户选择
                    error_msg = result.get("error", "未知错误") if result else "处理过程中发生错误"
                    logger.warning(f"Failed to process Word attachment: {error_msg}")
                    self._handle_failed_extraction()
            else:
                # 没有找到Word附件或没有选中附件，询问用户选择
                logger.info("No valid Word attachment found or selected, prompting user for action")
                self._handle_failed_extraction()

            logger.info("Project creation process continued successfully")

        except Exception as e:
            logger.error(f"Error continuing project creation process: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"继续项目创建流程失败: {str(e)}")

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
        """显示LTR申请窗口"""
        try:
            # 准备LTR数据
            dl_data = {
                'dl_number': '',  # 新申请，没有DL编号
                'data': application_data if application_data else {}
            }

            # 使用正确的LTR控制器
            from src.features.ltr_manager.controller.ltr_application_controller import LTRApplicationController
            ltr_controller = LTRApplicationController(self.parent_view)
            
            # 设置选中的文件名
            ltr_controller.set_selected_filename(selected_filename)
            
            # 获取临时文件夹路径（如果有的话）
            temp_folder_path = None
            if hasattr(self, 'email_extractor_controller') and self.email_extractor_controller:
                temp_folder_path = self.email_extractor_controller.get_temp_folder_path()
                logger.debug(f"从email_extractor_controller获取到的临时文件夹路径: {temp_folder_path}")
                # 检查路径是否存在
                import os
                if temp_folder_path and os.path.exists(temp_folder_path):
                    logger.debug(f"临时文件夹路径存在: {temp_folder_path}")
                else:
                    logger.warning(f"临时文件夹路径不存在或为空: {temp_folder_path}")

            # 通过控制器显示对话框并传递临时文件夹路径
            # 将application_data传递给控制器，以便正确初始化申请单数据
            if application_data:
                # 创建一个新的申请单数据对象
                from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
                ltr_controller.set_application_data(LTRApplicationData.from_dict(application_data))
            
            result = ltr_controller.show_application_dialog(temp_folder_path)
            # 注意：这里不需要处理result，因为LTRApplicationController会通过事件系统处理后续操作

        except Exception as e:
            logger.error(f"显示LTR申请窗口时出错: {e}")
            if self.parent_view:
                QMessageBox.warning(self.parent_view, "警告", f"无法打开LTR申请窗口: {str(e)}")


    def _get_selected_attachment(self):
        """
        获取选中的附件

        Returns:
            选中的附件或None
        """
        # 优先使用保存的选中附件
        if self.selected_attachment:
            filename = self.selected_attachment.get('filename', 'Unknown') if self.selected_attachment else 'None'
            logger.debug(f"Using saved selected attachment: {filename}")
            return self.selected_attachment

        # 备用方案：通过email_extractor_controller获取选中的附件
        if hasattr(self, 'email_extractor_controller') and self.email_extractor_controller:
            attachment = self.email_extractor_controller.get_selected_attachment()
            filename = attachment.get('filename', 'Unknown') if attachment else 'None'
            logger.debug(f"Got attachment from controller: {filename}")
            return attachment

        logger.debug("No selected attachment found")
        return None

    def _handle_failed_extraction(self):
        """
        处理提取失败的情况，询问用户选择
        """
        from PyQt5.QtWidgets import QMessageBox

        logger.debug("Handling failed extraction - showing options dialog")
        msg_box = QMessageBox(self.parent_view)
        msg_box.setWindowTitle("选择操作")
        msg_box.setText("没有找到有效的申请单信息，您希望？")
        msg_box.setIcon(QMessageBox.Question)

        blank_form_button = msg_box.addButton("填写空白申请表", QMessageBox.AcceptRole)
        reselect_button = msg_box.addButton("重新选择附件", QMessageBox.RejectRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.DestructiveRole)

        msg_box.setDefaultButton(blank_form_button)
        result = msg_box.exec_()
        
        logger.debug(f"User selection in options dialog: {msg_box.clickedButton()}")

        if msg_box.clickedButton() == blank_form_button:
            logger.debug("User selected to fill blank form")
            # 填写空白申请表
            self._show_ltr_application_dialog(None, '')  # 空文件名
        elif msg_box.clickedButton() == reselect_button:
            logger.debug("User selected to reselect attachment")
            # 重新选择附件，但保持邮件信息不变
            self._reselect_attachment()
        else:
            logger.debug("User cancelled the operation")
        # 如果点击取消，则不执行任何操作

    def _reselect_attachment(self):
        """
        重新选择附件，但保持邮件信息不变
        """
        try:
            logger.debug("Reselecting attachment while keeping email data")

            # 创建邮件选择对话框
            from src.features.email_extractor.view.email_selector_dialog import EmailSelectorDialog
            dialog = EmailSelectorDialog(self.parent_view)
            
            # 为对话框创建并关联控制器
            from src.features.email_extractor.controller.email_extractor_controller import EmailExtractorController
            controller = EmailExtractorController(dialog)
            controller.initialize()

            # 设置邮件上下文信息
            if self.context.email_data:
                # 准备邮件信息
                subject = self.context.email_data.subject
                sender = self.context.email_data.sender
                received_time = self.context.email_data.received_time
                email_info = f"主题: {subject}\n发件人: {sender}  时间: {received_time}"

                attachments = []
                for att in self.context.email_data.attachments:
                    attachments.append({
                        'filename': att.filename,
                        'content': att.content,
                        'content_type': att.content_type,
                        'size': att.size
                    })

                # 设置邮件上下文
                dialog.set_email_context(email_info, attachments, self.context.email_data.file_path)
                
                # 重要：确保对话框知道这是重新选择模式，不需要重新处理MSG文件
                dialog.is_reselect_mode = True

            # 显示对话框
            result = dialog.exec_()
            
            logger.debug(f"Reselect attachment dialog result: {result}")
            
            # 如果用户确认选择
            if result == EmailSelectorDialog.Accepted:
                # 获取选中的附件
                selected_attachment = dialog.get_selected_attachment()
                if selected_attachment:
                    # 更新上下文中的附件信息
                    self.context.selected_attachment = selected_attachment
                    # 更新选中的附件变量，确保后续流程可以获取到
                    self.selected_attachment = selected_attachment
                    logger.debug(f"已重新选择附件: {selected_attachment.get('filename', 'Unknown')}")
                    
                    # 更新界面显示（如果父视图有相应的方法）
                    if self.parent_view and hasattr(self.parent_view, 'update_attachment_info'):
                        filename = selected_attachment.get('filename', 'Unknown')
                        self.parent_view.update_attachment_info(filename)
                        
                    # 继续项目创建流程
                    self._continue_project_creation()
                else:
                    logger.debug("用户未选择附件")
                    # 当用户未选择附件时，显示选择操作对话框
                    self._handle_failed_extraction()
            else:
                logger.debug("用户取消了附件重新选择")

        except Exception as e:
            logger.error(f"重新选择附件时发生错误: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self.parent_view, "错误", f"重新选择附件时发生错误: {str(e)}")
            
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
        dl_number = data.get("dl_number")
        status = data.get("status")
        project_path = data.get("project_path")  # 获取项目路径

        logger.debug(f"_on_ltr_application_processed called with dl_number={dl_number}, status={status}, project_path={project_path}")

        # 如果没有DL编号或状态不是success，不执行任何操作
        if not dl_number or not dl_number.strip() or status != "success":
            logger.warning(f"LTR application processed but no valid DL number provided or status not success, dl_number={dl_number}, status={status}")
            return

        logger.info(f"LTR application processed successfully: {dl_number}")
        # 更新主窗口标题显示项目信息
        if self.parent_view:
            logger.debug(f"Setting main window title to: TestFlow Manager - 项目: {dl_number}")
            self.parent_view.setWindowTitle(f"TestFlow Manager - 项目: {dl_number}")
            logger.debug(f"Main window title after setting: {self.parent_view.windowTitle()}")
            
            # 更新顶栏DL编号显示
            if hasattr(self.parent_view, 'update_dl_number_display'):
                self.parent_view.update_dl_number_display(dl_number)
        # 使用QTimer延迟执行UI操作，避免在事件处理中直接操作UI
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._open_matrix_editor_with_ltr_number(dl_number, project_path))

    def _open_matrix_editor_with_ltr_number(self, dl_number, project_path=None):
        """
        更新Matrix编辑器中的LTR编号和项目数据
        
        Args:
            dl_number: LTR编号
            project_path: 项目路径
        """
        try:
            logger.info(f"Updating Matrix editor with LTR number: {dl_number}")
            logger.debug(f"Received dl_number: {dl_number}, project_path: {project_path}")
            
            # 如果dl_number为空，尝试从application_data.json文件中读取
            if not dl_number and project_path:
                logger.debug("dl_number is empty, trying to read from application_data.json")
                try:
                    # 构造application_data.json文件路径
                    json_file_path = os.path.join(project_path, "application_data.json")
                    if os.path.exists(json_file_path):
                        import json
                        with open(json_file_path, 'r', encoding='utf-8') as f:
                            project_data = json.load(f)
                            dl_number = project_data.get("DL", "")
                            logger.debug(f"Read dl_number from application_data.json: {dl_number}")
                    else:
                        logger.warning(f"application_data.json not found at: {json_file_path}")
                except Exception as e:
                    logger.error(f"Error reading dl_number from application_data.json: {e}")
            
            # 设置LTR编号到Matrix控制器
            if self.matrix_project_controller and self.matrix_project_controller.matrix_controller:
                self.matrix_project_controller.matrix_controller.set_ltr_number(dl_number)
                logger.debug(f"Set LTR number {dl_number} to Matrix controller")
                
            # 如果提供了项目路径，则设置项目路径
            if project_path and dl_number:
                logger.debug(f"Project path provided: {project_path}")
                # 设置项目路径到状态管理器
                state_manager.set_state("current_project", project_path)
                project_context = ProjectContext.from_project_path(project_path, dl_number)
                state_manager.set_state("current_project_context", project_context)
                
                # 通知其他组件项目已打开
                event_dispatcher.dispatch("project.opened", project_context.to_event_data())
                
                # 触发Matrix自动导入功能（延迟执行，确保UI已就绪）
                from PyQt5.QtCore import QTimer
                if self.parent_view and hasattr(self.parent_view, 'auto_import_from_project'):
                    QTimer.singleShot(100, lambda: self._trigger_matrix_update_after_project_creation(project_path))
                
                # 更新主窗口标题显示项目信息
                if self.parent_view:
                    logger.debug(f"Setting main window title in _open_matrix_editor_with_ltr_number to: TestFlow Manager - 项目: {dl_number}")
                    self.parent_view.setWindowTitle(f"TestFlow Manager - 项目: {dl_number}")
                    logger.debug(f"Main window title after setting in _open_matrix_editor_with_ltr_number: {self.parent_view.windowTitle()}")
                    
                    # 更新顶栏DL编号显示
                    if hasattr(self.parent_view, 'update_dl_number_display'):
                        self.parent_view.update_dl_number_display(dl_number)
                
                # 根据DL编号构造项目根目录路径
                from src.core.config_manager import config_manager
                default_project_path = config_manager.get("paths.default_project_path", "D:\\TestFlowManager\\Projects")
                project_root_path = os.path.join(default_project_path, dl_number)
                logger.info(f"Constructed project root path: {project_root_path}")
                
                # 检查构造的路径是否存在JSON文件
                json_files = []
                try:
                    json_files = [f for f in os.listdir(project_root_path) if f.endswith('.json')]
                    logger.info(f"Found JSON files in constructed path: {json_files}")
                except Exception as e:
                    logger.error(f"Error listing directory {project_root_path}: {e}")
                
                if json_files:
                    # 通过LTR集成服务加载项目数据
                    loaded_data = self.ltr_integration_service.load_ltr_project(project_root_path)
                    logger.info(f"Loaded LTR project data result: {loaded_data is not None}")
                    logger.info(f"Project data file path from LTR service: {self.ltr_integration_service.project_data_file_path}")
                else:
                    # 直接使用传入的project_path加载项目数据
                    logger.info(f"No JSON files found in constructed path, using provided project_path: {project_path}")
                    loaded_data = self.ltr_integration_service.load_ltr_project(project_path)
                    logger.info(f"Loaded LTR project data result: {loaded_data is not None}")
                    logger.info(f"Project data file path from LTR service: {self.ltr_integration_service.project_data_file_path}")
                
                # 只在LTR集成服务未设置或需要更新时才设置
                if self.matrix_project_controller.ltr_integration_service != self.ltr_integration_service:
                    self.matrix_project_controller.set_ltr_integration_service(self.ltr_integration_service)
                
                self._apply_matrix_project_context(project_context)
                
                logger.debug(f"Set project path {project_path} to Matrix controller via LTR integration service")
                
                # 初始化Matrix数据
                if self.matrix_project_controller.ltr_integration_service and self.matrix_project_controller.ltr_integration_service.is_project_loaded():
                    logger.debug("Initializing Matrix with LTR data")
                    self.matrix_project_controller.matrix_controller.initialize_with_ltr_data()
                    
                    # 更新Matrix视图以反映新数据
                    if self.parent_view and hasattr(self.parent_view, 'refresh_table'):
                        self.parent_view.refresh_table()
            else:
                logger.warning("No project path or DL number provided")
                
        except Exception as e:
            logger.error(f"Error updating Matrix editor with LTR number: {e}", exc_info=True)
            # 显示错误消息给用户
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"更新Matrix编辑器时出错: {str(e)}")

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
            
            # 设置当前项目到状态管理器
            from src.core.state_manager import state_manager
            state_manager.set_state("current_project", project_path)
            state_manager.set_state("current_project_context", ProjectContext.from_project_path(project_path))
            
            # 调用主窗口的 Matrix 自动导入方法
            if hasattr(self.parent_view, 'auto_import_from_project'):
                self.parent_view.auto_import_from_project()
                logger.debug("Successfully triggered Matrix auto-import in main window")
            
            if hasattr(self.parent_view, 'refresh_table'):
                self.parent_view.refresh_table()
                logger.debug("Successfully updated Matrix table display")
            
            # 切换回 Matrix 页面（索引为 0）
            from PyQt5.QtCore import QTimer
            if hasattr(self.parent_view, '_nav_list'):
                QTimer.singleShot(100, lambda: self._switch_to_matrix_page())
                
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
