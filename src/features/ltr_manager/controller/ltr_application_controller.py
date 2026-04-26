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
from src.utils.ltr_data_manager import LTRDataManager
from src.features.ltr_manager.controller.ltr_application_project_creation_coordinator import LTRApplicationProjectCreationCoordinator
from src.core.event_dispatcher import event_dispatcher, EventTopics


class LTRApplicationController:
    """
    LTR申请单控制器类
    处理LTR申请单的业务逻辑和事件
    """

    def __init__(self, parent_view=None, folder_manager_factory=None):
        """
        初始化LTR申请单控制器

        Args:
            parent_view: 父窗口视图实例
            folder_manager_factory: 文件夹管理器工厂函数（可选，用于依赖注入）
        """
        self.parent_view = parent_view
        self.service = LTRApplicationService()
        self.application_data = LTRApplicationData()
        
        # 依赖注入：使用工厂函数或延迟导入
        self._folder_manager_factory = folder_manager_factory
        self._folder_manager_instance = None
        
        # 添加LTR数据管理器
        self.ltr_data_manager = LTRDataManager()
        
        # 项目创建协调器（延迟初始化，需要 folder_manager）
        self._project_creation_coordinator = None
        
        # 添加事件订阅（带防重复标志）
        self._event_subscribed = False
        self._subscribe_to_ltr_events()
        
        # 添加属性来存储选中的文件名
        self.selected_filename = None
    
    @property
    def folder_manager(self):
        """惰性获取 folder_manager 实例"""
        if self._folder_manager_instance is None:
            if self._folder_manager_factory:
                # 使用注入的工厂函数
                self._folder_manager_instance = self._folder_manager_factory(self.parent_view)
            else:
                # 默认行为：延迟导入并创建
                from src.features.folder_manager.controller.folder_manager_controller import FolderManagerController
                self._folder_manager_instance = FolderManagerController(self.parent_view)
        return self._folder_manager_instance
    
    @property
    def project_creation_coordinator(self):
        """惰性获取 project_creation_coordinator 实例"""
        if self._project_creation_coordinator is None:
            from src.features.ltr_manager.controller.ltr_application_project_creation_coordinator import LTRApplicationProjectCreationCoordinator
            self._project_creation_coordinator = LTRApplicationProjectCreationCoordinator(
                self.folder_manager, self.ltr_data_manager
            )
        return self._project_creation_coordinator

    def _subscribe_to_ltr_events(self):
        """订阅 LTR 事件，避免重复订阅"""
        if not self._event_subscribed:
            event_dispatcher.subscribe(EventTopics.LTR_APPLICATION_PROCESSED, self._on_ltr_application_processed)
            self._event_subscribed = True
            logger.info("LTRApplicationController: Subscribed to ltr.application.processed")
        else:
            logger.warning("LTRApplicationController: Already subscribed, skipping")

    def cleanup(self):
        """清理资源，取消事件订阅"""
        if self._event_subscribed:
            try:
                event_dispatcher.unsubscribe(
                    EventTopics.LTR_APPLICATION_PROCESSED,
                    self._on_ltr_application_processed,
                )
                self._event_subscribed = False
                logger.info("LTRApplicationController: Unsubscribed from ltr.application.processed")
            except Exception as e:
                logger.warning(f"LTRApplicationController: Failed to unsubscribe: {e}")


    def show_application_dialog(self, temp_folder_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        显示LTR申请单对话框

        Args:
            temp_folder_path: 临时文件夹路径（可选）

        Returns:
            用户操作结果和修改后的数据，如果用户取消则返回None
        """
        try:
            logger.debug("Showing LTR application dialog")
            logger.debug(f"传递给对话框的临时文件夹路径: {temp_folder_path}")

            # 准备传递给对话框的数据
            dialog_data = {
                'dl_number': self.application_data.dl_number,
                'data': self.application_data.to_dict()
            }

            # 直接使用已有的 application_data，避免重复解析 Word 文档。
            # 上游（ProjectCreatorController / EmailExtractorController）已通过
            # set_application_data() 传入完整的解析结果，无需再次读取同一文件。
            extracted_word_data = self.application_data.to_dict() if self.application_data else None
            if extracted_word_data:
                logger.debug(f"复用已有的 application_data (file_path={getattr(self.application_data, 'file_path', None)})")

            # 创建并显示对话框，传递临时文件夹路径和提取的Word文档数据
            dialog = LTRApplicationDialog(dialog_data, self.parent_view, self, temp_folder_path, extracted_word_data)
            logger.debug(f"LTRApplicationDialog创建完成，传递的temp_folder_path: {temp_folder_path}")
            result = dialog.exec_()
            
            logger.debug(f"LTRApplicationDialog exec_ result: {result}")
            logger.debug(f"LTRApplicationDialog final result: {dialog.result()}")
            
            # 注意：由于我们在LTRApplicationDialog.accept()中使用了QTimer，
            # 这里的result可能不会立即反映对话框的真实状态。
            # 我们需要通过其他方式获取数据

            # 检查对话框是否接受了用户输入
            if dialog.result() == LTRApplicationDialog.Accepted:
                logger.debug("LTRApplicationDialog was accepted by user")
                # 获取用户修改后的数据
                modified_data = dialog.get_modified_data()
                # 处理数据转换
                processed_data = self._process_application_data(modified_data)
                logger.info("User accepted the application dialog")

                # 发布事件而不是直接返回数据
                # 注意：对于新申请单，dl_number是空的，因为还没有分配编号
                event_dispatcher.dispatch(EventTopics.LTR_APPLICATION_CONFIRMED, {
                    "dl_number": self.application_data.dl_number,  # 可能为空
                    "data": processed_data,
                    "controller": self
                })

                return {
                    'action': 'accepted',
                    'data': processed_data
                }
            else:
                logger.info("User cancelled the application dialog")
                logger.debug(f"LTRApplicationDialog result code: {dialog.result()}")
                return None

        except Exception as e:
            logger.error(f"Error showing application dialog: {e}", exc_info=True)
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "错误", f"显示申请单对话框时出错: {str(e)}")
            return None

    def apply_ltr_number(self, form_data: Dict[str, Any], parent=None, temp_folder_path: Optional[str] = None, extracted_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理LTR编号申请请求

        Args:
            form_data: 表单数据
            parent: 父窗口
            temp_folder_path: 临时文件夹路径（可选）
            extracted_data: 从Word文档提取的完整数据（可选）

        Returns:
            处理结果
        """
        logger.info("开始处理LTR编号申请请求")
        logger.debug(f"apply_ltr_number接收到的临时文件夹路径: {temp_folder_path}")

        try:
            # 验证表单数据
            if not form_data:
                return {"success": False, "error": "表单数据为空"}

            # 直接调用服务层处理申请
            result = self.service.apply_ltr(form_data, parent)

            # 如果申请成功，询问是否创建项目文件夹
            if result.get("success") and result.get("ltr_number"):
                reply = QMessageBox.question(
                    parent,
                    "创建项目文件夹",
                    f"LTR编号 {result['ltr_number']} 申请成功。\n\n是否创建以此编号为名的项目文件夹并保存申请数据？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    # 委托给项目创建协调器
                    creation_result = self.project_creation_coordinator.create_project_folder(
                        form_data=form_data,
                        ltr_number=result['ltr_number'],
                        selected_filename=self.selected_filename,
                        extracted_data=extracted_data,
                        temp_folder_path=temp_folder_path
                    )

                    if creation_result['status'] == 'created':
                        QMessageBox.information(parent, "成功", f"项目文件夹已成功创建！\n路径: {creation_result['project_path']}")
                    else:
                        QMessageBox.warning(parent, "警告", "项目文件夹创建失败")

            # 只在成功申请LTR编号的情况下（但用户选择不创建项目文件夹）
            elif result.get("success"):
                # 委托给协调器：通知申请已处理但未创建项目
                self.project_creation_coordinator.notify_application_processed_without_project(
                    form_data=form_data,
                    ltr_number=result.get('ltr_number', ''),
                    selected_filename=self.selected_filename,
                    extracted_data=extracted_data
                )

            return result

        except Exception as e:
            logger.error(f"处理LTR编号申请时发生错误: {e}", exc_info=True)
            # 委托给协调器：派发失败事件
            dl_number = form_data.get("dl_number", "")
            self.project_creation_coordinator.dispatch_failure_event(
                dl_number=dl_number,
                error_message=str(e)
            )
            return {"success": False, "error": f"处理申请时发生错误: {str(e)}"}

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

    def set_selected_filename(self, filename: Optional[str]):
        """
        设置选中的申请单文件名

        Args:
            filename: 选中的文件名
        """
        self.selected_filename = filename

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
