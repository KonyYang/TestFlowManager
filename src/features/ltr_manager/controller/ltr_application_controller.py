"""
LTR申请单控制器模块
处理LTR申请单的业务逻辑和事件
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QMessageBox
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
from src.features.ltr_manager.service.ltr_application_service import LTRApplicationService
from src.features.ltr_manager.view.ltr_application_dialog import LTRApplicationDialog


class LTRApplicationController:
    """
    LTR申请单控制器类
    处理LTR申请单的业务逻辑和事件
    """

    def __init__(self, parent_view=None):
        """
        初始化LTR申请单控制器

        Args:
            parent_view: 父窗口视图实例
        """
        self.parent_view = parent_view
        self.service = LTRApplicationService()
        self.application_data = LTRApplicationData()

    def handle_word_application(self, doc_filepath: str) -> bool:
        """
        处理Word格式的LTR申请单

        Args:
            doc_filepath: Word文档路径

        Returns:
            是否处理成功
        """
        try:
            logger.info(f"Handling Word application: {doc_filepath}")

            # 处理Word申请单
            self.application_data = self.service.process_word_application(doc_filepath)

            if self.application_data.status == "failed":
                logger.error(f"Failed to process Word application: {self.application_data.error_message}")
                if self.parent_view:
                    QMessageBox.critical(
                        self.parent_view,
                        "错误",
                        f"处理申请单失败: {self.application_data.error_message}"
                    )
                return False

            logger.info("Successfully processed Word application")
            return True

        except Exception as e:
            logger.error(f"Error handling Word application: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"处理申请单时出错: {str(e)}")
            return False

    def handle_new_application(self) -> bool:
        """
        处理新的空白LTR申请单

        Returns:
            是否处理成功
        """
        try:
            logger.info("Handling new blank LTR application")

            # 创建新的空白申请单
            self.application_data = self.service.create_new_application()

            logger.info("Successfully created new blank LTR application")
            return True

        except Exception as e:
            logger.error(f"Error handling new application: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"创建新申请单时出错: {str(e)}")
            return False

    def show_application_dialog(self) -> Optional[Dict[str, Any]]:
        """
        显示LTR申请单对话框

        Returns:
            用户操作结果和修改后的数据，如果用户取消则返回None
        """
        try:
            logger.debug("Showing LTR application dialog")

            # 准备传递给对话框的数据
            dialog_data = {
                'dl_number': self.application_data.dl_number,
                'data': self.application_data.to_dict()
            }

            # 创建并显示对话框
            dialog = LTRApplicationDialog(dialog_data, self.parent_view)
            result = dialog.exec_()

            if result == LTRApplicationDialog.Accepted:
                # 获取用户修改后的数据
                modified_data = dialog.get_modified_data()
                logger.info("User accepted the application dialog")
                return {
                    'action': 'accepted',
                    'data': modified_data
                }
            else:
                logger.info("User cancelled the application dialog")
                return None

        except Exception as e:
            logger.error(f"Error showing application dialog: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"显示申请单对话框时出错: {str(e)}")
            return None

    def validate_application(self) -> Dict[str, Any]:
        """
        验证当前申请单数据

        Returns:
            验证结果
        """
        return self.service.validate_application_data(self.application_data)

    def get_application_data(self) -> LTRApplicationData:
        """
        获取当前申请单数据

        Returns:
            当前的LTRApplicationData对象
        """
        return self.application_data

    def set_application_data(self, data: LTRApplicationData):
        """
        设置申请单数据

        Args:
            data: LTRApplicationData对象
        """
        self.application_data = data
