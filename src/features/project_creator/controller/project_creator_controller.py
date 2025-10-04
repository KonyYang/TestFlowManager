"""
项目创建控制器模块
处理项目创建流程，包括邮件提取、文档解析等
"""
from PyQt5.QtWidgets import QDialog, QMessageBox
from src.core.logger import logger
from src.features.project_creator.service.project_creator_service import ProjectCreatorService
from src.features.project_creator.model.project_creator_data import EmailData, EmailAttachment, ProjectCreationContext
from src.features.email_extractor.view.email_selector_dialog import EmailSelectorDialog
from src.features.email_extractor.controller.email_extractor_controller import EmailExtractorController


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
            # 创建邮件选择对话框
            dialog = EmailSelectorDialog(self.parent_view)
            controller = EmailExtractorController(dialog)

            # 初始化控制器
            if controller.initialize():
                # 显示对话框
                result = dialog.exec_()

                # 如果用户点击了"选择"按钮（即接受了对话框）
                if result == QDialog.Accepted:
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

            # 创建临时项目结构
            temp_folder = project_service.create_temp_folder_and_save_attachments(
                self.context.selected_file_path,
                self._get_attachments()
            )

            self.context.temp_folder = temp_folder

            # TODO: 将来可能需要使用temp_folder路径进行进一步操作
            # 例如：创建项目结构、保存处理结果等

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
                    self._show_ltr_application_dialog(result)
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

    def _show_ltr_application_dialog(self, application_data):
        """显示LTR申请窗口"""
        try:

            # 准备LTR数据
            dl_data = {
                'dl_number': '',  # 新申请，没有DL编号
                'data': application_data if application_data else {}
            }


            # 显示对话框
            dialog.exec_()

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

        msg_box = QMessageBox(self.parent_view)
        msg_box.setWindowTitle("选择操作")
        msg_box.setText("没有找到有效的申请单信息，您希望？")
        msg_box.setIcon(QMessageBox.Question)

        blank_form_button = msg_box.addButton("填写空白申请表", QMessageBox.AcceptRole)
        reselect_button = msg_box.addButton("重新选择附件", QMessageBox.RejectRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.DestructiveRole)

        msg_box.setDefaultButton(blank_form_button)
        result = msg_box.exec_()

        if msg_box.clickedButton() == blank_form_button:
            # 填写空白申请表
            self._show_ltr_application_dialog(None)
        elif msg_box.clickedButton() == reselect_button:
            # 重新选择附件，但保持邮件信息不变
            self._reselect_attachment()
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

            # 设置邮件上下文信息
            if self.context.email_data:
                # 准备邮件信息
                subject = self.context.email_data.subject
                sender = self.context.email_data.sender
                received_time = self.context.email_data.received_time
                email_info = f"主题: {subject}\n发件人: {sender}  时间: {received_time}"

                attachments = []
                for att in self.context.email_data.attachments:
                        'filename': att.filename,
                        'content': att.content,
                        'content_type': att.content_type,
                        'size': att.size

                # 设置邮件上下文
                dialog.set_email_context(email_info, attachments, self.context.selected_file_path)

            # 显示对话框
            result = dialog.exec_()

            # 如果用户点击了"选择"按钮
            if result == QDialog.Accepted:
                # 获取选中的附件
                selected_attachment = dialog.get_selected_attachment()

                if selected_attachment:
                    # 更新选中的附件
                    self.selected_attachment = selected_attachment
                    logger.info(f"Reselected attachment: {selected_attachment.get('filename', 'Unknown')}")

                    # 重新尝试处理项目创建
                    self._continue_project_creation()
                else:
                    logger.warning("No attachment selected during reselection")
            else:
                logger.info("User cancelled attachment reselection")

        except Exception as e:
            logger.error(f"Error during attachment reselection: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"重新选择附件失败: {str(e)}")

