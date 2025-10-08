# src/features/ltr_manager/service/ltr_base_service.py
"""
LTR基础服务模块
提供LTR相关服务的公共功能
"""
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.core.logger import logger
from src.utils.excel_utils import (
    get_shared_excel_app,
    open_excel_file,
    get_worksheet_names,
    get_sheet_by_name
)
from src.core.config_manager import config_manager
from src.features.ltr_manager.model.ltr_viewer_data import LTRViewerData

class LTRBaseService:
    """
    LTR基础服务类
    提供LTR相关服务的公共功能，如Excel文件操作、DL编号处理等
    """

    def __init__(self, data_model: LTRViewerData = None):
        """初始化LTR基础服务"""
        self.data_model = data_model
        self.ltr_file_path = config_manager.get("paths.ltr_file")

    def open_ltr_file(self, with_password: bool = False):
        """
        打开LTR文件

        Args:
            with_password: 是否使用密码以读写模式打开，默认为False（只读模式）

        Returns:
            工作簿对象，如果打开失败则返回None
        """
        try:
            ltr_file_path = config_manager.get("paths.ltr_file")

            if not ltr_file_path or not os.path.exists(ltr_file_path):
                logger.error(f"LTR文件路径无效: {ltr_file_path}")
                return None

            if with_password:
                ltr_password = config_manager.get("paths.ltr_password")
                print(f"[DEBUG] Password from config: {ltr_password}")
                workbook = open_excel_file(ltr_file_path, read_only=False, password=ltr_password)
                mode = "读写模式"
            else:
                workbook = open_excel_file(ltr_file_path, read_only=True)
                mode = "只读模式"

            if workbook:
                logger.info(f"成功以{mode}打开LTR文件: {ltr_file_path}")
            return workbook

        except Exception as e:
            mode = "读写模式(带密码)" if with_password else "只读模式"
            logger.error(f"以{mode}打开LTR文件时出错: {e}")
            return None


    def validate_and_parse_dl_number(self, dl_number: str) -> Dict[str, Any]:
        """
        验证并解析DL编号

        Args:
            dl_number: DL编号字符串

        Returns:
            包含验证结果和解析信息的字典
        """
        try:
            if not dl_number or not isinstance(dl_number, str):
                return {
                    "valid": False,
                    "error_message": "DL编号不能为空"
                }

            # 移除可能的空格
            dl_number = dl_number.strip()

            # 检查基本格式 (DL-YY-NNNN 或 DL-YY-NNNN-X)
            pattern = r'^DL-(\d{2})-(\d{4,})(?:-([A-Z]))?$'
            match = re.match(pattern, dl_number)

            if not match:
                return {
                    "valid": False,
                    "error_message": "DL编号格式不正确，应为 DL-YY-NNNN 或 DL-YY-NNNN-X"
                }

            year = int(match.group(1))
            number = int(match.group(2))
            suffix = match.group(3)

            # 验证年份范围 (假设为2000-2099)
            if year < 0 or year > 99:
                return {
                    "valid": False,
                    "error_message": "DL编号中的年份部分无效"
                }

            # 验证序号范围
            if number < 1:
                return {
                    "valid": False,
                    "error_message": "DL编号中的序号部分必须大于0"
                }

            return {
                "valid": True,
                "year": year,
                "number": number,
                "suffix": suffix,
                "has_suffix": bool(suffix)
            }

        except Exception as e:
            logger.error(f"验证DL编号时出错: {e}")
            return {
                "valid": False,
                "error_message": f"验证DL编号时发生错误: {str(e)}"
            }

    def load_available_sheets(self, workbook) -> List[str]:
        """
        加载可用的工作表名称

        Args:
            workbook: Excel工作簿对象

        Returns:
            工作表名称列表
        """
        try:
            sheet_names = get_worksheet_names(workbook)
            logger.info(f"成功加载 {len(sheet_names)} 个工作表")
            return sheet_names
        except Exception as e:
            logger.error(f"加载工作表时出错: {e}")
            return []

    def determine_search_sheets(self, workbook, dl_year: int, has_suffix: bool) -> List:
        """
        根据DL编号确定要搜索的工作表

        Args:
            workbook: Excel工作簿对象
            dl_year: DL编号中的年份
            has_suffix: 是否有后缀

        Returns:
            需要搜索的工作表列表
        """
        try:
            sheets_to_search = []

            # 构造年份工作表名称
            year_sheet_name = f"20{dl_year:02d}"

            # 查找年份工作表
            year_sheet = get_sheet_by_name(workbook, year_sheet_name)
            if year_sheet:
                sheets_to_search.append(year_sheet)
            else:
                logger.warning(f"未找到年份工作表: {year_sheet_name}")

            # 如果有后缀，还需要搜索"Special"工作表
            if has_suffix:
                special_sheet = get_sheet_by_name(workbook, "Special")
                if special_sheet:
                    sheets_to_search.append(special_sheet)
                else:
                    logger.warning("未找到Special工作表")

            # 如果没有找到特定工作表，则搜索所有工作表
            if not sheets_to_search:
                sheet_names = get_worksheet_names(workbook)
                for name in sheet_names:
                    sheet = get_sheet_by_name(workbook, name)
                    if sheet:
                        sheets_to_search.append(sheet)
                logger.info("未找到特定工作表，将搜索所有工作表")

            return sheets_to_search

        except Exception as e:
            logger.error(f"确定搜索工作表时出错: {e}")
            return []

    def clear_filters_and_unhide(self, worksheet) -> bool:
        """
        清除工作表的筛选条件并取消隐藏所有行列

        Args:
            worksheet: Excel工作表对象

        Returns:
            是否成功执行操作
        """
        try:
            # 取消隐藏所有行
            worksheet.Rows.Hidden = False

            # 取消隐藏所有列
            worksheet.Columns.Hidden = False

            # 清除筛选
            if worksheet.AutoFilterMode:
                worksheet.AutoFilterMode = False

            logger.debug("成功清除筛选条件并取消隐藏行列")
            return True

        except Exception as e:
            logger.warning(f"清除筛选和取消隐藏时出错: {e}")
            return False

    def find_dl_number(self, worksheet, dl_number: str) -> Dict[str, Any]:
        """
        在工作表中查找指定的DL编号

        Args:
            worksheet: Excel工作表对象
            dl_number: 要查找的DL编号

        Returns:
            包含查找结果的字典
        """
        try:
            # DL编号通常在D列 (第4列)
            dl_column = 4

            # 从第3行开始查找（假设第1-2行为标题）
            start_row = 3

            # 获取工作表的使用范围
            used_range = worksheet.UsedRange
            if not used_range:
                return {"success": False, "error": "工作表为空"}

            last_row = used_range.Rows.Count + used_range.Row - 1

            # 在D列中查找DL编号
            for row in range(start_row, last_row + 1):
                cell_value = worksheet.Cells(row, dl_column).Value
                if cell_value and str(cell_value).strip() == dl_number:
                    logger.info(f"在工作表 {worksheet.Name} 的第 {row} 行找到DL编号: {dl_number}")
                    return {
                        "success": True,
                        "row": row,
                        "worksheet": worksheet
                    }

            logger.info(f"在工作表 {worksheet.Name} 中未找到DL编号: {dl_number}")
            return {"success": False, "error": "未找到指定的DL编号"}

        except Exception as e:
            logger.error(f"查找DL编号时出错: {e}")
            return {"success": False, "error": str(e)}

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
                year = str(datetime.now().year)

            # 先尝试定位当前年份
            sheet = get_sheet_by_name(workbook, year)
            if sheet is not None and self.data_model:
                self.data_model.set_current_sheet(year)
                sheet.Activate()
                return sheet

            # 如果当前年份不存在，尝试定位上一年
            prev_year = str(int(year) - 1)
            sheet = get_sheet_by_name(workbook, prev_year)
            if sheet is not None and self.data_model:
                self.data_model.set_current_sheet(prev_year)
                sheet.Activate()
                return sheet

            logger.warning(f"Neither {year} nor {prev_year} sheet found in LTR file")
            return None
        except Exception as e:
            logger.error(f"Failed to navigate to year sheet: {e}")
            return None

    def find_first_blank_cell_from_top(self, worksheet, col_index: int = 1) -> int:
        """
        从顶部开始查找指定列的第一个空白单元格

        Args:
            worksheet: Excel工作表对象
            col_index: 列索引（从1开始）

        Returns:
            第一个空白单元格的行号，如果出错则返回0
        """
        try:
            # 获取使用范围的最后一行
            used_range = worksheet.UsedRange
            if not used_range:
                return 0

            last_row = used_range.Rows.Count + used_range.Row - 1

            # 从最后一行开始向上查找第一个非空单元格
            for row in range(last_row, 0, -1):
                cell_value = worksheet.Cells(row, col_index).Value
                if cell_value is not None and str(cell_value).strip() != "":
                    return row

            return 0
        except Exception as e:
            logger.error(f"Failed to find first blank cell from top: {e}")
            return 0

    def extract_row_data(self, worksheet, row: int) -> dict:
        """
        提取指定行E到Q列的数据

        Args:
            worksheet: Excel工作表对象
            row: 行号

        Returns:
            包含E到Q列数据的字典
        """
        try:
            data = {}
            # E列到Q列对应索引5到17
            for col_index in range(5, 18):
                cell_value = worksheet.Cells(row, col_index).Value
                # 将列索引转换为列名（E, F, G, ..., Q）
                col_name = chr(ord('A') + col_index - 1)
                data[col_name] = cell_value
            return data
        except Exception as e:
            logger.error(f"Failed to extract row data: {e}")
            return {}

    def get_ltr_file_path(self) -> str:
        """
        获取LTR文件路径

        Returns:
            LTR文件路径
        """
        return self.ltr_file_path
