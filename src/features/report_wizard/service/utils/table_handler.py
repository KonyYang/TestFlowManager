"""
表格处理工具模块
提供Word文档表格查找和修改相关的功能
"""

from typing import Dict, Any, Optional
from docx import Document
from src.core.logger import logger
from .cell_modifier import CellModifier
from .date_handler import DateHandler


class TableHandler:
    """
    表格处理器
    提供Word文档表格查找和修改相关的功能
    """

    @staticmethod
    def modify_revision_record_date(doc, header_data: Dict[str, Any], is_customer_report: bool = False) -> bool:
        """
        修改正文 'REVISION RECORD' 表格中的日期
        
        :param doc: python-docx Document 对象
        :param header_data: 页眉数据字典，包含 completion_date 等字段
        :param is_customer_report: 是否是客户报告，默认为 False
        :return: 是否成功
        """
        try:
            # 优先使用completion_date，如果不存在则使用date
            completion_date_str = header_data.get("completion_date", "")
            if not completion_date_str:
                completion_date_str = header_data.get("date", "")
            
            if not completion_date_str:
                logger.warning("header_data 中未找到 completion_date 或 date 字段！")
                return False

            # 格式化日期
            formatted_date = DateHandler.format_date_to_standard(completion_date_str)

            if doc is None:
                logger.error("❌ 文档对象未提供")
                return False
            
            found = False
            target_paragraph_found = False

            target_title = "REVISION RECORD" if is_customer_report else "8. REVISION RECORD"

            for i, para in enumerate(doc.paragraphs):
                if target_title in para.text:
                    target_paragraph_found = True

                    current_element = para._element
                    next_element = current_element.getnext()

                    while next_element is not None:
                        if next_element.tag.endswith('tbl'):
                            from docx.table import Table
                            table_obj = Table(next_element, doc)
                            table = table_obj
                            found = True
                            break
                        next_element = next_element.getnext()

                    if found:
                        break

            if not target_paragraph_found:
                # 尝试查找其他可能的标题
                for i, para in enumerate(doc.paragraphs):
                    if "REVISION" in para.text and ("RECORD" in para.text or "record" in para.text.lower()):
                        target_paragraph_found = True

                        current_element = para._element
                        next_element = current_element.getnext()

                        while next_element is not None:
                            if next_element.tag.endswith('tbl'):
                                from docx.table import Table
                                table_obj = Table(next_element, doc)
                                table = table_obj
                                found = True
                                break
                            next_element = next_element.getnext()

                        if found:
                            break

            if not found:
                logger.warning(f"未找到包含 '{target_title}' 的表格")
                # 尝试查找所有表格，看是否有包含修订记录相关文本的
                for table_idx, table in enumerate(doc.tables):
                    for row in table.rows:
                        for cell in row.cells:
                            if "DATE" in cell.text.upper() or "DATE" in cell.text.upper():
                                table = table
                                found = True
                                break
                        if found:
                            break
                    if found:
                        break

            if not found:
                logger.warning("未找到任何可能的修订记录表格")
                return False

            if len(table.rows) < 2 or len(table.columns) < 4:
                logger.warning("目标表格行列不足，无法操作！")
                return False
            
            # 修改第二行（索引1）的日期列，通常是第3列（索引2）或第4列（索引3）
            try:
                # 首先检查表头，找到日期列
                header_row = table.rows[0]
                date_column_idx = -1
                for i, cell in enumerate(header_row.cells):
                    if "DATE" in cell.text.upper():
                        date_column_idx = i
                        break
                
                # 如果找到了日期列标题，就在该列设置日期；否则默认在第3列设置
                target_col = 2 if date_column_idx == -1 else date_column_idx
                target_row = 1  # 通常在第二行（索引1）更新日期
                
                # 修改第一行数据（索引1）的日期列 - 使用参考代码的set_cell_text方法
                CellModifier.set_cell_text(table.cell(target_row, target_col), formatted_date)
                
                logger.info(f"修订记录表格日期已更新为: {formatted_date}")
            except Exception as cell_error:
                logger.error(f"更新修订记录表格日期时出错: {cell_error}")
                # 备选方案：尝试更新第2列和第3列
                try:
                    CellModifier.set_cell_text(table.cell(1, 2), formatted_date)
                    CellModifier.set_cell_text(table.cell(1, 3), formatted_date)
                    logger.info(f"修订记录表格日期已通过备选方案更新为: {formatted_date}")
                except Exception as backup_error:
                    logger.error(f"备选更新修订记录表格日期时也出错: {backup_error}")
                    return False

            if is_customer_report:
                while len(table.rows) < 4:
                    table.add_row()

                if len(table.rows) > 4:
                    for i in range(len(table.rows) - 1, 3, -1):  # 保留前4行
                        table._tbl.remove(table.rows[i]._tr)

                for i in range(2, 4):
                    for cell in table.rows[i].cells:
                        CellModifier.set_cell_text(cell, "")

            return True

        except Exception as e:
            logger.error(f"修改修订记录日期失败: {e}", exc_info=True)
            return False