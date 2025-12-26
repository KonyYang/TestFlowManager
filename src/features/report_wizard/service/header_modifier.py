"""
页眉修改服务模块
提供Word文档页眉修改相关的业务逻辑服务
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from docx import Document
from datetime import datetime
import pythoncom
from src.core.logger import logger
from src.utils.word_utils import get_shared_word_app


class HeaderModifier:
    """
    页眉修改服务类
    提供Word文档页眉修改相关的业务逻辑服务
    """

    def __init__(self, file_path: str):
        """初始化页眉修改服务"""
        self.file_path = file_path
        self.doc = None
        self.win_document = None
        self.word_app = None



    def modify_header(self, header_data: Dict[str, Any]) -> bool:
        """
        使用 win32com.client 精准填写 Word 首页页眉内容

        :param header_data: 页眉数据字典，包含 report_no, version, date, tester 等字段
        :return: 是否成功
        """
        try:
            # 检查是否已存在Word应用实例
            self.word_app = get_shared_word_app()
            if self.word_app is None:
                logger.error("无法获取Word应用程序实例")
                return False
            
            self.word_app.Visible = False
            
            # 打开文档
            cleaned_path = os.path.normpath(self.file_path)
            self.win_document = self.word_app.Documents.Open(cleaned_path)

            first_section = self.win_document.Sections(1)
            header_range = first_section.Headers(2).Range  # wdHeaderFooterFirstPage = 2

            # 查找合适的表格
            # logger.info("🔍 开始查找符合条件的表格（rows >= 5 and cols >= 3）...")
            # logger.debug(f"📎 当前页眉中表格数量: {header_range.Tables.Count}")

            suitable_table = None
            for table_index in range(1, header_range.Tables.Count + 1):
                header_table = header_range.Tables(table_index)
                rows = header_table.Rows.Count
                cols = header_table.Columns.Count

                if rows >= 5 and cols >= 3:
                    suitable_table = header_table
                    break

            if suitable_table is None:
                logger.error("❌ 未找到任何符合要求的表格（需要至少 5 行 x 3 列）")
                return False

            # 从header_data中获取数据
            report_no = header_data.get("report_no", "").strip()
            version = header_data.get("version", "").strip()
            completion_date = header_data.get("completion_date", "").strip()
            tester = header_data.get("tester", "").strip()
            report_title = header_data.get("report_title", "").strip()
            requested_by = header_data.get("requested_by", "").strip()
            test_period = header_data.get("test_period", "").strip()

            # 填充单元格内容 - 实验室测试报告格式
            self._replace_cell_text(suitable_table.Cell(3, 1), report_no, "第3行第1列")
            self._replace_cell_text(suitable_table.Cell(5, 1), requested_by, "第5行第1列")
            self._replace_cell_text(suitable_table.Cell(3, 4), tester, "第3行第4列")
            self._replace_cell_text(suitable_table.Cell(5, 3), tester, "第5行第3列", only_first_paragraph=True)
            self._replace_cell_text(suitable_table.Cell(5, 2), report_title, "第5行第2列")
            self._replace_cell_text(suitable_table.Cell(3, 2), completion_date, "第3行第2列")
            self._replace_cell_text(suitable_table.Cell(3, 3), test_period, "第3行第3列")
            
            # 检查是否有第5列，如果有则更新版本号
            if suitable_table.Columns.Count >= 5:
                self._replace_cell_text(suitable_table.Cell(3, 5), version, "第3行第5列")

            logger.info("✅ 首页页眉内容已成功填写")
            return True

        except Exception as e:
            logger.error(f"填写首页页眉失败: {e}", exc_info=True)
            return False

    def _format_date(self, date_str: str) -> str:
        """
        格式化日期字符串为 "DD/MMM/YYYY" 格式
        :param date_str: 输入的日期字符串
        :return: 格式化后的日期字符串
        """
        parsed_date = self._parse_date(date_str)
        if parsed_date:
            return parsed_date.strftime("%d/%b/%Y")  # 输出格式：31/Oct/2024
        return date_str

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        解析多种格式的日期字符串
        :param date_str: 日期字符串
        :return: 解析后的datetime对象，如果解析失败则返回None
        """
        if not date_str:
            return None

        date_formats = [
            "%Y-%m-%d",         # 2024-12-01
            "%d %b %Y",         # 01 Dec 2024
            "%d %B %Y",         # 01 December 2024
            "%b %d, %Y",        # Dec 01, 2024
            "%m/%d/%Y",         # 12/01/2024
            "%Y/%m/%d",         # 2024/12/01
            "%d-%b-%Y",         # 31-Oct-2024
            "%d/%m/%Y",         # 31/10/2024
            "%d.%m.%Y",         # 31.10.2024
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def format_date_to_standard(self, date_str: str) -> str:
        """
        将日期字符串解析为标准格式 (dd/MMM/YYYY，如 31/Oct/2024)
        
        :param date_str: 输入的日期字符串
        :return: 标准格式的日期字符串
        """
        parsed_date = self._parse_date(date_str)
        if parsed_date:
            return parsed_date.strftime("%d/%b/%Y")  # 输出格式：31/Oct/2024
        return date_str  # 如果解析失败，返回原始字符串

    def modify_revision_record_date(self, header_data: Dict[str, Any], is_customer_report: bool = False, doc=None) -> bool:
        """
        修改正文 'REVISION RECORD' 表格中的日期
        
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
            formatted_date = self.format_date_to_standard(completion_date_str)

            # 使用传入的doc参数，如果为None则使用self.doc
            doc_to_use = doc if doc is not None else self.doc
            if doc_to_use is None:
                logger.error("❌ 文档对象未提供且self.doc为None")
                return False
            
            found = False
            target_paragraph_found = False

            target_title = "REVISION RECORD" if is_customer_report else "8. REVISION RECORD"

            for i, para in enumerate(doc_to_use.paragraphs):
                if target_title in para.text:
                    target_paragraph_found = True

                    current_element = para._element
                    next_element = current_element.getnext()

                    while next_element is not None:
                        if next_element.tag.endswith('tbl'):
                            from docx.table import Table
                            table_obj = Table(next_element, doc_to_use)
                            table = table_obj
                            found = True
                            break
                        next_element = next_element.getnext()

                    if found:
                        break

            if not target_paragraph_found:
                # 尝试查找其他可能的标题
                for i, para in enumerate(doc_to_use.paragraphs):
                    if "REVISION" in para.text and ("RECORD" in para.text or "record" in para.text.lower()):
                        target_paragraph_found = True

                        current_element = para._element
                        next_element = current_element.getnext()

                        while next_element is not None:
                            if next_element.tag.endswith('tbl'):
                                from docx.table import Table
                                table_obj = Table(next_element, doc_to_use)
                                table = table_obj
                                found = True
                                break
                            next_element = next_element.getnext()

                        if found:
                            break

            if not found:
                logger.warning(f"未找到包含 '{target_title}' 的表格")
                # 尝试查找所有表格，看是否有包含修订记录相关文本的
                for table_idx, table in enumerate(doc_to_use.tables):
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
                self.set_cell_text(table.cell(target_row, target_col), formatted_date)
                
                logger.info(f"修订记录表格日期已更新为: {formatted_date}")
            except Exception as cell_error:
                logger.error(f"更新修订记录表格日期时出错: {cell_error}")
                # 备选方案：尝试更新第2列和第3列
                try:
                    self.set_cell_text(table.cell(1, 2), formatted_date)
                    self.set_cell_text(table.cell(1, 3), formatted_date)
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
                        self.set_cell_text(cell, "")

            return True

            return True

        except Exception as e:
            logger.error(f"修改修订记录日期失败: {e}", exc_info=True)
            return False

    def set_cell_text(self, cell, new_texts, replace_all_paragraphs=False):
        """
        替换单元格中的文本内容，保留原有格式（支持多段落）

        :param cell: python-docx 单元格对象
        :param new_texts: 字符串 或 字符串列表（对应多个段落）
        :param replace_all_paragraphs: 是否替换所有段落，默认只替换第一个
        """
        if isinstance(new_texts, str):
            new_texts = [new_texts]

        # 获取单元格的原始内容
        original_content = cell.text.strip()
        
        paragraphs = cell.paragraphs
        if not replace_all_paragraphs:
            paragraphs = paragraphs[:1] if paragraphs else []

        for i, para in enumerate(paragraphs):
            if i >= len(new_texts):
                break

            if not para.runs:
                para.add_run(new_texts[i])
                continue

            # 保留第一个 run 的格式
            first_run = para.runs[0]
            original_format = {
                'bold': first_run.bold,
                'italic': first_run.italic,
                'underline': first_run.underline,
                'font_name': first_run.font.name,
                'font_size': first_run.font.size,
                'color': first_run.font.color.rgb if first_run.font.color else None,
                'highlight_color': first_run.font.highlight_color,
                'alignment': para.alignment,
            }

            # 清空原有文本
            for run in list(para.runs):
                run.text = ""

            # 插入新文本
            new_run = para.add_run(new_texts[i])
            new_run.bold = original_format['bold']
            new_run.italic = original_format['italic']
            new_run.underline = original_format['underline']
            new_run.font.name = original_format['font_name']
            new_run.font.size = original_format['font_size']
            if original_format['color']:
                new_run.font.color.rgb = original_format['color']
            new_run.font.highlight_color = original_format['highlight_color']
            para.alignment = original_format['alignment']

        # 记录被替换的单元格信息
        logger.info(f"✅ 单元格内容已更新，保留了原始格式")
        logger.info(f"📍 被修改单元格原始内容: '{original_content}' -> 新内容: '{new_texts[0] if new_texts else ''}'")

    def _set_docx_cell_text(self, cell, new_text: str):
        """
        为docx表格单元格设置文本内容
        
        :param cell: docx表格单元格对象
        :param new_text: 新文本内容
        """
        # 清空单元格内容
        cell.text = new_text

    def _replace_cell_text(self, cell, new_text: str, location_desc: str = "", only_first_paragraph: bool = False):
        """
        替换单元格中的文本内容，支持仅替换第一个段落，并保留段落结构。

        :param cell: Word 表格单元格对象
        :param new_text: 要插入的新文本
        :param location_desc: 单元格位置描述（用于日志）
        :param only_first_paragraph: 是否只替换第一个段落，默认 False
        """
        try:
            cell_range = cell.Range
            original_text = cell_range.Text.strip()
            logger.info(f"{location_desc} 原始内容: '{original_text}'")

            if only_first_paragraph:
                # 只替换第一个段落的内容，保留其他段落和段落标记
                if cell_range.Paragraphs.Count >= 1:
                    first_para_range = cell_range.Paragraphs(1).Range
                    first_para_end_pos = first_para_range.End - 1  # 不包含段落结束符

                    # 设置范围为第一个段落的文本内容（不含段落符）
                    sub_range = cell_range.Duplicate
                    sub_range.SetRange(cell_range.Start, first_para_end_pos)

                    sub_range.Text = new_text
                    logger.info(f"{location_desc} 第一个段落已更新为: '{new_text}'")
                else:
                    cell_range.InsertAfter(new_text)
                    logger.warning(f"{location_desc} 没有段落，已插入新文本作为第一个段落。")
            else:
                # 清空单元格并插入新文本
                cell_range.Text = ""
                cell_range.InsertAfter(new_text)
                logger.info(f"{location_desc} 已更新为: '{new_text}'")

        except Exception as e:
            logger.error(f"替换 {location_desc} 内容时出错: {e}", exc_info=True)
            raise

    def modify_second_header(self, header_data: Dict[str, Any]) -> bool:
        """
        使用 win32com.client 精准填写 Word 第二节页眉中的 "Report No." 字段，
        替换其后的内容，保留原格式和换行符。

        :param header_data: 页眉数据字典，包含 report_no 等字段
        :return: 是否成功
        """
        try:
            # 检查是否已存在Word应用实例
            if self.word_app is None:
                self.word_app = get_shared_word_app()
                if self.word_app is None:
                    logger.error("无法获取Word应用程序实例")
                    return False
            
            self.word_app.Visible = False
            
            # 打开文档
            cleaned_path = os.path.normpath(self.file_path)
            self.win_document = self.word_app.Documents.Open(cleaned_path)

            # 定位到第二节页眉
            second_section = self.win_document.Sections(2)
            header_range = second_section.Headers(1).Range  # wdHeaderFooterPrimary = 1

            logger.info("✅ 成功定位到第二节页眉")

            # 获取第一个表格
            if header_range.Tables.Count == 0:
                logger.error("❌ 页眉中未找到表格！")
                return False

            header_table = header_range.Tables(1)

            if header_table.Rows.Count < 1 or header_table.Columns.Count < 1:
                logger.error("❌ 表格行列不足，无法操作！")
                return False

            cell_range = header_table.Cell(1, 1).Range
            original_text = cell_range.Text.strip()

            logger.info(f"🔍 检查单元格内容: '{original_text}'")

            # 查找 "Report No."
            report_no_pos = cell_range.Text.find("Report No.")
            if report_no_pos == -1:
                logger.error("❌ 未找到 'Report No.' 关键词！")
                return False

            logger.info("✅ 找到 'Report No.' 关键词")

            # 定义要替换的值
            report_no = header_data.get("report_no", "").strip()

            if not report_no:
                logger.warning("⚠️ header_data 中未找到 report_no 字段！")
                return False

            # 创建新范围，从 "Report No." 后开始
            new_range = cell_range.Duplicate
            report_no_end_pos = report_no_pos + len("Report No.")
            new_range.Start = cell_range.Start + report_no_end_pos
            new_range.End = cell_range.End - 1  # 去掉最后的 \x07（Word 的段落标记）

            # 替换为新的 report_no
            new_range.Text = report_no

            logger.info(f"✅ 已更新 'Report No.' 为: '{report_no}'")
            return True

        except Exception as e:
            logger.error(f"填写第二节页眉失败: {e}", exc_info=True)
            return False

    def cleanup(self):
        """清理资源"""
        try:
            if self.win_document:
                # 检查文档是否仍然可用
                try:
                    # 尝试访问文档的一个属性来检查连接状态
                    _ = self.win_document.Name
                    # 如果能成功访问，则关闭文档
                    self.win_document.Close()
                except (AttributeError, Exception):
                    # 如果文档已断开连接，则跳过关闭
                    pass
                self.win_document = None
            # 注意：不要关闭word_app，因为它可能是共享实例
        except Exception as e:
            logger.debug(f"清理页眉修改器资源时出错: {e}")  # 改为debug级别，避免不必要的错误日志