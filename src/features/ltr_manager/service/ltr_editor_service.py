"""
LTR编辑器服务模块
提供LTR编辑器相关的服务功能
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QMessageBox
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_editor_data import LTREditorData
from src.features.ltr_manager.model.ltr_viewer_data import LTRViewerData
from src.features.ltr_manager.service.ltr_viewer_service import LTRViewerService


class LTREditorService:
    """
    LTR编辑器服务类
    提供LTR编辑器相关的服务功能
    """

    def __init__(self, editor_data_model: LTREditorData, ltr_data_model: LTRViewerData, ltr_service: LTRViewerService):
        """
        初始化LTR编辑器服务

        Args:
            editor_data_model: LTR编辑器数据模型实例
            ltr_data_model: LTR数据模型实例
            ltr_service: LTR服务实例
        """
        self.editor_data_model = editor_data_model
        self.ltr_data_model = ltr_data_model
        self.ltr_service = ltr_service

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
            # 1. 使用密码打开LTR文件（读写模式）
            workbook = self.ltr_service.open_ltr_file_with_password()
            if workbook is None:
                logger.error("无法以读写模式打开LTR文件")
                QMessageBox.warning(parent, "更新失败", "无法打开LTR文件，请检查密码设置是否正确。")
                return False

            # 获取Excel应用程序对象
            excel_app = workbook.Application
            # 设置为后台操作，不显示Excel界面
            excel_app.Visible = False
            excel_app.ScreenUpdating = False  # 暂时关闭屏幕更新

            # 2. 验证并解析DL编号
            parse_result = self.ltr_service.validate_and_parse_dl_number(dl_number)
            if not parse_result["valid"]:
                logger.error(f"无效的DL编号格式: {dl_number}")
                QMessageBox.warning(parent, "更新失败", f"DL编号格式无效: {dl_number}")
                return False

            # 3. 加载可用工作表
            sheets = self.ltr_service.load_available_sheets(workbook)
            logger.info(f"加载了 {len(sheets)} 个工作表")

            # 4. 根据DL编号确定要搜索的工作表
            dl_year = parse_result["year"]
            has_suffix = parse_result["has_suffix"]
            sheets_to_search = self.ltr_service.determine_search_sheets(workbook, dl_year, has_suffix)

            # 5. 在确定的工作表中查找DL编号
            found = False
            target_worksheet = None
            target_row = None

            for sheet in sheets_to_search:
                if sheet is not None:
                    # 清除筛选和取消隐藏
                    self.ltr_service.clear_filters_and_unhide(sheet)

                    # 查找DL编号
                    search_result = self.ltr_service.find_dl_number(sheet, dl_number)
                    if search_result["success"]:
                        found = True
                        target_worksheet = sheet
                        target_row = search_result["row"]
                        break

            if not found:
                logger.error(f"在工作表中未找到DL编号: {dl_number}")
                QMessageBox.warning(parent, "更新失败", f"未找到DL编号: {dl_number}")
                return False

            # 6. 更新每个字段的值 (E列到Q列对应索引为5到17)
            field_names = [
                'project_type',                # E列
                'sample_information',          # F列
                'tests_to_be_performed',       # G列
                'test_type',                   # H列
                'requested_by',                # I列
                'location',                    # J列
                'project_leader',              # K列
                'test_result',                 # L列
                'failed_item',                 # M列
                'sample_deposition',           # N列
                'sub_contract',                # O列
                'test_fee',                    # P列
                'remarks_po'                   # Q列
            ]

            # 更新每个字段的值
            for i, field_name in enumerate(field_names):
                column_index = 5 + i  # E列索引为5
                value = modified_data.get(field_name, "")
                target_worksheet.Cells(target_row, column_index).Value = value

            # 7. 保存工作簿
            workbook.Save()
            logger.info(f"成功更新DL编号 {dl_number} 的数据")

            # 8. 显示成功消息
            QMessageBox.information(parent, "更新成功", f"DL编号 {dl_number} 的数据已成功更新。")
            return True

        except Exception as e:
            logger.error(f"更新LTR数据失败: {e}")
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
                    release_excel_app(excel_app)
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
