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
        # 添加事件订阅
        from src.core.event_dispatcher import event_dispatcher
        event_dispatcher.subscribe("ltr.application.processed", self._on_ltr_application_processed)


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
            dialog = LTRApplicationDialog(dialog_data, self.parent_view, self)
            result = dialog.exec_()

            if result == LTRApplicationDialog.Accepted:
                # 获取用户修改后的数据
                modified_data = dialog.get_modified_data()
                # 处理数据转换
                processed_data = self._process_application_data(modified_data)
                logger.info("User accepted the application dialog")

                # 发布事件而不是直接返回数据
                from src.core.event_dispatcher import event_dispatcher
                event_dispatcher.dispatch("ltr.application.confirmed", {
                    "dl_number": self.application_data.dl_number,
                    "data": processed_data,
                    "controller": self
                })

                return {
                    'action': 'accepted',
                    'data': processed_data
                }
            else:
                logger.info("User cancelled the application dialog")
                return None

        except Exception as e:
            logger.error(f"Error showing application dialog: {e}")
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"显示申请单对话框时出错: {str(e)}")
            return None


    def _process_application_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理申请单数据，进行必要的转换

        Args:
            raw_data: 原始数据

        Returns:
            处理后的数据
        """
        processed_data = raw_data.copy()

        # project_type 映射转换
        project_type_map = {
            "NPD": "New Product Development",
            "PEX": "Product Extension",
            "OPS": "Operational Support",
            "CR": "Cost Reduction",
            "ADM": "Lab Activities (Lab Use Only)"
        }

        if 'project_type' in processed_data and processed_data['project_type'] in project_type_map:
            processed_data['project_type'] = project_type_map[processed_data['project_type']]

        # test_type 映射转换
        test_type_map = {
            "Partial Qualification": "Product/Process Development",
            "Qualification": "Product/Process Qualification",
            "Failure Analysis": "Lab/Failure Analysis",
            "Other": "Customer Specific Testing",
            "Analysis": "Customer Specific Testing",
            "Chemical": "Customer Specific Testing",
            "Electrical": "Customer Specific Testing",
            "Environmental": "Customer Specific Testing",
            "Whisker": "Customer Specific Testing",
            "Mechanical": "Customer Specific Testing",
            "ORT": "Customer Specific Testing",
            "Solderability": "Customer Specific Testing",
        }

        if 'test_type' in processed_data and processed_data['test_type'] in test_type_map:
            processed_data['test_type'] = test_type_map[processed_data['test_type']]

        return processed_data

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

    # 可以暂时保留这些方法，但添加注释说明
    def open_ltr(self, dl_number: str):
        """
        查看LTR申请单 - 已弃用，按钮已移除

        Args:
            dl_number: DL编号
        """
        # 实现查看LTR的逻辑
        logger.info(f"Opening LTR: {dl_number}")
        # 后续实现

    def apply_ltr(self, application_data: Dict[str, Any]):
        """
        申请LTR - 已弃用，按钮已移除

        Args:
            application_data: 申请单数据
        """
        # 实现申请LTR的逻辑
        logger.info("Applying LTR")
        # 后续实现

    def update_ltr(self, dl_number: str, application_data: Dict[str, Any]):
        """
        更新LTR - 已弃用，按钮已移除

        Args:
            dl_number: DL编号
            application_data: 申请单数据
        """
        # 实现更新LTR的逻辑
        logger.info(f"Updating LTR: {dl_number}")
        # 后续实现


    def _on_ltr_application_processed(self, data):
        """
        处理LTR申请单处理完成事件

        Args:
            data: 事件数据，包含处理结果
        """
        dl_number = data.get("dl_number")
        status = data.get("status")

        if status == "success":
            logger.info(f"LTR application processed successfully: {dl_number}")
            # 可以在这里添加进一步的处理逻辑，比如更新UI状态
            if self.parent_view:
                # 假设parent_view有更新状态的方法
                # self.parent_view.update_status(f"LTR申请单处理完成: {dl_number}")
                pass
        else:
            logger.error(f"LTR application processing failed: {dl_number}")
            # 可以在这里添加错误处理逻辑
            if self.parent_view:
                QMessageBox.warning(self.parent_view, "警告", f"LTR申请单处理失败: {dl_number}")
