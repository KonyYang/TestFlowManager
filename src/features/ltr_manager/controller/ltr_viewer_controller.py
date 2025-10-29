"""
LTR控制器模块
处理LTR文件的业务逻辑和事件
"""

import os
from typing import List, Optional
from PyQt5.QtWidgets import QWidget
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_viewer_data import LTRViewerData
from src.features.ltr_manager.service.ltr_base_service import LTRBaseService



class LTRViewerController:
    """
    LTR控制器类
    处理LTR文件的业务逻辑和事件
    """

    def __init__(self):
        """
        初始化LTR控制器
        """
        self.data_model = LTRViewerData()
        self.service = LTRBaseService(self.data_model)

    def handle_view_ltr(self) -> bool:
        """
        处理查看LTR文件事件（包含定位工作表、清除筛选等操作）

        Returns:
            是否成功完成所有操作
        """
        workbook = None
        try:
            logger.debug("Handling advanced view LTR file request")

            # 1. 打开LTR文件（只打开一次，隐藏Excel以提高性能）
            workbook = self.service.open_ltr_file(with_password=False)
            if workbook is None:
                logger.error("Failed to open LTR file")
                return False

            # 获取Excel应用程序对象
            excel_app = workbook.Application
            
            # 2. 加载可用工作表
            sheets = self.service.load_available_sheets(workbook)
            logger.info(f"Loaded {len(sheets)} available sheets")

            # 3. 定位到年份工作表
            sheet = self.service.navigate_to_year_sheet(workbook)
            if sheet is None:
                logger.warning("Failed to navigate to year sheet")
                # 即使找不到年份工作表，也继续执行其他操作

            # 4. 如果找到了工作表，则清除筛选和取消隐藏
            if sheet is not None:
                # 清除筛选和取消隐藏
                if self.service.clear_filters_and_unhide(sheet):
                    logger.debug("Successfully cleared filters and unhidden rows/columns")
                else:
                    logger.warning("Failed to clear filters and unhide rows/columns")

                # 定位到最后有效行（D列）
                last_row = self.service.find_first_blank_cell_from_top(sheet, col_index=4)  # D列是第4列
                if last_row > 0:
                    logger.info(f"Found last valid row at row {last_row}")
                    # 将光标定位到D列的最后一个有效行
                    try:
                        sheet.Cells(last_row, 4).Select()  # 选择D列的最后一个有效行
                    except Exception as e:
                        logger.error(f"Failed to select cell at row {last_row}, column 4: {e}")
                else:
                    logger.warning("Failed to find last valid row")

            # 所有操作完成后再显示Excel应用程序
            excel_app.Visible = True
            
            logger.info("Advanced LTR file operations completed")
            return True
        except Exception as e:
            logger.error(f"Failed to handle advanced view LTR request: {e}")
            # 如果出现异常，确保Excel应用程序可见，以便用户可以关闭它
            if workbook and workbook.Application:
                workbook.Application.Visible = True
            return False
        finally:
            # 确保工作簿被正确关闭，但不要过早关闭
            # 注意：如果Excel应用程序是可见的，用户可能还需要访问它
            # 在这种情况下，我们不应该自动关闭工作簿
            pass

    def handle_view_dl_number(self, dl_number: str) -> dict:
        """
        处理查看指定DL编号事件

        Args:
            dl_number: 要查找的DL编号

        Returns:
            包含查找结果和数据的字典:
            - success: 是否成功找到并定位到DL编号
            - data: E到Q列的数据（如果找到）
        """
        workbook = None
        excel_app = None
        try:
            logger.debug(f"Handling view DL number request: {dl_number}")

            # 1. 验证DL编号格式
            parse_result = self.service.validate_and_parse_dl_number(dl_number)
            if not parse_result["valid"]:
                logger.error(f"Invalid DL number format: {dl_number}")
                return {"success": False, "data": None, "error": parse_result["error_message"]}

            # 2. 打开LTR文件（只打开一次）
            workbook = self.service.open_ltr_file(with_password=False)
            if workbook is None:
                logger.error("Failed to open LTR file")
                return {"success": False, "data": None, "error": "无法打开LTR文件"}

            # 获取Excel应用程序对象用于后续操作
            excel_app = workbook.Application
            # 设置为后台操作，不显示Excel界面
            excel_app.Visible = False
            excel_app.ScreenUpdating = False  # 暂时关闭屏幕更新

            # 3. 直接使用已解析的年份和后缀信息查找DL编号
            dl_year = parse_result["year"]
            has_suffix = parse_result["has_suffix"]

            find_result = self.service.find_dl_number_in_workbook(workbook, dl_year, has_suffix, dl_number)

            if find_result["success"]:
                target_worksheet = find_result["worksheet"]
                target_row = find_result["row"]

                # 提取E到Q列的数据
                row_data = self.service.extract_row_data(target_worksheet, target_row)

                # 保存找到的位置信息到数据模型
                self.data_model.set_found_row(target_row)
                self.data_model.set_found_worksheet(target_worksheet)
                self.data_model.set_dl_number(dl_number)

                logger.info(f"Successfully found DL number: {dl_number}")
                return {"success": True, "data": row_data}
            else:
                logger.warning(f"DL number {dl_number} not found in available sheets")
                return {"success": False, "data": None, "error": "未找到指定的DL编号"}

        except Exception as e:
            logger.error(f"Failed to handle view DL number request: {e}")
            return {"success": False, "data": None, "error": str(e)}
        finally:
            # 确保Excel资源被正确关闭，因为我们不需要显示它
            if excel_app:
                excel_app.ScreenUpdating = True  # 恢复屏幕更新

            # 关闭工作簿和Excel应用程序
            if workbook:
                try:
                    workbook.Close(SaveChanges=False)
                except Exception as e:
                    logger.error(f"Failed to close workbook: {e}")

            if excel_app:
                try:
                    excel_app.Quit()
                except Exception as e:
                    logger.error(f"Failed to quit Excel application: {e}")

                # 释放COM对象
                try:
                    from src.utils.excel_utils import release_excel_app
                    release_excel_app()
                except Exception as e:
                    logger.error(f"Failed to release Excel application: {e}")

    def get_ltr_file_path(self) -> str:
        """
        获取LTR文件路径

        Returns:
            LTR文件路径
        """
        return self.service.get_ltr_file_path()
