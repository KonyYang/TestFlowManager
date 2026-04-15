"""
LTR编辑器控制器模块
处理LTR编辑器的业务逻辑和事件
"""

from typing import Dict, Any, TYPE_CHECKING
from PyQt5.QtWidgets import QDialog
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_editor_data import LTREditorData
from src.features.ltr_manager.service.ltr_editor_service import LTREditorService
from src.features.ltr_manager.model.ltr_viewer_data import LTRViewerData

if TYPE_CHECKING:
    from src.features.ltr_manager.view.ltr_editor_dialog import LTREditorDialog


class LTREditorController:
    """
    LTR编辑器控制器类
    处理LTR编辑器的业务逻辑和事件
    """

    def __init__(self, ltr_data_model: LTRViewerData, ltr_service):
        """
        初始化LTR编辑器控制器

        Args:
            ltr_data_model: LTR数据模型实例
            ltr_service: LTR服务实例
        """
        self.editor_data_model = LTREditorData()
        self.ltr_data_model = ltr_data_model
        self.service = LTREditorService(self.editor_data_model, self.ltr_data_model)

    def open_editor_dialog(self, dl_data: Dict[str, Any], parent=None) -> Dict[str, Any]:
        """
        打开LTR编辑器对话框

        Args:
            dl_data: 包含DL编号和相关数据的字典
            parent: 父窗口

        Returns:
            包含操作结果和修改后数据的字典
        """
        # 延迟导入避免循环依赖
        from src.features.ltr_manager.view.ltr_editor_dialog import LTREditorDialog

        # 初始化数据模型
        dl_number = dl_data.get('dl_number', '')
        original_data = dl_data.get('data', {})

        self.editor_data_model.set_dl_number(dl_number)
        self.editor_data_model.set_original_data(original_data)

        # 创建回调函数，用于对话框内的更新操作
        def update_callback(dlnum: str, modified: Dict[str, Any]) -> bool:
            """对话框内更新的回调函数"""
            return self.update_ltr_data(dlnum, modified, parent)

        # 创建并显示对话框
        dialog = LTREditorDialog(dl_data, parent, update_callback=update_callback)
        logger.debug("显示 LTR 编辑对话框...")
        result = dialog.exec_()
        logger.debug(f"对话框返回结果: {result}")

        if result == QDialog.Accepted:
            logger.debug("用户确认了对话框")
            # 获取修改后的数据
            modified_data = dialog.get_modified_data()
            logger.debug(f"获取到的修改数据: {modified_data}")

            # 更新数据模型
            self.editor_data_model.set_modified_data(modified_data)

            # 返回成功结果和修改后的数据
            return_value = {
                "success": True,
                "dl_number": dl_number,
                "modified_data": modified_data
            }
            logger.debug(f"返回成功结果: {return_value}")
            return return_value
        else:
            logger.debug("用户取消了对话框")
            # 用户取消操作
            return_value = {
                "success": False,
                "dl_number": None,
                "modified_data": None
            }
            logger.debug(f"返回取消结果: {return_value}")
            return return_value

    def update_ltr_data(self, dl_number: str, modified_data: Dict[str, Any] = None, parent=None) -> bool:
        """
        更新LTR数据

        Args:
            dl_number: DL编号
            modified_data: 修改后的数据，如果为None则使用数据模型中的数据
            parent: 父窗口，用于显示消息框

        Returns:
            是否成功更新数据
        """
        try:
            # 如果没有提供修改后的数据，则使用数据模型中的数据
            if modified_data is None:
                modified_data = self.editor_data_model.get_modified_data()

            # 验证数据
            validation_result = self.service.validate_data(modified_data)
            if not validation_result["valid"]:
                logger.error(f"数据验证失败: {validation_result['errors']}")
                return False

            # 更新数据到Excel
            success = self.service.update_ltr_data(dl_number, modified_data, parent)

            if success:
                logger.info(f"成功更新DL编号 {dl_number} 的数据")
            else:
                logger.error(f"更新DL编号 {dl_number} 的数据失败")

            return success
        except Exception as e:
            logger.error(f"更新LTR数据时发生异常: {e}")
            return False

    def open_editor_and_update(self, dl_data: Dict[str, Any], parent=None) -> bool:
        """
        打开LTR编辑器对话框并更新数据

        Args:
            dl_data: 包含DL编号和相关数据的字典
            parent: 父窗口

        Returns:
            是否成功更新数据
        """
        # 打开编辑器对话框
        editor_result = self.open_editor_dialog(dl_data, parent)

        if editor_result["success"]:
            # 用户点击了更新按钮，获取修改后的数据并更新到Excel
            dl_number = editor_result["dl_number"]
            modified_data = editor_result["modified_data"]
            return self.update_ltr_data(dl_number, modified_data, parent)
        else:
            # 用户取消操作
            return False

    def get_attachments(self):
        """
        获取附件列表

        Returns:
            附件列表
        """
        email_data = self.data_model.get_email_data()
        return email_data.get("attachments", [])
