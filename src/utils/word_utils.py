"""
Word工具模块
提供底层的Word操作工具函数
"""

from typing import Optional, Any, List, Tuple
from src.core.logger import logger

# 共享的Word应用实例
_shared_word_app = None
_word_instance_count = 0
_word_initialized = False


def get_shared_word_app():
    """获取共享的Word应用实例"""
    global _shared_word_app, _word_instance_count, _word_initialized

    # 检查Word应用是否仍然可用
    if _shared_word_app is not None:
        try:
            # 尝试访问Word应用的一个基本属性来检查它是否仍然响应
            _shared_word_app.Name
        except:
            # Word应用似乎已经关闭或无响应，需要重新创建
            _shared_word_app = None
            _word_instance_count = 0
            _word_initialized = False
            logger.debug("Previous Word application instance was not responsive, will create a new one")

    if _shared_word_app is None:
        try:
            import pythoncom
            if not _word_initialized:
                pythoncom.CoInitialize()
                _word_initialized = True
            import win32com.client
            _shared_word_app = win32com.client.Dispatch("Word.Application")
            _shared_word_app.Visible = False
            logger.debug("Created new shared Word application instance")
        except Exception as e:
            logger.error(f"Failed to initialize Word application: {e}")
            return None

    _word_instance_count += 1
    logger.debug(f"Word instance count increased to {_word_instance_count}")
    return _shared_word_app


def release_word_app():
    """释放Word应用实例"""
    global _shared_word_app, _word_instance_count, _word_initialized

    _word_instance_count -= 1
    logger.debug(f"Word instance count decreased to {_word_instance_count}")

    # 不再主动关闭Word应用，让它保持运行以提高性能
    # 只有在应用退出时才彻底清理资源
    if _word_instance_count <= 0 and _shared_word_app:
        try:
            # 只关闭所有文档，但保持Word应用运行
            if _shared_word_app.Documents:
                for document in _shared_word_app.Documents:
                    try:
                        document.Close(SaveChanges=False)
                    except:
                        pass
            logger.debug("Closed all documents but kept Word application running")
        except Exception as e:
            logger.error(f"Error while closing documents: {e}")


def cleanup_word_resources():
    """彻底清理Word资源，在应用退出时调用"""
    global _shared_word_app, _word_instance_count, _word_initialized

    if _shared_word_app:
        try:
            # 检查Word应用是否仍然可用
            try:
                _shared_word_app.Name  # 测试连接
                # 只有在Word可用时才尝试关闭文档和退出
                # 关闭所有文档
                if _shared_word_app.Documents:
                    for document in _shared_word_app.Documents:
                        try:
                            document.Close(SaveChanges=False)
                        except:
                            pass

                # 退出Word应用
                _shared_word_app.Quit()
                logger.debug("Word application quit successfully")
            except:
                # Word应用已经关闭或无响应，直接清理引用
                logger.debug("Word application was already closed or unresponsive")
        except Exception as e:
            logger.error(f"Error while cleaning up Word resources: {e}")
        finally:
            _shared_word_app = None

    # 反初始化COM
    if _word_initialized:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
            _word_initialized = False
            logger.debug("COM library uninitialized")
        except Exception as e:
            logger.error(f"Error while uninitializing COM library: {e}")

def is_word_closed(word_app: Any) -> bool:
    """
    检查Word应用程序是否已关闭

    Args:
        word_app: Word应用程序对象

    Returns:
        如果Word已关闭返回True，否则返回False
    """
    try:
        # 尝试访问Word应用程序的一个基本属性
        word_app.Name
        return False  # 如果成功访问，说明Word仍在运行
    except:
        return True  # 否则认为Word已关闭


def close_document(document: Any, save_changes: bool = False) -> bool:
    """
    关闭Word文档并释放资源

    Args:
        document: Word文档对象
        save_changes: 是否保存更改

    Returns:
        是否成功关闭
    """
    try:
        if document:
            document.Close(SaveChanges=save_changes)
            logger.debug(f"Document closed successfully (save_changes={save_changes})")
            return True
    except Exception as e:
        logger.error(f"Failed to close document: {e}")
    return False


def open_word_file(file_path: str, read_only: bool = True, password: Optional[str] = None) -> Any:
    """
    通用打开Word文件函数，使用Word COM接口打开文件

    Args:
        file_path: Word文件路径
        read_only: 是否以只读模式打开
        password: 文件密码（可选）

    Returns:
        Word文档对象，如果打开失败则返回None
    """
    try:
        # 检查文件是否存在
        import os
        if not os.path.exists(file_path):
            logger.error(f"Word file not found: {file_path}")
            return None

        word_app = get_shared_word_app()
        if word_app is None:
            logger.error("Failed to get Word application instance")
            return None

        word_app.Visible = False
        word_app.DisplayAlerts = False

        # 以指定模式打开文件
        doc = word_app.Documents.Open(
            file_path,
            ReadOnly=read_only,
            PasswordDocument=password or ""
        )

        logger.debug(f"Successfully opened document: {file_path} (read_only={read_only})")
        return doc
    except Exception as e:
        logger.error(f"Failed to open document '{file_path}': {e}")
        return None


def get_table_cell_text(table: Any, row: int, col: int) -> str:
    """
    获取表格中指定单元格的文本内容

    Args:
        table: Word表格对象
        row: 行号（从1开始）
        col: 列号（从1开始）

    Returns:
        单元格文本内容
    """
    try:
        cell = table.Cell(row, col)
        if cell.Range.ContentControls.Count > 0:
            text = cell.Range.ContentControls(1).Range.Text
        elif cell.Range.FormFields.Count > 0:
            text = cell.Range.FormFields(1).Result
        else:
            text = cell.Range.Text
        return text.replace('\r', '').replace('\a', '').strip()
    except Exception as e:
        logger.error(f"Failed to get cell text at ({row}, {col}): {e}")
        return ""


def find_text_in_document(document: Any, search_text: str) -> Optional[Any]:
    """
    在文档中查找指定文本

    Args:
        document: Word文档对象
        search_text: 要查找的文本

    Returns:
        找到的范围对象，如果未找到则返回None
    """
    try:
        # 使用Find方法查找文本
        found_range = document.Content.Duplicate
        found_range.Find.Text = search_text
        found_range.Find.Execute()

        if found_range.Find.Found:
            return found_range
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to search text '{search_text}' in document: {e}")
        return None


def find_cell_with_text(table: Any, search_text: str) -> Optional[Tuple[int, int]]:
    """
    在表格中查找包含指定文本的单元格

    Args:
        table: Word表格对象
        search_text: 要查找的文本

    Returns:
        (行号, 列号)的元组，如果未找到则返回None
    """
    try:
        for i in range(1, table.Rows.Count + 1):
            for j in range(1, table.Columns.Count + 1):
                try:
                    cell_text = table.Cell(i, j).Range.Text.strip()
                    if search_text.lower() in cell_text.lower():
                        return (i, j)
                except Exception:
                    continue
        return None
    except Exception as e:
        logger.error(f"Failed to find cell with text '{search_text}': {e}")
        return None


def find_target_cell(table: Any, search_text: str, next_row: bool = False) -> Optional[Any]:
    """
    在表格中查找包含指定文本的单元格，并返回相邻的目标单元格

    Args:
        table: Word表格对象
        search_text: 要查找的文本
        next_row: 是否在下一行查找目标单元格

    Returns:
        目标单元格对象，如果未找到则返回None
    """
    try:
        position = find_cell_with_text(table, search_text)
        if position:
            i, j = position
            target_cell = None
            if next_row and i < table.Rows.Count:
                target_cell = table.Cell(i + 1, j)
            elif not next_row and j < table.Columns.Count:
                target_cell = table.Cell(i, j + 1)
            return target_cell
    except Exception as e:
        logger.error(f"Failed to find target cell for text '{search_text}': {e}")
    return None


def modify_cell_content(cell: Any, new_text: str) -> bool:
    """
    修改单元格内容，支持内容控件和表单字段

    Args:
        cell: Word单元格对象
        new_text: 新的文本内容

    Returns:
        是否成功修改
    """
    try:
        if cell.Range.ContentControls.Count > 0:
            cc = cell.Range.ContentControls(1)
            # 检查内容控件是否被锁定
            if hasattr(cc, 'LockContents') and cc.LockContents:
                logger.warning(f"Content control is locked; cannot modify")
                return False

            # 根据内容控件类型进行处理
            if cc.Type == 4:  # Dropdown list
                found = False
                for entry in cc.DropdownListEntries:
                    option_text = entry.Text.strip().replace('\r', '').replace('\a', '')
                    if option_text == new_text:
                        entry.Select()
                        found = True
                        break
                if not found:
                    logger.warning(f"Dropdown option '{new_text}' not found in content control")
                    return False
                return True
            elif cc.Type in [0, 1, 3]:  # RichText, PlainText or Text ContentControl
                cc.Range.Text = new_text
                return True
            elif cc.Type == 6:  # Date ContentControl
                cc.Range.Text = new_text
                return True
            else:
                logger.warning(f"Unsupported content control type {cc.Type}")
                return False
        elif cell.Range.FormFields.Count > 0:
            ff = cell.Range.FormFields(1)
            if ff.Type == 70:  # Text Input FormField
                ff.Result = new_text
                return True
            else:
                logger.warning(f"Unsupported FormField type {ff.Type}")
                return False
        else:
            cell.Range.Text = new_text
            return True
    except Exception as e:
        logger.error(f"Error modifying cell content: {e}")
        return False


def extract_field_value_from_table(doc: Any, search_keyword: str, next_row: bool = False) -> str:
    """
    从文档表格中提取字段值

    Args:
        doc: Word文档对象
        search_keyword: 搜索关键词
        next_row: 是否在下一行查找值

    Returns:
        提取的值
    """
    logger.debug(f"Searching for keyword '{search_keyword}' in tables...")
    try:
        for table in doc.Tables:
            for i in range(1, table.Rows.Count + 1):
                for j in range(1, table.Columns.Count + 1):
                    try:
                        cell_text = table.Cell(i, j).Range.Text.strip()
                        if search_keyword.lower() in cell_text.lower():
                            target_cell = None
                            if next_row and i < table.Rows.Count:
                                target_cell = table.Cell(i + 1, j)
                            elif not next_row and j < table.Columns.Count:
                                target_cell = table.Cell(i, j + 1)

                            if target_cell:
                                if target_cell.Range.ContentControls.Count > 0:
                                    value = target_cell.Range.ContentControls(1).Range.Text
                                elif target_cell.Range.FormFields.Count > 0:
                                    value = target_cell.Range.FormFields(1).Result
                                else:
                                    value = target_cell.Range.Text
                                return value.replace('\r', '').replace('\a', '').strip()
                    except Exception:
                        continue
    except Exception as e:
        logger.error(f"Error extracting field '{search_keyword}': {e}")
    return ""


def find_paragraph_with_text(document: Any, search_text: str) -> Optional[Any]:
    """
    在文档段落中查找包含指定文本的段落

    Args:
        document: Word文档对象
        search_text: 要查找的文本

    Returns:
        找到的段落对象，如果未找到则返回None
    """
    try:
        for para in document.Paragraphs:
            if search_text in para.Range.Text:
                return para
        return None
    except Exception as e:
        logger.error(f"Failed to find paragraph with text '{search_text}': {e}")
        return None


def get_section_header(section: Any, header_type: int = 1) -> Optional[Any]:
    """
    获取文档节的页眉

    Args:
        section: Word文档节对象
        header_type: 页眉类型 (1=Primary, 2=First Page, 3=Even Page)

    Returns:
        页眉对象，如果不存在则返回None
    """
    try:
        header = section.Headers(header_type)
        if header.Exists:
            return header
        return None
    except Exception as e:
        logger.error(f"Failed to get section header: {e}")
        return None


def get_section_footer(section: Any, footer_type: int = 1) -> Optional[Any]:
    """
    获取文档节的页脚

    Args:
        section: Word文档节对象
        footer_type: 页脚类型 (1=Primary, 2=First Page, 3=Even Page)

    Returns:
        页脚对象，如果不存在则返回None
    """
    try:
        footer = section.Footers(footer_type)
        if footer.Exists:
            return footer
        return None
    except Exception as e:
        logger.error(f"Failed to get section footer: {e}")
        return None