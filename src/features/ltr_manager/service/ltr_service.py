"""
LTR服务模块
提供LTR文件操作相关的服务功能
"""

import os
import platform
from typing import Optional, List, Any
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.features.ltr_manager.model.ltr_data import LTRData
# 导入Excel工具函数
from src.utils.excel_utils import get_sheet_by_name, open_excel_file, get_worksheet_names, is_excel_closed


class LTRService:
    """
    LTR服务类
    提供LTR文件操作相关的服务功能
    """

    def __init__(self, data_model: LTRData):
        """
        初始化LTR服务

        Args:
            data_model: LTR数据模型实例
        """
        self.data_model = data_model
        # 从配置文件获取LTR文件路径
        ltr_file_path = config_manager.get("ltr.file_path", "D:\\Source\\Office Auto\\TestDocument\\LTR_number.xls")
        self.data_model.set_file_path(ltr_file_path)

    def open_ltr_file_readonly(self) -> bool:
        """
        以只读模式打开LTR文件

        Returns:
            是否成功打开文件
        """
        try:
            file_path = self.data_model.get_file_path()

            # 使用通用Excel文件打开函数
            success = open_excel_file(file_path, read_only=True)

            if success:
                logger.info(f"Successfully opened LTR file in read-only mode: {file_path}")
            else:
                logger.error(f"Failed to open LTR file in read-only mode: {file_path}")

            return success
        except Exception as e:
            logger.error(f"Failed to open LTR file in read-only mode: {e}")
            return False

    def get_ltr_file_path(self) -> str:
        """
        获取LTR文件路径

        Returns:
            LTR文件的完整路径
        """
        return self.data_model.get_file_path()

    def navigate_to_year_sheet(self, workbook: Any, year: Optional[str] = None) -> Any:
        """
        定位到指定年份的工作表

        Args:
            workbook: Excel工作簿对象
            year: 年份（如"2025"），如果为None则使用当前年份

        Returns:
            工作表对象，如果失败则返回None
        """
        try:
            if year is None:
                import datetime
                year = str(datetime.datetime.now().year)

            # 先尝试定位当前年份
            sheet = get_sheet_by_name(workbook, year)
            if sheet is not None:
                self.data_model.set_current_sheet(year)
                sheet.Activate()
                return sheet

            # 如果当前年份不存在，尝试定位上一年
            prev_year = str(int(year) - 1)
            sheet = get_sheet_by_name(workbook, prev_year)
            if sheet is not None:
                self.data_model.set_current_sheet(prev_year)
                sheet.Activate()
                return sheet

            logger.warning(f"Neither {year} nor {prev_year} sheet found in LTR file")
            return None
        except Exception as e:
            logger.error(f"Failed to navigate to year sheet: {e}")
            return None

    def clear_filters_and_unhide(self, sheet: Any) -> bool:
        """
        清除数据筛选和取消隐藏行/列 (LTR特有功能)

        Args:
            sheet: Excel工作表对象

        Returns:
            是否成功清除筛选和取消隐藏
        """
        logger.debug("unhide_and_clear_filters(ws) - 开始执行")
        try:
            # 清除自动筛选
            if sheet.AutoFilterMode:
                logger.debug("  [ACTION] 正在清除筛选器...")
                sheet.AutoFilterMode = False
            else:
                logger.debug("  [INFO] 当前工作表无筛选器")

            # 取消隐藏所有行
            logger.debug("  [ACTION] 取消隐藏所有行...")
            sheet.Rows.EntireRow.Hidden = False

            # 取消隐藏所有列
            logger.debug("  [ACTION] 取消隐藏所有列...")
            sheet.Columns.EntireColumn.Hidden = False

            logger.debug("unhide_and_clear_filters(ws) - ✅ 成功完成")
            return True
        except Exception as e:
            logger.error(f"unhide_and_clear_filters 执行失败: {e}")
            return False


    def find_first_blank_cell_from_top(self, sheet: Any, col_index: int, max_empty_rows: int = 5):
        """
        从上往下查找第一个空白单元格（连续多个空白则认为是结束位置）
        :param sheet: Excel 工作表对象
        :param col_index: 列索引（从1开始）
        :param max_empty_rows: 连续多少个空行为"结束"
        :return: 第一个空白单元格的行号 (row_number)
        """
        try:
            # 获取工作簿所属 Excel 应用
            excel_app = sheet.Parent
            if is_excel_closed(excel_app):
                logger.info("Excel 已关闭，跳过查找操作")
                return -1

            start_row = 1
            empty_count = 0

            while True:
                cell_value = sheet.Cells(start_row, col_index).Value
                if cell_value in (None, "", "None"):
                    empty_count += 1
                    if empty_count >= max_empty_rows:
                        row_number = start_row - max_empty_rows + 1
                        logger.info(f"在第 {row_number} 行发现连续 {max_empty_rows} 行为空")
                        return row_number
                else:
                    empty_count = 0

                # 设置上限防止死循环
                if start_row > 10000:
                    logger.info("达到最大查找行数(10000)，未发现空白单元格")
                    return -1

                start_row += 1

        except Exception as e:
            logger.error(f"查找空白单元格失败: {e}")
            return -1



    def load_available_sheets(self, workbook: Any) -> List[str]:
        """
        加载Excel文件中所有工作表名称

        Args:
            workbook: Excel工作簿对象

        Returns:
            工作表名称列表
        """
        try:
            # 使用工具函数获取工作表列表
            sheets = get_worksheet_names(workbook)

            # 记录工作表列表到数据模型
            self.data_model.set_available_sheets(sheets)

            logger.debug(f"Loaded {len(sheets)} available sheets: {sheets}")
            return sheets
        except Exception as e:
            logger.error(f"Failed to load available sheets: {e}")
            return []
