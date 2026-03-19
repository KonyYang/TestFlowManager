"""
Excel工具模块
提供底层的Excel操作工具函数
"""
import os
from openpyxl import Workbook
from typing import List, Optional, Any
import pythoncom
from src.core.logger import logger

# 共享的Excel应用实例
_shared_excel_app = None
_excel_instance_count = 0
_excel_initialized = False


def get_shared_excel_app():
    """获取共享的Excel应用实例"""
    global _shared_excel_app, _excel_instance_count, _excel_initialized

    if _shared_excel_app is None:
        try:
            # 确保COM库已初始化
            try:
                pythoncom.CoInitialize()
                _excel_initialized = True
            except pythoncom.com_error:
                # 如果已经初始化，则忽略
                pass
            
            import win32com.client
            _shared_excel_app = win32com.client.Dispatch("Excel.Application")
            
            # 等待Excel应用程序完全就绪
            import time
            time.sleep(0.5)
            
            # 安全地设置Excel属性，捕获可能的错误
            try:
                _shared_excel_app.Visible = False
            except:
                # 如果无法设置Visible属性，继续执行
                pass
            
            try:
                _shared_excel_app.DisplayAlerts = False
            except:
                # 如果无法设置DisplayAlerts属性，继续执行
                pass
                
            # 确认Excel应用程序确实可用
            try:
                # 尝试访问一个简单的属性来确认Excel已准备好
                _ = _shared_excel_app.Version
                logger.debug("Created new shared Excel application instance")
            except Exception as e:
                logger.error(f"Excel application not ready: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to initialize Excel application: {e}")
            return None

    _excel_instance_count += 1
    logger.debug(f"Excel instance count increased to {_excel_instance_count}")
    return _shared_excel_app


def release_excel_app():
    """释放Excel应用实例"""
    global _shared_excel_app, _excel_instance_count, _excel_initialized

    _excel_instance_count -= 1
    logger.debug(f"Excel instance count decreased to {_excel_instance_count}")

    if _excel_instance_count <= 0 and _shared_excel_app:
        try:
            # 关闭所有工作簿
            if _shared_excel_app.Workbooks:
                for workbook in _shared_excel_app.Workbooks:
                    try:
                        workbook.Close(SaveChanges=False)
                    except:
                        pass

            # 退出Excel应用
            _shared_excel_app.Quit()
            logger.debug("Excel application quit successfully")
        except Exception as e:
            logger.error(f"Error while quitting Excel application: {e}")
        finally:
            _shared_excel_app = None

        # 反初始化COM
        if _excel_initialized:
            try:
                pythoncom.CoUninitialize()
                _excel_initialized = False
                logger.debug("COM library uninitialized")
            except Exception as e:
                logger.error(f"Error while uninitializing COM library: {e}")

def is_excel_closed(excel_app: Any) -> bool:
    """
    检查Excel应用程序是否已关闭

    Args:
        excel_app: Excel应用程序对象

    Returns:
        如果Excel已关闭返回True，否则返回False
    """
    try:
        # 尝试访问Excel应用程序的一个基本属性
        excel_app.Name
        return False  # 如果成功访问，说明Excel仍在运行
    except:
        return True  # 否则认为Excel已关闭

def close_workbook(workbook: Any, save_changes: bool = False) -> bool:
    """
    关闭Excel工作簿并释放资源

    Args:
        workbook: Excel工作簿对象
        save_changes: 是否保存更改

    Returns:
        是否成功关闭
    """
    try:
        if workbook:
            workbook.Close(SaveChanges=save_changes)
            logger.debug(f"Workbook closed successfully (save_changes={save_changes})")
            return True
    except Exception as e:
        logger.error(f"Failed to close workbook: {e}")
    return False


def open_excel_file(file_path: str, read_only: bool = True, password: Optional[str] = None) -> Any:
    """
    通用打开 Excel 文件函数，使用 Excel COM 接口打开文件

    Args:
        file_path: Excel 文件路径
        read_only: 是否以只读模式打开
        password: 文件密码（可选）

    Returns:
        Excel 工作簿对象，如果打开失败则返回 None
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"Excel file not found: {file_path}")
            return None

        excel_app = get_shared_excel_app()
        if excel_app is None:
            logger.error("Failed to get Excel application instance")
            return None

        # 先隐藏 Excel 应用程序以提高性能
        excel_app.Visible = False
        excel_app.DisplayAlerts = False
        excel_app.EnableEvents = False

        logger.debug(f"准备以只读模式={read_only}打开文件：{file_path}")
        
        # 以指定模式打开文件
        # 关键参数说明：
        # - UpdateLinks: 0 (不更新链接)
        # - ReadOnly: read_only (只读模式)
        # - Format: None (自动检测格式)
        # - WriteResPassword: "" (写入密码)
        # - Password: password (读取密码)
        # - Origin: None (编码类型)
        # - Delimiter: None (分隔符)
        # - AddToMru: False (不添加到最近文件列表)
        # - CorruptLoad: 2 (xlNormalLoad，正常加载)
        wb = excel_app.Workbooks.Open(
            Filename=file_path,
            UpdateLinks=0,
            ReadOnly=read_only,
            Format=None,
            WriteResPassword="",
            Password=password if password else "",
            Origin=None,
            Delimiter=None,
            AddToMru=False,
            CorruptLoad=2  # xlNormalLoad
        )

        logger.debug(f"Successfully opened workbook: {file_path} (read_only={read_only})")
        return wb
    except Exception as e:
        logger.error(f"Failed to open workbook '{file_path}': {e}")
        return None

def save_to_excel(file_path, data):
    """
    将数据保存到Excel文件

    Args:
        file_path: 文件路径
        data: 要保存的数据，二维列表格式

    Returns:
        bool: 保存成功返回True，失败返回False
    """
    try:
        # 创建工作簿
        wb = Workbook()
        ws = wb.active

        # 写入数据
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_value in enumerate(row_data):
                ws.cell(row=row_idx + 1, column=col_idx + 1, value=cell_value)

        # 保存文件
        wb.save(file_path)
        return True
    except Exception as e:
        print(f"保存Excel失败: {e}")
        return False

def get_worksheet_names(workbook: Any) -> List[str]:
    """
    获取工作簿中所有工作表的名称

    Args:
        workbook: Excel工作簿对象

    Returns:
        工作表名称列表
    """
    try:
        sheet_names = []
        for worksheet in workbook.Worksheets:
            sheet_names.append(worksheet.Name)
        logger.debug(f"Retrieved {len(sheet_names)} worksheet names")
        return sheet_names
    except Exception as e:
        logger.error(f"Failed to get worksheet names: {e}")
        return []

def get_sheet_by_name(workbook: Any, sheet_name: str) -> Any:
    """
    根据名称获取工作表

    Args:
        workbook: 工作簿对象
        sheet_name: 工作表名称

    Returns:
        工作表对象
    """
    try:
        # 尝试获取工作表
        sheet = workbook.Worksheets(sheet_name)
        return sheet
    except Exception as e:
        logger.error(f"Failed to get sheet '{sheet_name}': {e}")
        return None

def find_cell(sheet: Any, search_string: str, column: Optional[int] = None,
              look_in: int = -4163, look_at: int = 2) -> Optional[tuple]:
    """
    在工作表中查找指定字符串，返回匹配单元格的位置信息

    Args:
        sheet: Excel工作表对象
        search_string: 要查找的字符串
        column: 限定查找的列号（可选），默认在整个工作表中查找
        look_in: 查找范围 (-4163: xlValues, -4144: xlFormulas)
        look_at: 匹配方式 (1: xlPart部分匹配, 2: xlWhole完全匹配)

    Returns:
        (行号, 列号, 单元格值)的元组，如果未找到则返回None
    """
    try:
        # 确定在哪个范围内查找
        search_range = sheet.Columns(column) if column else sheet.Cells

        # 使用Find方法查找字符串
        found_cell = search_range.Find(
            What=search_string,
            LookIn=look_in,
            LookAt=look_at,
            SearchDirection=1  # xlNext
        )

        if found_cell is not None:
            row = found_cell.Row
            col = found_cell.Column
            value = found_cell.Value
            return (row, col, value)
        else:
            return None

    except Exception as e:
        logger.error(f"Failed to search string '{search_string}' in sheet: {e}")
        return None