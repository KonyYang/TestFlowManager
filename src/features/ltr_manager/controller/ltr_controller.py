"""
LTR控制器模块
处理LTR文件的业务逻辑和事件
"""

from typing import List, Optional
from PyQt5.QtWidgets import QWidget
from src.core.logger import logger
from src.features.ltr_manager.model.ltr_data import LTRData
from src.features.ltr_manager.service.ltr_service import LTRService


class LTRController:
    """
    LTR控制器类
    处理LTR文件的业务逻辑和事件
    """

    def __init__(self):
        """
        初始化LTR控制器
        """
        self.data_model = LTRData()
        self.service = LTRService(self.data_model)

    def handle_view_ltr(self) -> bool:
        """
        处理查看LTR文件事件（包含定位工作表、清除筛选等操作）

        Returns:
            是否成功完成所有操作
        """
        workbook = None
        try:
            logger.debug("Handling advanced view LTR file request")

            # 1. 打开LTR文件（只打开一次）
            workbook = self.service.open_ltr_file_readonly()
            if workbook is None:
                logger.error("Failed to open LTR file")
                return False

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

                # 定位到最后有效行
                last_row = self.service.find_first_blank_cell_from_top(sheet, col_index=4)
                if last_row > 0:
                    logger.info(f"Found last valid row at row {last_row}")
                else:
                    logger.warning("Failed to find last valid row")

            logger.info("Advanced LTR file operations completed")
            return True
        except Exception as e:
            logger.error(f"Failed to handle advanced view LTR request: {e}")
            return False
        finally:
            # 确保工作簿被正确关闭，但不要过早关闭
            # 注意：如果Excel应用程序是可见的，用户可能还需要访问它
            # 在这种情况下，我们不应该自动关闭工作簿
            pass


    def handle_view_dl_number(self, dl_number: str) -> bool:
        """
        处理查看指定DL编号事件

        Args:
            dl_number: 要查找的DL编号

        Returns:
            是否成功找到并定位到DL编号
        """
        workbook = None
        try:
            logger.debug(f"Handling view DL number request: {dl_number}")

            # 1. 验证DL编号格式
            parse_result = self.service.validate_and_parse_dl_number(dl_number)
            if not parse_result["valid"]:
                logger.error(f"Invalid DL number format: {dl_number}")
                return False

            # 2. 打开LTR文件（只打开一次）
            workbook = self.service.open_ltr_file_readonly()
            if workbook is None:
                logger.error("Failed to open LTR file")
                return False

            # 3. 加载可用工作表
            sheets = self.service.load_available_sheets(workbook)
            logger.info(f"Loaded {len(sheets)} available sheets")

            # 4. 根据DL编号确定要查找的工作表
            dl_year = parse_result["year"]
            has_suffix = parse_result["has_suffix"]

            sheets_to_search = self.service.determine_search_sheets(workbook, dl_year, has_suffix)

            # 5. 在确定的工作表中查找DL编号
            found = False
            found_position = None

            for sheet in sheets_to_search:
                if sheet is not None:
                    # 清除筛选和取消隐藏
                    self.service.clear_filters_and_unhide(sheet)

                    # 查找DL编号
                    search_result = self.service.find_dl_number(sheet, dl_number)
                    if search_result["success"]:
                        # 找到了DL编号，定位到该单元格
                        sheet.Activate()
                        target_cell = sheet.Cells(search_result["row"], search_result["column"])
                        target_cell.Select()
                        found = True
                        found_position = {
                            "worksheet": sheet,
                            "row": search_result["row"],
                            "column": search_result["column"]
                        }
                        # 保存找到的位置信息到数据模型
                        self.data_model.set_found_row(search_result["row"])
                        self.data_model.set_found_worksheet(sheet)
                        self.data_model.set_dl_number(dl_number)
                        break

            if found:
                logger.info(f"Successfully found and positioned to DL number: {dl_number} at row {found_position['row']}")
            else:
                logger.warning(f"DL number {dl_number} not found in available sheets")

            return found

        except Exception as e:
            logger.error(f"Failed to handle view DL number request: {e}")
            return False
        finally:
            # 注意：如果Excel应用程序是可见的，用户可能还需要访问它
            # 在这种情况下，我们不应该自动关闭工作簿
            pass



    def get_ltr_file_path(self) -> str:
        """
        获取LTR文件路径

        Returns:
            LTR文件路径
        """
        return self.service.get_ltr_file_path()
