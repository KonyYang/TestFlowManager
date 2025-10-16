# src/features/ltr_manager/service/ltr_editor_service.py
"""
LTR编辑器服务模块
提供LTR编辑器相关的服务功能
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QMessageBox
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_editor_data import LTREditorData
from src.features.ltr_manager.model.ltr_viewer_data import LTRViewerData
from src.features.ltr_manager.service.ltr_base_service import LTRBaseService


class LTREditorService(LTRBaseService):
    """
    LTR编辑器服务类
    提供LTR编辑器相关的服务功能
    """

    def __init__(self, editor_data_model: LTREditorData, ltr_data_model: LTRViewerData):
        """
        初始化LTR编辑器服务

        Args:
            editor_data_model: LTR编辑器数据模型实例
            ltr_data_model: LTR数据模型实例
        """
        super().__init__()
        self.editor_data_model = editor_data_model
        self.ltr_data_model = ltr_data_model

    def update_ltr_data(self, dl_number: str, modified_data: Dict[str, Any], parent=None) -> bool:
        """
        更新LTR数据到Excel工作表

        Args:
            dl_number: DL编号
            modified_data: 修改后的数据
            parent: 父窗口，用于显示消息框

        Returns:
            是否成功更新数据
        """
        workbook = None
        excel_app = None
        try:
            # 1. 验证并解析DL编号
            parse_result = self.validate_and_parse_dl_number(dl_number)
            if not parse_result["valid"]:
                logger.error(f"无效的DL编号格式: {dl_number}")
                if parent:
                    QMessageBox.warning(parent, "更新失败", f"DL编号格式无效: {dl_number}")
                return False

            # 2. 使用密码打开LTR文件（读写模式）
            workbook = self.open_ltr_file(with_password=True)
            if workbook is None:
                logger.error("无法以读写模式打开LTR文件")
                if parent:
                    QMessageBox.warning(parent, "更新失败", "无法打开LTR文件，请检查密码设置是否正确。")
                return False

            # 获取Excel应用程序对象
            excel_app = workbook.Application
            # 设置为后台操作，不显示Excel界面
            excel_app.Visible = False
            excel_app.ScreenUpdating = False  # 暂时关闭屏幕更新

            # 3. 直接使用已解析的年份和后缀信息查找DL编号
            dl_year = parse_result["year"]
            has_suffix = parse_result["has_suffix"]

            find_result = self.find_dl_number_in_workbook(workbook, dl_year, has_suffix, dl_number)

            if not find_result["success"]:
                logger.error(f"在工作表中未找到DL编号: {dl_number}")
                if parent:
                    QMessageBox.warning(parent, "更新失败", f"未找到DL编号: {dl_number}")
                return False

            target_worksheet = find_result["worksheet"]
            target_row = find_result["row"]

            # 4. 准备数据列用于更新
            data_columns = [
                modified_data.get('project_type', ''),
                modified_data.get('sample_information', ''),
                modified_data.get('tests_to_be_performed', ''),
                modified_data.get('test_type', ''),
                modified_data.get('requested_by', ''),
                modified_data.get('location', ''),
                modified_data.get('project_leader', ''),
                modified_data.get('test_result', ''),
                modified_data.get('failed_item', ''),
                modified_data.get('sample_deposition', ''),
                modified_data.get('sub_contract', ''),
                modified_data.get('test_fee', ''),
                modified_data.get('remarks_po', '')
            ]

            # 5. 使用基类的通用更新方法更新数据
            if not self.update_worksheet_data(target_worksheet, target_row, data_columns, parent):
                return False

            # 6. 保存工作簿
            workbook.Save()
            logger.info(f"成功更新DL编号 {dl_number} 的数据")

            # 7. 显示成功消息
            if parent:
                QMessageBox.information(parent, "更新成功", f"DL编号 {dl_number} 的数据已成功更新。")
            return True

        except Exception as e:
            logger.error(f"更新LTR数据失败: {e}")
            if parent:
                QMessageBox.critical(parent, "更新失败", f"更新数据时发生错误: {str(e)}")
            return False
        finally:
            # 恢复屏幕更新
            if excel_app:
                excel_app.ScreenUpdating = True

            # 确保工作簿被正确关闭
            if workbook:
                try:
                    workbook.Close(SaveChanges=False)
                except Exception as e:
                    logger.error(f"关闭工作簿时发生错误: {e}")

                # 释放Excel应用程序
                try:
                    from src.utils.excel_utils import release_excel_app
                    release_excel_app()
                except Exception as e:
                    logger.error(f"释放Excel应用程序时发生错误: {e}")

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证数据的有效性

        Args:
            data: 要验证的数据

        Returns:
            验证结果字典，包含是否有效和错误信息
        """
        # 这里可以添加数据验证逻辑
        # 目前只是简单返回验证通过
        return {
            "valid": True,
            "errors": {}
        }
