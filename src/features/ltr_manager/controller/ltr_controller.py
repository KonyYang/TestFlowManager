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


    def get_ltr_file_path(self) -> str:
        """
        获取LTR文件路径

        Returns:
            LTR文件路径
        """
        return self.service.get_ltr_file_path()
