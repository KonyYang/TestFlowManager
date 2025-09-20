"""
LTR服务模块
提供LTR文件操作相关的服务功能
"""

import os
import platform
from typing import Optional, List, Any
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.features.ltr_manager.model.ltr_viewer_data import LTRViewerData
# 导入Excel工具函数
from src.utils.excel_utils import get_sheet_by_name, open_excel_file, get_worksheet_names, is_excel_closed


class LTRViewerService:
    """
    LTR服务类
    提供LTR文件操作相关的服务功能
    """

    def __init__(self, data_model: LTRViewerData):
        """
        初始化LTR服务

        Args:
            data_model: LTR数据模型实例
        """
        self.data_model = data_model
        # 从配置文件获取LTR文件路径
        ltr_file_path = config_manager.get("paths.fileltr", "D:\\Source\\Office Auto\\TestDocument\\LTR_number.xls")
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

    def open_ltr_file_with_password(self) -> bool:
        """
        使用密码打开LTR文件

        Returns:
            是否成功打开文件
        """
        try:
            file_path = self.data_model.get_file_path()
            # 从配置中获取密码，默认为"DGLAB"
            password = config_manager.get("paths.LTRPassword", "DGLAB")  # 使用原始大小写键名

            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"LTR file not found: {file_path}")
                return False

            # 使用通用Excel文件打开函数，带密码参数，以读写模式打开
            success = open_excel_file(file_path, read_only=False, password=password)

            if success:
                logger.info(f"Successfully opened LTR file with password: {file_path}")
            else:
                logger.error(f"Failed to open LTR file with password: {file_path}")

            return success
        except Exception as e:
            logger.error(f"Failed to open LTR file with password: {e}")
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

    def validate_and_parse_dl_number(self, dl_number: str) -> dict:
        """
        验证并解析DL编号

        Args:
            dl_number: 要验证和解析的DL编号

        Returns:
            包含解析结果的字典:
            - valid: 是否有效
            - year: 年份部分
            - has_suffix: 是否有后缀
            - error_message: 错误信息（如果无效）
        """
        import re
        from datetime import datetime

        # 验证基本格式 DL-XXXX-YY-ZZZ[后缀]
        match = re.match(r"DL-(\d{4})-(\d{2})-(\d{3})(.*)", dl_number)
        if not match:
            return {
                "valid": False,
                "year": None,
                "has_suffix": None,
                "error_message": "DL编号格式不正确，应为 DL-XXXX-YY-ZZZ[后缀] 格式"
            }

        year = int(match.group(1))
        suffix = match.group(4)

        # 验证年份合理性
        current_year = datetime.now().year
        if year < 2000 or year > current_year + 1:
            return {
                "valid": False,
                "year": year,
                "has_suffix": bool(suffix),
                "error_message": f"年份 {year} 不在合理范围内"
            }

        return {
            "valid": True,
            "year": year,
            "has_suffix": bool(suffix),
            "error_message": None
        }

    def determine_search_sheets(self, workbook, dl_year: int, has_suffix: bool) -> list:
        """
        根据DL编号的年份和后缀信息确定要搜索的工作表

        Args:
            workbook: Excel工作簿对象
            dl_year: DL编号中的年份
            has_suffix: 是否有后缀

        Returns:
            要搜索的工作表列表
        """
        from datetime import datetime

        sheets_to_search = []
        current_year = datetime.now().year
        available_sheets = [ws.Name for ws in workbook.Sheets if ws.Name.isdigit()]

        # 如果没有后缀，只查找对应年份的工作表
        if not has_suffix:
            sheet_name = str(dl_year)
            if sheet_name in available_sheets:
                sheets_to_search.append(workbook.Sheets(sheet_name))
        else:
            # 有后缀的情况下
            sheet_name = str(dl_year)
            if sheet_name in available_sheets:
                sheets_to_search.append(workbook.Sheets(sheet_name))

            # 如果年份不是当前年份，还要查找下一年的工作表
            if dl_year != current_year:
                next_year_sheet_name = str(dl_year + 1)
                if next_year_sheet_name in available_sheets:
                    sheets_to_search.append(workbook.Sheets(next_year_sheet_name))

        # 如果没有找到特定年份的工作表，查找最近两年的工作表
        if not sheets_to_search:
            for year in [current_year, current_year - 1]:
                sheet_name = str(year)
                if sheet_name in available_sheets:
                    sheets_to_search.append(workbook.Sheets(sheet_name))

        return sheets_to_search

    def find_dl_number(self, worksheet, dl_number: str) -> dict:
        """
        在指定工作表中查找DL编号

        Args:
            worksheet: 要查找的工作表
            dl_number: 要查找的DL编号

        Returns:
            包含查找结果的字典:
            - success: 是否成功找到
            - row: 找到的行号
            - column: 找到的列号（通常是4，即D列）
        """
        try:
            # 使用更高效的方式查找DL编号
            # 先尝试使用Excel内置的查找功能
            from src.utils.excel_utils import find_cell

            try:
                # 使用通用的find_cell函数在D列(第4列)中查找DL编号
                result = find_cell(worksheet, dl_number, column=4)

                if result:
                    row, column, value = result
                    return self._set_found_result(worksheet, dl_number, row, column)
            except Exception as e:
                logger.debug(f"Excel Find method failed, falling back to manual search: {e}")

            # 如果内置查找失败，则使用原来的逐行查找方法
            row = 2  # 从第2行开始（跳过标题行）
            while row < 10000:  # 设置上限防止死循环
                cell_value = worksheet.Cells(row, 4).Value  # D列
                if cell_value is None:
                    # 检查是否已经超出数据范围
                    if worksheet.Cells(row + 5, 4).Value is None:  # 连续5行为空则认为到达末尾
                        break
                elif str(cell_value).strip() == dl_number:
                    # 找到了DL编号
                    return self._set_found_result(worksheet, dl_number, row, 4)
                row += 1

            # 未找到DL编号
            return {
                "success": False,
                "row": None,
                "column": None
            }

        except Exception as e:
            logger.error(f"查找DL编号时发生错误: {e}")
            return {
                "success": False,
                "row": None,
                "column": None
            }

    def _set_found_result(self, worksheet, dl_number: str, row: int, column: int) -> dict:
        """
        设置查找成功的结果

        Args:
            worksheet: 工作表对象
            dl_number: 找到的DL编号
            row: 行号
            column: 列号

        Returns:
            包含查找结果的字典
        """
        # 保存找到的位置信息到数据模型
        self.data_model.set_found_row(row)
        self.data_model.set_found_worksheet(worksheet)
        self.data_model.set_dl_number(dl_number)

        return {
            "success": True,
            "row": row,
            "column": column
        }


    def extract_row_data(self, worksheet, row_number: int) -> dict:
        """
        提取指定行的E到Q列数据

        Args:
            worksheet: Excel工作表对象
            row_number: 行号

        Returns:
            包含E到Q列数据的字典
        """
        try:
            # E列到Q列对应索引为5到17
            data = {}
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

            for i, field_name in enumerate(field_names):
                column_index = 5 + i  # E列索引为5
                cell_value = worksheet.Cells(row_number, column_index).Value
                data[field_name] = cell_value if cell_value is not None else ""

            return data
        except Exception as e:
            logger.error(f"Failed to extract row data: {e}")
            # 返回默认空数据
            return {field: "" for field in field_names}
