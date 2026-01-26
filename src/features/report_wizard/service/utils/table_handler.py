"""
表格处理工具模块
提供Word文档表格查找和修改相关的功能
"""

import win32com.client
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

    @staticmethod
    def apply_table_formatting(target_table):
        """
        应用表格格式设置，包括边框、自动调整和垂直对齐
        
        Args:
            target_table: Word表格对象（win32com对象）
        """
        try:
            # 设置表格边框线
            target_table.Borders.Enable = True
            # 设置边框线宽
            for border_id in range(7):  # Word中边框的ID范围是0-6
                try:
                    target_table.Borders(border_id).Visible = True
                    target_table.Borders(border_id).LineWidth = 0.5  # 设置线宽
                except:
                    # 某些边框可能不存在，忽略错误
                    pass

            # 设置表格根据窗口自动调整 - 使用安全的多级降级策略
            success = False
            
            # 方法1: 百分比宽度设置（安全方法）
            try:
                # 先设置宽度类型为百分比
                target_table.PreferredWidthType = 2  # wdPreferredWidthPercent
                # 安全设置宽度值为100%（页面宽度的100%）
                target_table.PreferredWidth = 100  # 设置为页面宽度的100%
                target_table.AllowAutoFit = False  # 禁用自动调整，强制使用设定宽度
                logger.info("成功使用百分比宽度设置并禁用自动调整")
                success = True
            except Exception as e1:
                logger.warning(f"百分比宽度设置失败: {e1}")
                
            # 如果方法1失败，尝试方法2: AutoFitBehavior(1) - 自动适应窗口
            if not success:
                try:
                    target_table.PreferredWidthType = 3  # wdPreferredWidthType = wdPreferredWidthPercent
                    target_table.AllowAutoFit = True
                    target_table.AutoFitBehavior(1)  # wdAutoFitWindow
                    logger.info("成功使用AutoFitBehavior(1)调整表格")
                    success = True
                except Exception as e2:
                    logger.warning(f"AutoFitBehavior(1)失败: {e2}")
                    
            # 如果前两种方法都失败，尝试方法3: AutoFit()，然后手动调整列宽
            if not success:
                try:
                    target_table.AutoFit()
                    logger.info("成功使用AutoFit()调整表格")
                    
                    # 尝试手动调整每列宽度，使其平均分布
                    total_cols = target_table.Columns.Count
                    if total_cols > 0:
                        # 获取页面宽度（减去页边距）
                        try:
                            page_width = target_table.Range.Document.PageSetup.PageWidth
                            left_margin = target_table.Range.Document.PageSetup.LeftMargin
                            right_margin = target_table.Range.Document.PageSetup.RightMargin
                            available_width = page_width - left_margin - right_margin
                            
                            # 平均分配每列宽度，确保不超过最大限制
                            # 对于多列表格，设置更小的列宽以避免超过页面宽度
                            col_width = min(available_width * 0.9 / total_cols, 1584) if total_cols > 0 else 1584  # 使用90%的可用宽度，最大不超过1584
                            
                            # 对于超过10列的表格，进一步减小列宽以确保表格不会超出页面
                            if total_cols > 10:
                                col_width = min(col_width, 60)  # 对于多列表格，最大列宽设为60磅
                            
                            for i in range(1, total_cols + 1):
                                try:
                                    target_table.Columns(i).Width = col_width
                                except:
                                    # 如果设置单个列宽失败，尝试设置整个表格宽度
                                    try:
                                        target_table.PreferredWidth = available_width * 0.9
                                        target_table.PreferredWidthType = 3  # wdPreferredWidthPercent
                                    except:
                                        pass
                            
                            logger.info(f"手动设置每列宽度为 {col_width} 磅")
                        except Exception as e3:
                            logger.warning(f"手动调整列宽失败: {e3}")
                    success = True
                except Exception as e3:
                    logger.warning(f"AutoFit()失败: {e3}")
                    
            # 如果以上方法都失败，尝试方法4: 专门针对多列表格的处理
            if not success:
                try:
                    total_cols = target_table.Columns.Count
                    if total_cols > 10:  # 对于多列表格，使用特殊的处理方式
                        # 设置表格为窄列模式
                        for i in range(1, total_cols + 1):
                            try:
                                # 尝试设置较小的固定宽度
                                target_table.Columns(i).SetWidth(12.0, 0)  # 12磅，wdRulerPageFit = 0
                            except:
                                pass  # 如果设置单列宽度失败，继续下一行
                        logger.info(f"已为多列表格({total_cols}列)设置窄列模式")
                        success = True
                except Exception as e4:
                    logger.warning(f"多列表格处理失败: {e4}")

            # 设置所有单元格垂直对齐方式为居中
            try:
                target_table.CellRange.VerticalAlignment = 1  # wdCellAlignVerticalCenter = 1
            except:
                pass
            
            # 额外确保所有单元格都设置为垂直居中（双重保险）
            try:
                for i in range(1, target_table.Rows.Count + 1):
                    row = target_table.Rows(i)
                    for j in range(1, row.Cells.Count + 1):
                        cell = row.Cells(j)
                        cell.VerticalAlignment = 1  # wdAlignVerticalCenter
                logger.info("所有单元格已设置为垂直居中")
            except Exception as e:
                logger.warning(f"设置单元格垂直居中失败: {e}")
                # 如果上述方法失败，尝试使用CellRange方式
                try:
                    target_table.CellRange.VerticalAlignment = 1  # wdCellAlignVerticalCenter = 1
                except:
                    pass
        except Exception as e:
            logger.warning(f"设置表格格式时出错: {e}")

    @staticmethod
    def modify_revision_record_date_win32com(win_document, header_data: Dict[str, Any], is_customer_report: bool = False) -> bool:
        """
        使用win32com修改正文 'REVISION RECORD' 表格中的日期
        
        :param win_document: win32com Word文档对象
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

            # 查找修订记录表格
            target_title = "REVISION RECORD" if is_customer_report else "8. REVISION RECORD"
            target_table = None
            
            # 首先按标题查找表格
            for i in range(1, win_document.Paragraphs.Count + 1):
                paragraph = win_document.Paragraphs(i)
                para_text = paragraph.Range.Text.strip()
                
                if target_title in para_text:
                    # 查找紧随其后的表格
                    para_end_pos = paragraph.Range.End
                    for j in range(1, win_document.Tables.Count + 1):
                        table = win_document.Tables(j)
                        if table.Range.Start >= para_end_pos:
                            target_table = table
                            break
                    
                    if target_table:
                        break
            
            # 如果按标题未找到，尝试查找包含"REVISION"和"RECORD"的表格
            if not target_table:
                for i in range(1, win_document.Paragraphs.Count + 1):
                    paragraph = win_document.Paragraphs(i)
                    para_text = paragraph.Range.Text.strip()
                    
                    if "REVISION" in para_text.upper() and ("RECORD" in para_text.upper() or "record" in para_text.lower()):
                        # 查找紧随其后的表格
                        para_end_pos = paragraph.Range.End
                        for j in range(1, win_document.Tables.Count + 1):
                            table = win_document.Tables(j)
                            if table.Range.Start >= para_end_pos:
                                target_table = table
                                break
                        
                        if target_table:
                            break
            
            # 如果还是没找到，尝试查找包含日期列的表格
            if not target_table:
                for j in range(1, win_document.Tables.Count + 1):
                    table = win_document.Tables(j)
                    # 检查表格是否包含日期相关字段
                    for row_idx in range(1, min(3, table.Rows.Count + 1)):  # 检查前几行
                        for col_idx in range(1, table.Columns.Count + 1):
                            cell_text = table.Cell(row_idx, col_idx).Range.Text.strip()
                            if "DATE" in cell_text.upper():
                                target_table = table
                                break
                        if target_table:
                            break
                    if target_table:
                        break

            if not target_table:
                logger.warning(f"未找到包含 '{target_title}' 的表格")
                return False

            if target_table.Rows.Count < 2 or target_table.Columns.Count < 4:
                logger.warning("目标表格行列不足，无法操作！")
                return False
            
            # 修改第二行（索引2）的日期列，通常是第3列（索引3）或第4列（索引4）
            try:
                # 首先检查表头，找到日期列
                header_row = target_table.Rows(1)
                date_column_idx = -1
                for i in range(1, header_row.Cells.Count + 1):
                    cell_text = header_row.Cells(i).Range.Text.strip()
                    if "DATE" in cell_text.upper():
                        date_column_idx = i
                        break
                
                # 如果找到了日期列标题，就在该列设置日期；否则默认在第3列设置
                target_col = 3 if date_column_idx == -1 else date_column_idx
                target_row = 2  # 通常在第二行（索引2）更新日期
                
                # 修改第一行数据（索引2）的日期列
                target_table.Cell(target_row, target_col).Range.Text = formatted_date
                
                logger.info(f"修订记录表格日期已更新为: {formatted_date}")
            except Exception as cell_error:
                logger.error(f"更新修订记录表格日期时出错: {cell_error}")
                # 备选方案：尝试更新第3列和第4列
                try:
                    target_table.Cell(2, 3).Range.Text = formatted_date
                    target_table.Cell(2, 4).Range.Text = formatted_date
                    logger.info(f"修订记录表格日期已通过备选方案更新为: {formatted_date}")
                except Exception as backup_error:
                    logger.error(f"备选更新修订记录表格日期时也出错: {backup_error}")
                    return False

            # 如果是客户报告，处理额外的行
            if is_customer_report:
                # 确保表格至少有4行
                while target_table.Rows.Count < 4:
                    target_table.Rows.Add()

                # 如果表格行数过多，移除多余行
                if target_table.Rows.Count > 4:
                    for i in range(target_table.Rows.Count, 4, -1):
                        try:
                            target_table.Rows(i).Delete()
                        except:
                            pass  # 忽略删除失败

                # 清空第3和第4行的内容
                for i in range(3, 5):
                    if i <= target_table.Rows.Count:
                        for cell in target_table.Rows(i).Cells:
                            cell.Range.Text = ""

            return True

        except Exception as e:
            logger.error(f"修改修订记录日期失败: {e}", exc_info=True)
            return False

    @staticmethod
    def find_table_by_paragraph_win32com(word_doc, paragraph_keyword: str):
        """
        使用win32com在Word文档中根据段落关键字查找紧跟其后的表格
        
        Args:
            word_doc: win32com Word文档对象
            paragraph_keyword: 段落中的关键字（如"TEST DESCRIPTION"）
            
        Returns:
            找到的表格对象，如果未找到则返回None
        """
        logger.info(f"使用win32com查找关键字 '{paragraph_keyword}' 后的表格")
        
        # 遍历文档中的所有段落
        for i in range(1, word_doc.Paragraphs.Count + 1):
            paragraph = word_doc.Paragraphs(i)
            para_text = paragraph.Range.Text.strip()
            
            # 检查段落文本是否包含目标关键字
            if paragraph_keyword.upper() in para_text.upper():
                # 检查段落是否为粗体且有下划线
                if paragraph.Range.Font.Bold and paragraph.Range.Font.Underline:
                    logger.info(f"找到包含 '{paragraph_keyword}' 的粗体下划线段落: {para_text}")
                    
                    # 获取文档中所有表格的位置
                    table_positions = []
                    for j, doc_table in enumerate(word_doc.Tables):
                        # 记录表格在文档中的位置
                        table_positions.append((doc_table.Range.Start, doc_table))
                    
                    # 按表格起始位置排序
                    table_positions.sort(key=lambda x: x[0])
                    
                    # 查找紧跟在此段落后的第一个表格
                    paragraph_end_pos = paragraph.Range.End
                    for pos, table in table_positions:
                        if pos >= paragraph_end_pos:
                            logger.info(f"找到紧跟在段落后的表格")
                            return table
    
        # 如果通过段落查找失败，尝试通过表格内容查找
        for j, doc_table in enumerate(word_doc.Tables):
            # 检查表格第一行的单元格内容
            if doc_table.Rows.Count > 0:
                first_row = doc_table.Rows(1)
                for cell in first_row.Cells:
                    cell_text = cell.Range.Text.strip()
                    if paragraph_keyword.upper() in cell_text.upper():
                        # 检查字体是否为粗体
                        if cell.Range.Font.Bold:
                            logger.info(f"在表格中找到包含 '{paragraph_keyword}' 的单元格")
                            return doc_table
    
        logger.warning(f"未找到关键字 '{paragraph_keyword}' 后的表格")
        return None