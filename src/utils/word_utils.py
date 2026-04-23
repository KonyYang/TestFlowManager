"""
Word工具模块
提供底层的Word操作工具函数
"""

from typing import Optional, Any, List, Tuple
from src.core.logger import logger
from src.infrastructure.office.legacy_word_runtime_provider import (
    shared_word_runtime_provider,
)


def get_shared_word_app():
    """获取共享的Word应用实例"""
    return shared_word_runtime_provider.acquire_application()


def release_word_app():
    """释放Word应用实例"""
    shared_word_runtime_provider.release_application()


def cleanup_word_resources():
    """彻底清理Word资源，在应用退出时调用"""
    shared_word_runtime_provider.cleanup_resources()

def is_word_closed(word_app: Any) -> bool:
    """
    检查Word应用程序是否已关闭

    Args:
        word_app: Word应用程序对象

    Returns:
        如果Word已关闭返回True，否则返回False
    """
    return shared_word_runtime_provider.is_application_closed(word_app)


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


def open_docx_document(file_path: str):
    """
    使用python-docx打开Word文档

    Args:
        file_path: Word文档路径

    Returns:
        Document对象，如果打开失败则返回None
    """
    try:
        from docx import Document
        doc = Document(file_path)
        logger.info(f"成功加载文档: {file_path}")
        return doc
    except Exception as e:
        logger.error(f"无法加载文档: {e}")
        raise


def save_docx_document(doc, save_path: str = None):
    """
    保存Word文档

    Args:
        doc: Document对象
        save_path: 保存路径，如果为None则保存到原路径

    Returns:
        是否成功保存
    """
    try:
        logger.info(f"准备保存文档: {save_path if save_path else 'unknown path'}")
        if save_path:
            logger.info(f"📖 正在将文档另存为新路径: {save_path}")
            doc.save(save_path)
            logger.info(f"✅ 文档已另存为: {save_path}")
        else:
            # 如果没有提供保存路径，抛出错误
            logger.error("❌ 保存路径不能为空")
            return False
        return True
    except Exception as e:
        logger.error(f"❌ 保存文档失败: {e}", exc_info=True)
        raise
