"""
单元格处理工具模块
提供Word文档单元格文本替换相关的功能
"""

from typing import Union, List
from src.core.logger import logger


class CellModifier:
    """
    单元格修改器
    提供Word文档单元格文本替换相关的功能
    """

    @staticmethod
    def set_cell_text(cell, new_texts: Union[str, List[str]], replace_all_paragraphs: bool = False):
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

    @staticmethod
    def set_docx_cell_text(cell, new_text: str):
        """
        为docx表格单元格设置文本内容
        
        :param cell: docx表格单元格对象
        :param new_text: 新文本内容
        """
        # 清空单元格内容
        cell.text = new_text

    @staticmethod
    def replace_cell_text(cell, new_text: str, location_desc: str = "", only_first_paragraph: bool = False):
        """
        替换单元格中的文本内容，支持仅替换第一个段落，并保留段落结构。
        使用 win32com.client 对象进行操作

        :param cell: Word 表格单元格对象 (win32com对象)
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