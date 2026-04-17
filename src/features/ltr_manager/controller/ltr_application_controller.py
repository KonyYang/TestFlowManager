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
from src.features.folder_manager.controller.folder_manager_controller import FolderManagerController
from src.utils.ltr_data_manager import LTRDataManager
# 添加事件调度器
from src.core.event_dispatcher import event_dispatcher, EventTopics


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
        # 添加文件夹管理控制器
        self.folder_manager = FolderManagerController(parent_view)
        # 添加LTR数据管理器
        self.ltr_data_manager = LTRDataManager()
        # 添加事件订阅
        event_dispatcher.subscribe(EventTopics.LTR_APPLICATION_PROCESSED, self._on_ltr_application_processed)
        # 添加属性来存储选中的文件名
        self.selected_filename = None


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

            # 获取从Word文档提取的完整数据（如果存在的话）
            # 如果application_data是从Word文档处理得到的，它应该包含原始的提取数据
            extracted_word_data = None
            if hasattr(self.application_data, 'file_path') and self.application_data.file_path:
                # 如果有文件路径，重新处理一次以获取完整的提取数据
                try:
                    # 使用extractor提取完整的数据
                    from src.features.ltr_manager.service.application_processing.data_extractor import LTRApplicationDataExtractor
                    extractor = LTRApplicationDataExtractor()
                    extracted_word_data = extractor.extract_application_data(self.application_data.file_path)
                    logger.debug(f"从Word文档重新提取的数据: {extracted_word_data}")
                except Exception as e:
                    logger.warning(f"重新提取Word文档数据失败: {e}")
                    # 如果重新提取失败，使用当前application_data中的数据
                    extracted_word_data = self.application_data.to_dict()

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
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    parent,
                    "创建项目文件夹",
                    f"LTR编号 {result['ltr_number']} 申请成功。\n\n是否创建以此编号为名的项目文件夹并保存申请数据？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    # 收集完整的申请数据，包括DL编号和选中的文件名
                    application_data = self.ltr_data_manager.collect_application_data(
                        form_data, 
                        result['ltr_number'],
                        self.selected_filename  # 传递选中的文件名
                    )
                    
                    # 如果有从Word文档提取的完整数据，合并到application_data中
                    if extracted_data:
                        # 保留从UI获取的数据，同时添加从Word文档提取的详细信息
                        for key, value in extracted_data.items():
                            # 只有当application_data中没有该字段或字段为空时才使用提取的数据
                            if key not in application_data or not application_data[key]:
                                application_data[key] = value
                        logger.debug(f"已合并从Word文档提取的数据")
                    
                    logger.debug(f"收集到的申请数据: {application_data}")
                    
                    # 检查申请数据中的file_path
                    logger.debug(f"申请数据中的file_path: {application_data.get('file_path', 'None')}")
                    logger.debug(f"传入的临时文件夹路径: {temp_folder_path}")
                    
                    # 如果提供了临时文件夹路径，添加到申请数据中
                    if temp_folder_path:
                        application_data['file_path'] = temp_folder_path
                        logger.debug(f"已将临时文件夹路径添加到申请数据中: {temp_folder_path}")
                    else:
                        logger.warning("未提供临时文件夹路径")
                        # 检查申请数据中是否已经有file_path
                        if 'file_path' in application_data and application_data['file_path']:
                            logger.debug(f"使用申请数据中已有的file_path: {application_data['file_path']}")
                        else:
                            logger.warning("申请数据中也没有有效的file_path")
                    
                    # 使用完整项目结构创建方法
                    project_result = self.folder_manager.create_complete_project_structure(application_data)
                    if project_result:
                        # 保存申请数据
                        self.ltr_data_manager.save_to_project_file(result['ltr_number'], application_data)
                        logger.info(f"完整项目结构创建成功: {project_result}")
                        QMessageBox.information(parent, "成功", f"项目文件夹已成功创建！\n路径: {project_result}")
                        
                        # 只有在有有效的LTR编号时才发布事件
                        if result.get('ltr_number') and result['ltr_number'].strip():
                            # 发布事件通知项目创建成功，携带项目路径信息
                            event_dispatcher.dispatch(EventTopics.LTR_APPLICATION_PROCESSED, {
                                "dl_number": result['ltr_number'],
                                "status": "success",
                                "project_path": project_result,  # 添加项目路径
                                "application_data": application_data
                            })
                        else:
                            logger.warning("LTR number is empty, not dispatching success event")
                    else:
                        logger.error("完整项目结构创建失败")
                        QMessageBox.warning(parent, "警告", "项目文件夹创建失败")
                        
                        # 只有在有有效的LTR编号时才发布事件
                        if result.get('ltr_number') and result['ltr_number'].strip():
                            # 发布事件通知项目创建失败
                            event_dispatcher.dispatch(EventTopics.LTR_APPLICATION_PROCESSED, {
                                "dl_number": result['ltr_number'],
                                "status": "failed",
                                "error": "项目文件夹创建失败",
                                "project_path": None  # 添加project_path字段
                            })
                        else:
                            logger.warning("LTR number is empty, not dispatching failure event")
            # 只在成功申请LTR编号的情况下返回成功结果
            elif result.get("success"):
                # 创建完整的application_data用于事件通知
                application_data = self.ltr_data_manager.collect_application_data(
                    form_data, 
                    result.get('ltr_number', ''),
                    self.selected_filename
                )
                
                # 如果有从Word文档提取的完整数据，合并到application_data中
                if extracted_data:
                    for key, value in extracted_data.items():
                        if key not in application_data or not application_data[key]:
                            application_data[key] = value
                    
                # LTR编号申请成功但用户选择不创建项目文件夹
                # 仍然需要发布事件通知其他组件
                event_dispatcher.dispatch(EventTopics.LTR_APPLICATION_PROCESSED, {
                    "dl_number": result.get('ltr_number', ''),
                    "status": "success",
                    "application_data": application_data,
                    "project_path": None  # 添加project_path字段，即使为None
                })
                
            return result

        except Exception as e:
            import traceback
            logger.error(f"处理LTR编号申请时发生错误: {e}", exc_info=True)
            # 只有在有有效的DL编号时才发布事件
            dl_number = form_data.get("dl_number", "")
            if dl_number and dl_number.strip():
                # 发布事件通知项目创建失败
                event_dispatcher.dispatch(EventTopics.LTR_APPLICATION_PROCESSED, {
                    "dl_number": dl_number,
                    "status": "failed",
                    "error": str(e),
                    "project_path": None  # 添加project_path字段
                })
            else:
                logger.warning("DL number is empty, not dispatching error event")
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