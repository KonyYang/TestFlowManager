"""
客户报告生成服务模块
提供客户报告生成相关的业务逻辑服务
"""

import os
import shutil
import pythoncom
import win32com.client as win32
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from src.core.logger import logger
from src.core.config_manager import config_manager


class CustomerReportService:
    """
    客户报告生成服务类
    提供客户报告生成相关的业务逻辑服务
    """

    def __init__(self):
        """初始化客户报告生成服务"""
        self.word_app = None
        self.source_doc = None
        self.template_doc = None
        self.temp_template_path = None

    def _initialize_word_app(self):
        """初始化Word应用程序"""
        try:
            # 初始化COM组件
            pythoncom.CoInitialize()
            self.word_app = win32.gencache.EnsureDispatch('Word.Application')
            self.word_app.Visible = False
            logger.debug("Word应用程序初始化成功")
        except Exception as e:
            logger.error(f"初始化Word应用程序失败: {e}")
            raise

    def _find_template_file(self):
        """
        查找客户报告模板文件
        
        Returns:
            str: 模板文件路径，如果未找到则返回空字符串
        """
        try:
            # 从配置中获取模板目录
            template_dir = config_manager.get("paths.template_dir", "")
            if not template_dir or not os.path.exists(template_dir):
                logger.warning(f"模板目录不存在: {template_dir}")
                return ""
            
            # 查找以"E-4515"开头的Word文档
            for filename in os.listdir(template_dir):
                if filename.startswith("E-4515") and filename.endswith((".docx", ".doc")):
                    template_path = os.path.join(template_dir, filename)
                    # 规范化路径
                    template_path = os.path.normpath(template_path)
                    logger.debug(f"找到客户报告模板文件: {template_path}")
                    return template_path
            
            logger.warning("未找到以'E-4515'开头的客户报告模板文件")
            return ""
        except Exception as e:
            logger.error(f"查找模板文件时出错: {e}")
            return ""

    def _select_source_document(self, parent_window=None, project_path=None):
        """
        选择源文档
        
        Args:
            parent_window: 父窗口
            project_path: 项目路径
            
        Returns:
            str: 源文档路径，如果用户取消则返回空字符串
        """
        try:
            # 设置默认目录
            default_dir = project_path if project_path and os.path.exists(project_path) else ""
            
            # 弹出文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                parent_window,
                "选择源文档",
                default_dir,
                "Word文档 (*.docx *.doc)"
            )
            
            if not file_path:
                logger.info("用户取消了文件选择")
                return ""
            
            # 规范化路径
            file_path = os.path.normpath(file_path)
            logger.debug(f"选择的源文档: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"选择源文档时出错: {e}")
            return ""

    def _prepare_documents(self, source_path, template_path):
        """
        准备源文档和模板文档
        
        Args:
            source_path (str): 源文档路径
            template_path (str): 模板文档路径
        """
        try:
            # 规范化路径
            source_path = os.path.normpath(source_path)
            template_path = os.path.normpath(template_path)
            
            # 检查源文件是否存在
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"源文档不存在: {source_path}")
            
            # 检查模板文件是否存在
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"模板文档不存在: {template_path}")
            
            # 打开源文档（只读模式）
            self.source_doc = self.word_app.Documents.Open(source_path, ReadOnly=True)
            logger.debug(f"成功打开源文档: {source_path}")
            
            # 创建临时模板文件路径
            source_dir = os.path.dirname(source_path)
            self.temp_template_path = os.path.join(source_dir, "Temp_CustomerReport.docx")
            self.temp_template_path = os.path.normpath(self.temp_template_path)
            
            # 复制模板文件到临时路径
            shutil.copy2(template_path, self.temp_template_path)
            logger.debug(f"模板文件已复制到临时路径: {self.temp_template_path}")
            
            # 打开临时模板文件
            self.template_doc = self.word_app.Documents.Open(self.temp_template_path)
            logger.debug("临时模板文件已打开")
        except Exception as e:
            logger.error(f"准备文档时出错: {e}")
            raise

    def _modify_header(self):
        """
        修改页眉信息
        
        Returns:
            bool: 是否成功修改页眉
        """
        try:
            # 获取源文档首页页眉表格
            logger.debug(f"源文档段落数: {self.source_doc.Paragraphs.Count}")
            logger.debug(f"源文档节段数: {self.source_doc.Sections.Count}")
            
            # 检查第一节是否存在
            if self.source_doc.Sections.Count < 1:
                logger.error("源文档没有节段")
                return False
                
            source_section = self.source_doc.Sections(1)
            logger.debug(f"源文档第一节存在")
            
            # 参考 fill_first_header_win32 方法，只使用首页页眉 (wdHeaderFooterFirstPage = 2)
            try:
                header_range = source_section.Headers(2).Range  # wdHeaderFooterFirstPage = 2
                
                # 查找合适的表格（参考 fill_first_header_win32 方法）
                logger.debug(f"源文档首页页眉中表格数量: {header_range.Tables.Count}")
                
                source_header_table = None
                for table_index in range(1, header_range.Tables.Count + 1):
                    header_table = header_range.Tables(table_index)
                    rows = header_table.Rows.Count
                    cols = header_table.Columns.Count
                    logger.debug(f"正在检查源文档第 {table_index} 个表格：{rows} 行 x {cols} 列")
                    
                    # 查找至少5行3列的表格
                    if rows >= 5 and cols >= 3:
                        logger.info(f"在源文档中找到符合条件的表格：第 {table_index} 个表格，{rows} 行 x {cols} 列")
                        source_header_table = header_table
                        break
                
                if source_header_table is None:
                    logger.error("源文档首页页眉中未找到符合要求的表格（需要至少 5 行 x 3 列）")
                    return False
            except Exception as e:
                logger.error(f"访问源文档首页页眉失败: {e}")
                return False
            
            logger.debug(f"源文档首页页眉表格已获取，行列数: {source_header_table.Rows.Count}x{source_header_table.Columns.Count}")
            

            # 获取模板文档首页页眉表格
            logger.debug(f"模板文档段落数: {self.template_doc.Paragraphs.Count}")
            logger.debug(f"模板文档节段数: {self.template_doc.Sections.Count}")
            
            # 检查第一节是否存在
            if self.template_doc.Sections.Count < 1:
                logger.error("模板文档没有节段")
                return False
                
            template_section = self.template_doc.Sections(1)
            logger.debug(f"模板文档第一节存在")
            
            # 参考 fill_first_header_win32 方法，只使用首页页眉 (wdHeaderFooterFirstPage = 2)
            try:
                header_range = template_section.Headers(2).Range  # wdHeaderFooterFirstPage = 2
                
                # 查找合适的表格（参考 fill_first_header_win32 方法）
                logger.debug(f"模板文档首页页眉中表格数量: {header_range.Tables.Count}")
                
                template_header_table = None
                for table_index in range(1, header_range.Tables.Count + 1):
                    header_table = header_range.Tables(table_index)
                    rows = header_table.Rows.Count
                    cols = header_table.Columns.Count
                    logger.debug(f"正在检查模板文档第 {table_index} 个表格：{rows} 行 x {cols} 列")
                    
                    # 查找至少5行3列的表格
                    if rows >= 5 and cols >= 3:
                        logger.info(f"在模板文档中找到符合条件的表格：第 {table_index} 个表格，{rows} 行 x {cols} 列")
                        template_header_table = header_table
                        break
                
                if template_header_table is None:
                    logger.error("模板文档首页页眉中未找到符合要求的表格（需要至少 5 行 x 3 列）")
                    return False
            except Exception as e:
                logger.error(f"访问模板文档首页页眉失败: {e}")
                return False
            
            logger.debug(f"模板文档首页页眉表格已获取，行列数: {template_header_table.Rows.Count}x{template_header_table.Columns.Count}")
            
            # 提取并处理源文档页眉表格第3行第1列内容
            report_no_content = source_header_table.Cell(3, 1).Range.Text
            # 模仿VBA中的处理方式，去除回车符和特殊字符并trim
            report_no_content = report_no_content.replace("\r", "").replace("\x07", "").strip()
            logger.debug(f"从源文档提取的报告编号内容: {report_no_content}")
            
            # 填充模板页眉表格
            # 第3行第1列：report_no_content + "-CR"
            template_header_table.Cell(3, 1).Range.Text = report_no_content + "-CR"
            logger.debug(f"已设置模板表格第3行第1列内容: {report_no_content}-CR")
            
            # 第3行第2、3列 - 模仿VBA中的处理方式
            col2_text = source_header_table.Cell(3, 2).Range.Text.replace("\r", "").strip()
            template_header_table.Cell(3, 2).Range.Text = col2_text
            logger.debug(f"已设置模板表格第3行第2列内容: {col2_text}")
            
            col3_text = source_header_table.Cell(3, 3).Range.Text.replace("\r", "").strip()
            template_header_table.Cell(3, 3).Range.Text = col3_text
            logger.debug(f"已设置模板表格第3行第3列内容: {col3_text}")
            
            # 第5行第1列 - 模仿VBA中的处理方式
            col5_2_text = source_header_table.Cell(5, 2).Range.Text.replace("\r", "").strip()
            template_header_table.Cell(5, 1).Range.Text = col5_2_text
            logger.debug(f"已设置模板表格第5行第1列内容: {col5_2_text}")
            
            # 处理第5行第3列（源文档）的内容，复制到第5行第2列（模板文档）
            # 模仿VBA中的处理逻辑
            source_cell_5_3 = source_header_table.Cell(5, 3).Range
            template_cell_5_2 = template_header_table.Cell(5, 2).Range
            
            # 获取源单元格的段落数量
            source_para_count = source_cell_5_3.Paragraphs.Count
            template_para_count = template_cell_5_2.Paragraphs.Count
            logger.debug(f"源单元格(5,3)段落数: {source_para_count}, 模板单元格(5,2)段落数: {template_para_count}")
            
            # 提取源单元格的第一段内容（模仿VBA）
            source_first_paragraph = ""
            if source_para_count >= 1:
                source_first_paragraph = source_cell_5_3.Paragraphs(1).Range.Text
            logger.debug(f"源单元格(5,3)第1段落内容: {repr(source_first_paragraph)}")
            
            # 提取源单元格的第二段内容（模仿VBA）
            source_second_paragraph = ""
            if source_para_count >= 2:
                source_second_paragraph = source_cell_5_3.Paragraphs(2).Range.Text
            logger.debug(f"源单元格(5,3)第2段落内容: {repr(source_second_paragraph)}")
            
            # 替换目标单元格的第一个段落内容
            if template_para_count >= 1:
                template_cell_5_2.Paragraphs(1).Range.Text = source_first_paragraph
                logger.debug(f"已设置模板单元格(5,2)第1段落内容")
            
            # 替换目标单元格的第二个段落内容
            if template_para_count >= 2:
                template_cell_5_2.Paragraphs(2).Range.Text = source_second_paragraph
                logger.debug(f"已设置模板单元格(5,2)第2段落内容")
            
            # 处理第5行第4列（源文档）的内容，复制到第5行第3列（模板文档）
            # 模仿VBA中的处理逻辑
            source_cell_5_4 = source_header_table.Cell(5, 4).Range
            template_cell_5_3 = template_header_table.Cell(5, 3).Range
            
            # 获取源单元格的段落数量
            source_para_count = source_cell_5_4.Paragraphs.Count
            template_para_count = template_cell_5_3.Paragraphs.Count
            logger.debug(f"源单元格(5,4)段落数: {source_para_count}, 模板单元格(5,3)段落数: {template_para_count}")
            
            # 提取源单元格的第一段内容（模仿VBA）
            source_first_paragraph = ""
            if source_para_count >= 1:
                source_first_paragraph = source_cell_5_4.Paragraphs(1).Range.Text
            logger.debug(f"源单元格(5,4)第1段落内容: {repr(source_first_paragraph)}")
            
            # 提取源单元格的第二段内容（模仿VBA）
            source_second_paragraph = ""
            if source_para_count >= 2:
                source_second_paragraph = source_cell_5_4.Paragraphs(2).Range.Text
            logger.debug(f"源单元格(5,4)第2段落内容: {repr(source_second_paragraph)}")
            
            # 替换目标单元格的第一个段落内容
            if template_para_count >= 1:
                template_cell_5_3.Paragraphs(1).Range.Text = source_first_paragraph
                logger.debug(f"已设置模板单元格(5,3)第1段落内容")
            
            # 替换目标单元格的第二个段落内容
            if template_para_count >= 2:
                template_cell_5_3.Paragraphs(2).Range.Text = source_second_paragraph
                logger.debug(f"已设置模板单元格(5,3)第2段落内容")
            
            # 打印要替换的文本信息
            logger.debug(f"将要替换的文本内容: {report_no_content}")
            
            # 修改模板的第二节页眉表格（参考 fill_second_header_win32 方法）
            logger.debug(f"模板文档节段数: {self.template_doc.Sections.Count}")
            if self.template_doc.Sections.Count >= 2:
                # 参考 fill_second_header_win32 方法，使用主要页眉 (wdHeaderFooterPrimary = 1)
                try:
                    second_section = self.template_doc.Sections(2)
                    header_range = second_section.Headers(1).Range  # wdHeaderFooterPrimary = 1
                    
                    logger.debug("成功定位到模板文档第二节页眉")
                    logger.debug(f"第二节页眉中表格数量: {header_range.Tables.Count}")
                    
                    # 检查第二节页眉中是否存在表格
                    if header_range.Tables.Count == 0:
                        logger.error("模板文档第二节页眉中未找到表格！")
                        return False
                    
                    second_section_header_table = header_range.Tables(1)
                    
                    if second_section_header_table.Rows.Count < 1 or second_section_header_table.Columns.Count < 1:
                        logger.error("模板文档第二节页眉表格行列不足，无法操作！")
                        return False
                    
                    cell_range = second_section_header_table.Cell(1, 1).Range
                    original_text = cell_range.Text.strip()
                    logger.debug(f"检查第二节页眉表格第1行第1列内容: '{original_text}'")
                    
                    # 查找 "Report No."
                    report_no_pos = cell_range.Text.find("Report No.")
                    if report_no_pos == -1:
                        logger.error("模板文档第二节页眉表格中未找到 'Report No.' 关键词！")
                        return False
                    
                    logger.debug("在模板文档第二节页眉表格中找到 'Report No.' 关键词")
                    
                    # 清理 report_no_content 中的隐藏字符和段落标记（模仿VBA）
                    replace_text = report_no_content.replace("\r", "").replace("\x07", "").strip()
                    
                    # 创建新范围，从 "Report No." 后开始
                    new_range = cell_range.Duplicate
                    report_no_end_pos = report_no_pos + len("Report No.")
                    new_range.Start = cell_range.Start + report_no_end_pos
                    new_range.End = cell_range.End - 1  # 去掉最后的 \x07（Word 的段落标记）
                    
                    # 替换为新的 DL 编号
                    new_range.Text = replace_text + "-CR"
                    logger.debug(f"已在第二节页眉中将 'Report No.' 更新为: '{replace_text}-CR'")
                except Exception as e:
                    logger.error(f"处理模板文档第二节页眉时出错: {e}")
                    return False
            else:
                logger.warning("模板文档没有第二节")
            
            logger.debug("页眉信息修改完成")
            return True
        except Exception as e:
            logger.error(f"修改页眉信息时出错: {e}")
            return False

    def _copy_purpose_to_equipments_content(self):
        """
        复制从"1. PURPOSE"到"7. EQUIPMENTS"的内容
        """
        try:
            # 在源文档中查找"1. PURPOSE"
            source_range = self.source_doc.Content
            find_purpose = source_range.Find
            find_purpose.Text = "1. PURPOSE"
            find_purpose.MatchCase = True
            find_purpose.MatchWholeWord = True
            found_purpose = find_purpose.Execute()
            
            if not found_purpose:
                logger.warning("未找到 '1. PURPOSE' 起始位置")
                return False
            
            start_pos = source_range.Start
            
            # 在源文档中查找"7. EQUIPMENTS"
            source_range = self.source_doc.Content
            find_equipments = source_range.Find
            find_equipments.Text = "7. EQUIPMENTS"
            find_equipments.MatchCase = True
            find_equipments.MatchWholeWord = True
            found_equipments = find_equipments.Execute()
            
            if not found_equipments:
                logger.warning("未找到 '7. EQUIPMENTS' 结束位置")
                return False
            
            end_pos = source_range.Start
            
            # 提取内容范围
            content_range = self.source_doc.Range(start_pos, end_pos)
            
            # 定位模板文档的第一节范围
            section_one_range = self.template_doc.Sections(1).Range
            # 定位到第一节正文的结尾
            section_one_range.Collapse(0)  # wdCollapseEnd = 0
            
            # 复制内容到模板第一节
            content_range.Copy()
            section_one_range.Paste()
            
            logger.debug("从'1. PURPOSE'到'7. EQUIPMENTS'的内容复制完成")
            return True
        except Exception as e:
            logger.error(f"复制内容时出错: {e}")
            return False

    def _remove_number_and_dot_in_formatted_paragraphs(self):
        """
        清理章节标题格式（去除数字和点）
        """
        try:
            # 遍历模板文档中的每个段落
            for i in range(1, self.template_doc.Paragraphs.Count + 1):
                paragraph = self.template_doc.Paragraphs(i)
                paragraph_range = paragraph.Range
                
                # 检查段落是否为粗体且带单下划线
                if (paragraph_range.Font.Bold and 
                    paragraph_range.Font.Underline == 1):  # wdUnderlineSingle = 1
                    
                    para_text = paragraph_range.Text
                    
                    # 检查段落是否以数字和"."开头
                    if len(para_text) >= 2 and para_text[0].isdigit() and para_text[1] == '.':
                        # 删除前两个字符
                        new_start = paragraph_range.Start + 2
                        remove_range = self.template_doc.Range(paragraph_range.Start, new_start)
                        remove_range.Text = "\n"
                        
                        # 删除新增的空行
                        try:
                            prev_paragraph = paragraph.Previous()
                            if prev_paragraph is not None:
                                prev_paragraph.Range.Delete()
                        except:
                            # 忽略Previous方法可能出现的异常
                            pass
            
            logger.debug("章节标题格式清理完成")
            return True
        except Exception as e:
            logger.error(f"清理章节标题格式时出错: {e}")
            return False

    def _copy_revision_record(self):
        """
        复制修订记录（8. REVISION RECORD）
        """
        try:
            # 检查文档是否包含段落
            if not hasattr(self.source_doc, 'Paragraphs'):
                logger.warning("源文档不包含段落")
                return False
                
            # 从源文档的最后一段向前查找"8. REVISION RECORD"
            found_revision_start = False
            found_revision_end = False
            start_index = -1
            end_index = -1
            
            # 反向查找起始位置
            for i in range(self.source_doc.Paragraphs.Count, 0, -1):
                paragraph = self.source_doc.Paragraphs(i)
                if "8. REVISION RECORD" in paragraph.Range.Text:
                    found_revision_start = True
                    start_index = i
                    break
            
            if not found_revision_start:
                logger.warning("未在源文档中找到 '8. REVISION RECORD'")
                return False
            
            # 查找结束位置
            for i in range(start_index + 1, self.source_doc.Paragraphs.Count + 1):
                paragraph = self.source_doc.Paragraphs(i)
                if "Note: Each new revision replaces/supersedes all previous revisions." in paragraph.Range.Text:
                    found_revision_end = True
                    end_index = i
                    break
            
            if not found_revision_end:
                logger.warning("未找到修订记录结束标记")
                return False
            
            # 获取内容范围
            start_pos = self.source_doc.Paragraphs(start_index).Range.Start
            end_pos = self.source_doc.Paragraphs(end_index).Range.End
            content_range = self.source_doc.Range(start_pos, end_pos)
            
            # 将内容插入到模板文档末尾
            self._insert_content_to_document_end(content_range)
            
            logger.debug("修订记录复制完成")
            return True
        except Exception as e:
            logger.error(f"复制修订记录时出错: {e}")
            return False

    def _add_end_of_report(self):
        """
        添加报告结束标记
        """
        try:
            # 检查文档是否包含段落
            if not hasattr(self.source_doc, 'Paragraphs'):
                logger.warning("源文档不包含段落")
                return False
                
            # 从源文档的最后一个段落开始往前查找"*** End of Report ***"
            found_end_marker = False
            end_marker_paragraph = None
            
            for i in range(self.source_doc.Paragraphs.Count, 0, -1):
                paragraph = self.source_doc.Paragraphs(i)
                if "*** End of Report ***" in paragraph.Range.Text:
                    found_end_marker = True
                    end_marker_paragraph = paragraph
                    break
            
            if not found_end_marker:
                logger.warning("源文档中未找到 '*** End of Report ***' 内容")
                return False
            
            # 获取模板文档的末尾范围
            target_range = self.template_doc.Content
            target_range.Collapse(0)  # wdCollapseEnd = 0
            
            # 复制内容
            target_range.FormattedText = end_marker_paragraph.Range.FormattedText
            
            logger.debug("报告结束标记添加完成")
            return True
        except Exception as e:
            logger.error(f"添加报告结束标记时出错: {e}")
            return False

    def _move_and_format_text(self):
        """
        移动并格式化特定文本
        """
        try:
            # 定义要查找的文本
            search_text = "The results of testing only apply to the sample"
            target_text = "Unless otherwise specified, assessment of conformity to requirements is based on simple acceptance."
            
            # 查找并提取要移动的文本（从起始到句号）
            source_range = self.template_doc.Content
            find_source = source_range.Find
            find_source.Text = search_text
            find_source.Forward = True
            find_source.Wrap = 1  # wdFindStop = 1
            found_source = find_source.Execute()
            
            if not found_source:
                logger.warning(f"未找到目标文本: {search_text}")
                return False
            
            # 确定从匹配位置到句号的范围
            text_to_move_range = source_range.Duplicate
            text_to_move_range.End = text_to_move_range.Start
            while text_to_move_range.Characters.Last.Text != ".":
                text_to_move_range.MoveEnd(1, 1)
                # 防止无限循环
                if text_to_move_range.End - text_to_move_range.Start > 1000:
                    break
            
            # 剪切范围
            text_to_move_range.Cut()
            
            # 查找目标位置文本
            target_range = self.template_doc.Content
            find_target = target_range.Find
            find_target.Text = target_text
            find_target.Forward = True
            find_target.Wrap = 1  # wdFindStop = 1
            found_target = find_target.Execute()
            
            if not found_target:
                logger.warning(f"未找到目标位置文本: {target_text}")
                return False
            
            # 在目标文本后粘贴剪切的内容
            paste_range = target_range.Duplicate
            paste_range.Collapse(0)  # wdCollapseEnd = 0
            paste_range.Paste()
            
            # 设置格式：粗体、字体 Arial，大小 10
            paste_range.Font.Bold = True
            paste_range.Font.Name = "Arial"
            paste_range.Font.Size = 10
            
            logger.debug("文本移动和格式化完成")
            return True
        except Exception as e:
            logger.error(f"移动和格式化文本时出错: {e}")
            return False

    def _insert_content_to_document_end(self, content_range):
        """
        将内容插入到文档末尾
        
        Args:
            content_range: 要插入的内容范围
        """
        try:
            # 定位到目标文档末尾
            target_range = self.template_doc.Range()
            target_range.Collapse(0)  # wdCollapseEnd = 0
            
            # 插入分页符（如果需要）
            # 这里简化处理，直接在文档末尾插入内容
            target_range.FormattedText = content_range.FormattedText
            
            logger.debug("内容已插入到文档末尾")
        except Exception as e:
            logger.error(f"插入内容到文档末尾时出错: {e}")
            raise

    def _generate_new_filename(self, source_path):
        """
        生成新文件名
        
        Args:
            source_path (str): 源文件路径
            
        Returns:
            str: 新文件名
        """
        try:
            source_filename = os.path.basename(source_path)
            
            # 提取第一个连续非空格字符串
            parts = source_filename.split(" ")
            extracted_string = ""
            for part in parts:
                if part.strip():
                    extracted_string = part.strip()
                    break
            
            if not extracted_string:
                logger.error("提取的字符串为空，无法生成新文件名")
                return ""
            
            # 生成新文件名
            new_filename = source_filename.replace(extracted_string, extracted_string + "-CR")
            new_filename = new_filename.replace("Report", "Report_Customer")
            
            logger.debug(f"生成的新文件名: {new_filename}")
            return new_filename
        except Exception as e:
            logger.error(f"生成新文件名时出错: {e}")
            return ""

    def _save_customer_report(self, source_path, new_filename):
        """
        保存客户报告
        
        Args:
            source_path (str): 源文件路径
            new_filename (str): 新文件名
            
        Returns:
            str: 保存的文件路径，如果用户取消保存则返回空字符串
        """
        try:
            # 构造默认保存路径
            source_dir = os.path.dirname(source_path)
            default_save_path = os.path.join(source_dir, new_filename)
            # 规范化路径
            default_save_path = os.path.normpath(default_save_path)
            
            # 弹出保存对话框让用户确认保存路径
            save_path, _ = QFileDialog.getSaveFileName(
                None,
                "保存客户报告",
                default_save_path,
                "Word文档 (*.docx *.doc)"
            )
            
            # 如果用户取消了保存操作
            if not save_path:
                logger.info("用户取消了保存操作")
                return ""  # 返回空字符串表示用户取消操作
            
            # 规范化用户选择的路径
            save_path = os.path.normpath(save_path)
            
            # 保存文档
            self.template_doc.SaveAs2(save_path)
            logger.debug(f"客户报告已保存为: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"保存客户报告时出错: {e}")
            raise

    def _cleanup(self):
        """清理资源"""
        try:
            # 关闭文档
            if self.template_doc:
                try:
                    self.template_doc.Close(SaveChanges=False)
                except:
                    pass  # 文档可能已经关闭
                self.template_doc = None
            
            if self.source_doc:
                try:
                    self.source_doc.Close(SaveChanges=False)
                except:
                    pass  # 文档可能已经关闭
                self.source_doc = None
            
            # 删除临时文件
            if self.temp_template_path and os.path.exists(self.temp_template_path):
                try:
                    os.remove(self.temp_template_path)
                    logger.debug(f"临时文件已删除: {self.temp_template_path}")
                except Exception as e:
                    logger.warning(f"删除临时文件时出错: {e}")
            
            # 退出Word应用
            if self.word_app:
                try:
                    self.word_app.Quit()
                except:
                    pass  # Word应用可能已经退出
                self.word_app = None
            
            # 卸载COM组件
            try:
                pythoncom.CoUninitialize()
            except:
                pass  # COM组件可能已经卸载
            logger.debug("资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")

    def generate_customer_report(self, parent_window=None, project_path=None):
        """
        生成客户报告主函数
        
        Args:
            parent_window: 父窗口
            project_path: 项目路径
            
        Returns:
            tuple: (是否成功, 保存路径或错误信息)
        """
        try:
            logger.info("开始生成客户报告")
            
            # 初始化Word应用程序
            self._initialize_word_app()
            
            # 查找模板文件
            template_path = self._find_template_file()
            if not template_path:
                return False, "未找到客户报告模板文件"
            
            # 选择源文档
            source_path = self._select_source_document(parent_window, project_path)
            if not source_path:
                return False, "用户取消了操作"
            
            # 准备文档
            self._prepare_documents(source_path, template_path)
            
            # 检查文档是否成功打开
            if not self.source_doc or not self.template_doc:
                return False, "未能成功打开源文档或模板文档"
            
            # 修改页眉信息
            if not self._modify_header():
                return False, "修改页眉信息失败"
            
            # 复制核心内容
            if not self._copy_purpose_to_equipments_content():
                return False, "复制核心内容失败"

            # 复制修订记录
            if not self._copy_revision_record():
                return False, "复制修订记录失败"

            # 清理章节标题格式
            if not self._remove_number_and_dot_in_formatted_paragraphs():
                return False, "清理章节标题格式失败"

            # 添加报告结束标记
            if not self._add_end_of_report():
                return False, "添加报告结束标记失败"
            
            # 移动并格式化特定文本
            if not self._move_and_format_text():
                return False, "移动并格式化特定文本失败"
            
            # 生成新文件名
            new_filename = self._generate_new_filename(source_path)
            if not new_filename:
                return False, "生成新文件名失败"
            
            # 保存客户报告
            save_path = self._save_customer_report(source_path, new_filename)
            
            logger.info(f"客户报告生成完成: {save_path}")
            return True, save_path
        except Exception as e:
            logger.error(f"生成客户报告时出错: {e}")
            error_msg = str(e)
            return False, error_msg
        finally:
            # 清理资源
            self._cleanup()












