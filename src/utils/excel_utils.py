"""
Excel工具模块
提供底层的Excel操作工具函数
"""

from typing import List, Optional, Any
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
            import pythoncom
            if not _excel_initialized:
                pythoncom.CoInitialize()
                _excel_initialized = True
            import win32com.client
            _shared_excel_app = win32com.client.Dispatch("Excel.Application")
            _shared_excel_app.Visible = False
            _shared_excel_app.DisplayAlerts = False
            logger.debug("Created new shared Excel application instance")
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
                import pythoncom
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
    通用打开Excel文件函数，使用Excel COM接口打开文件

    Args:
        file_path: Excel文件路径
        read_only: 是否以只读模式打开
        password: 文件密码（可选）

    Returns:
        Excel工作簿对象，如果打开失败则返回None
    """
    try:
        # 检查文件是否存在
        import os
        if not os.path.exists(file_path):
            logger.error(f"Excel file not found: {file_path}")
            return None

        excel_app = get_shared_excel_app()
        if excel_app is None:
            logger.error("Failed to get Excel application instance")
            return None

        excel_app.Visible = True
        excel_app.DisplayAlerts = False
        excel_app.EnableEvents = False

        # 以只读模式打开文件
        wb = excel_app.Workbooks.Open(
            file_path,
            0,  # 更新链接选项（0表示不更新）
            read_only,  # 只读模式
            None,  # 格式参数
            password or "",  # 密码（打开密码）
            "",  # 写入密码
            False,  # 是否将文件添加到最近文件列表
            None,  # 编码类型
            2  # 忽略建议只读标志
        )

        logger.debug(f"Successfully opened workbook: {file_path} (read_only={read_only})")
        return wb
    except Exception as e:
        logger.error(f"Failed to open workbook '{file_path}': {e}")
        return None

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
