"""
页眉管理工具模块
提供Word文档页眉修改相关的功能
"""

import os
from typing import Dict, Any
from src.core.logger import logger
from src.utils.word_utils import get_shared_word_app
from .cell_modifier import CellModifier
from .date_handler import DateHandler


class HeaderManager:
    """
    页眉管理器
    提供Word文档页眉修改相关的功能
    """

    @staticmethod
    def modify_first_header(file_path: str, header_data: Dict[str, Any], word_app=None) -> bool:
        """
        使用 win32com.client 精准填写 Word 首页页眉内容

        :param file_path: Word文档路径
        :param header_data: 页眉数据字典，包含 report_no, version, date, tester 等字段
        :param word_app: Word应用程序实例，如果为None则获取共享实例
        :return: 是否成功
        """
        try:
            # 检查是否已存在Word应用实例
            if word_app is None:
                word_app = get_shared_word_app()
                if word_app is None:
                    logger.error("无法获取Word应用程序实例")
                    return False
            
            word_app.Visible = False
            word_app.DisplayAlerts = False
            
            # 打开文档
            cleaned_path = os.path.normpath(file_path)
            win_document = word_app.Documents.Open(cleaned_path)

            first_section = win_document.Sections(1)
            header_range = first_section.Headers(2).Range  # wdHeaderFooterFirstPage = 2

            # 查找合适的表格
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
            # 根据版本号决定报告编号的显示格式
            formatted_report_no = HeaderManager.format_report_no_for_display(header_data)
            CellModifier.replace_cell_text(suitable_table.Cell(3, 1), formatted_report_no, "第3行第1列")
            CellModifier.replace_cell_text(suitable_table.Cell(5, 1), requested_by, "第5行第1列")
            CellModifier.replace_cell_text(suitable_table.Cell(3, 4), tester, "第3行第4列")
            CellModifier.replace_cell_text(suitable_table.Cell(5, 3), tester, "第5行第3列", only_first_paragraph=True)
            CellModifier.replace_cell_text(suitable_table.Cell(5, 2), report_title, "第5行第2列")
            CellModifier.replace_cell_text(suitable_table.Cell(3, 2), completion_date, "第3行第2列")
            CellModifier.replace_cell_text(suitable_table.Cell(3, 3), test_period, "第3行第3列")
            
            # 检查是否有第5列，如果有则更新版本号
            if suitable_table.Columns.Count >= 5:
                version_to_display = HeaderManager.format_version_for_display(version)
                CellModifier.replace_cell_text(suitable_table.Cell(3, 5), version_to_display, "第3行第5列")

            logger.info("✅ 首页页眉内容已成功填写")
            return True

        except Exception as e:
            logger.error(f"填写首页页眉失败: {e}", exc_info=True)
            return False

    @staticmethod
    def modify_first_header_with_document(win_document, header_data: Dict[str, Any]) -> bool:
        """
        使用已打开的win32com文档对象精准填写 Word 首页页眉内容

        :param win_document: 已打开的Word文档对象
        :param header_data: 页眉数据字典，包含 report_no, version, date, tester 等字段
        :return: 是否成功
        """
        try:
            first_section = win_document.Sections(1)
            header_range = first_section.Headers(2).Range  # wdHeaderFooterFirstPage = 2

            # 查找合适的表格
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
            # 根据版本号决定报告编号的显示格式
            formatted_report_no = HeaderManager.format_report_no_for_display(header_data)
            CellModifier.replace_cell_text(suitable_table.Cell(3, 1), formatted_report_no, "第3行第1列")
            CellModifier.replace_cell_text(suitable_table.Cell(5, 1), requested_by, "第5行第1列")
            CellModifier.replace_cell_text(suitable_table.Cell(3, 4), tester, "第3行第4列")
            CellModifier.replace_cell_text(suitable_table.Cell(5, 3), tester, "第5行第3列", only_first_paragraph=True)
            CellModifier.replace_cell_text(suitable_table.Cell(5, 2), report_title, "第5行第2列")
            CellModifier.replace_cell_text(suitable_table.Cell(3, 2), completion_date, "第3行第2列")
            CellModifier.replace_cell_text(suitable_table.Cell(3, 3), test_period, "第3行第3列")
            
            # 检查是否有第5列，如果有则更新版本号
            if suitable_table.Columns.Count >= 5:
                version_to_display = HeaderManager.format_version_for_display(version)
                CellModifier.replace_cell_text(suitable_table.Cell(3, 5), version_to_display, "第3行第5列")

            logger.info("✅ 首页页眉内容已成功填写")
            return True

        except Exception as e:
            logger.error(f"填写首页页眉失败: {e}", exc_info=True)
            return False

    @staticmethod
    def modify_second_header(file_path: str, header_data: Dict[str, Any], word_app=None) -> bool:
        """
        使用 win32com.client 精准填写 Word 第二节页眉中的 "Report No." 字段，
        替换其后的内容，保留原格式和换行符。

        :param file_path: Word文档路径
        :param header_data: 页眉数据字典，包含 report_no 等字段
        :param word_app: Word应用程序实例，如果为None则获取共享实例
        :return: 是否成功
        """
        try:
            # 检查是否已存在Word应用实例
            if word_app is None:
                word_app = get_shared_word_app()
                if word_app is None:
                    logger.error("无法获取Word应用程序实例")
                    return False

            word_app.Visible = False
            word_app.DisplayAlerts = False

            # 打开文档
            cleaned_path = os.path.normpath(file_path)
            win_document = word_app.Documents.Open(cleaned_path)

            # 定位到第二节页眉
            second_section = win_document.Sections(2)
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

            # 如果 report_no 为空，则跳过修改
            if not report_no:
                logger.warning("⚠️ header_data 中未找到 report_no 字段，跳过第二节页眉修改")
                return True  # 返回成功，因为这不是致命错误

            # 根据版本号格式化最终的报告编号
            final_report_no = HeaderManager.format_report_no_for_display(header_data)

            # 创建新范围，从 "Report No." 后开始
            new_range = cell_range.Duplicate
            report_no_end_pos = report_no_pos + len("Report No.")
            new_range.Start = cell_range.Start + report_no_end_pos
            new_range.End = cell_range.End - 1  # 去掉最后的 \x07（Word 的段落标记）

            # 替换为新的 report_no
            new_range.Text = final_report_no

            logger.info(f"✅ 已更新 'Report No.' 为: '{final_report_no}'")
            return True

        except Exception as e:
            logger.error(f"填写第二节页眉失败: {e}", exc_info=True)
            return False

    @staticmethod
    def modify_second_header_with_document(win_document, header_data: Dict[str, Any]) -> bool:
        """
        使用已打开的win32com文档对象精准填写 Word 第二节页眉中的 "Report No." 字段，
        替换其后的内容，保留原格式和换行符。

        :param win_document: 已打开的Word文档对象
        :param header_data: 页眉数据字典，包含 report_no 等字段
        :return: 是否成功
        """
        try:
            # 定位到第二节页眉
            second_section = win_document.Sections(2)
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

            # 如果 report_no 为空，则跳过修改
            if not report_no:
                logger.warning("⚠️ header_data 中未找到 report_no 字段，跳过第二节页眉修改")
                return True  # 返回成功，因为这不是致命错误

            # 根据版本号格式化最终的报告编号
            final_report_no = HeaderManager.format_report_no_for_display(header_data)

            # 创建新范围，从 "Report No." 后开始
            new_range = cell_range.Duplicate
            report_no_end_pos = report_no_pos + len("Report No.")
            new_range.Start = cell_range.Start + report_no_end_pos
            new_range.End = cell_range.End - 1  # 去掉最后的 \x07（Word 的段落标记）

            # 替换为新的 report_no
            new_range.Text = final_report_no

            logger.info(f"✅ 已更新 'Report No.' 为: '{final_report_no}'")
            return True

        except Exception as e:
            logger.error(f"填写第二节页眉失败: {e}", exc_info=True)
            return False

    @staticmethod
    def format_report_no_for_display(header_data: Dict[str, Any]) -> str:
        """
        根据版本号格式化报告编号显示
        如果版本号是 "A"，则只显示报告编号；否则添加 "Rev." 前缀
        """
        report_no = header_data.get("report_no", "").strip()
        version = header_data.get("version", "A").strip()
        
        if version == "A":
            return report_no
        else:
            # 如果版本号不包含 "Rev." 前缀，则添加
            if not version.startswith("Rev."):
                version_with_prefix = f"Rev.{version}"
            else:
                version_with_prefix = version
            return f"{report_no} {version_with_prefix}"

    @staticmethod
    def format_version_for_display(version: str) -> str:
        """
        格式化版本号显示
        如果版本号是 "A"，则只显示 "A"；否则添加 "Rev." 前缀
        """
        if version == "A":
            return "A"
        else:
            # 如果版本号不包含 "Rev." 前缀，则添加
            if not version.startswith("Rev."):
                return f"Rev.{version}"
            else:
                return version