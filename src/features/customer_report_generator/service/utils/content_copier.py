"""
内容复制模块
处理Word文档内容的复制功能
"""

from src.core.logger import logger


class ContentCopier:
    """
    内容复制器
    负责处理Word文档内容的复制功能
    """
    
    @staticmethod
    def copy_purpose_to_equipments_content(source_doc, template_doc):
        """
        复制从"1. PURPOSE"到"7. EQUIPMENTS"的内容
        """
        try:
            # 在源文档中查找"1. PURPOSE"
            source_range = source_doc.Content
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
            source_range = source_doc.Content
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
            content_range = source_doc.Range(start_pos, end_pos)
            
            # 定位模板文档的第一节范围
            section_one_range = template_doc.Sections(1).Range
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

    @staticmethod
    def copy_revision_record(source_doc, template_doc):
        """
        复制修订记录（8. REVISION RECORD）
        """
        try:
            # 检查文档是否包含段落
            if not hasattr(source_doc, 'Paragraphs'):
                logger.warning("源文档不包含段落")
                return False
                
            # 从源文档的最后一段向前查找"8. REVISION RECORD"
            found_revision_start = False
            found_revision_end = False
            start_index = -1
            end_index = -1
            
            # 反向查找起始位置
            for i in range(source_doc.Paragraphs.Count, 0, -1):
                paragraph = source_doc.Paragraphs(i)
                if "8. REVISION RECORD" in paragraph.Range.Text:
                    found_revision_start = True
                    start_index = i
                    break
            
            if not found_revision_start:
                logger.warning("未在源文档中找到 '8. REVISION RECORD'")
                return False
            
            # 查找结束位置
            for i in range(start_index + 1, source_doc.Paragraphs.Count + 1):
                paragraph = source_doc.Paragraphs(i)
                if "Note: Each new revision replaces/supersedes all previous revisions." in paragraph.Range.Text:
                    found_revision_end = True
                    end_index = i
                    break
            
            if not found_revision_end:
                logger.warning("未找到修订记录结束标记")
                return False
            
            # 获取内容范围
            start_pos = source_doc.Paragraphs(start_index).Range.Start
            end_pos = source_doc.Paragraphs(end_index).Range.End
            content_range = source_doc.Range(start_pos, end_pos)
            
            # 将内容插入到模板文档末尾
            ContentCopier._insert_content_to_document_end(content_range, template_doc)
            
            # 在文档末尾添加3个空行和"*** End of Report ***"段落
            # 定位到目标文档末尾
            target_range = template_doc.Range()
            target_range.Collapse(0)  # wdCollapseEnd = 0
            
            # 添加3个空行
            target_range.Text = "\n\n\n"
            
            # 添加"*** End of Report ***"段落并设置格式
            end_marker_range = template_doc.Range()
            end_marker_range.Collapse(0)  # wdCollapseEnd = 0
            end_marker_range.Text = "*** End of Report ***\n"
            
            # 设置格式：Times New Roman 字体、小四字号、加粗、倾斜、居中
            end_marker_range.Font.Name = "Times New Roman"
            end_marker_range.Font.Size = 12  # 小四对应12磅
            end_marker_range.Font.Bold = True
            end_marker_range.Font.Italic = True
            end_marker_range.ParagraphFormat.Alignment = 1  # 1 表示居中对齐
            
            logger.debug("修订记录复制完成，并添加了报告结束标记")
            return True
        except Exception as e:
            logger.error(f"复制修订记录时出错: {e}")
            return False

    @staticmethod
    def _insert_content_to_document_end(content_range, template_doc):
        """
        将内容插入到文档末尾
        
        Args:
            content_range: 要插入的内容范围
            template_doc: 模板文档对象
        """
        try:
            # 定位到目标文档末尾
            target_range = template_doc.Range()
            target_range.Collapse(0)  # wdCollapseEnd = 0
            
            # 插入分页符（如果需要）
            # 这里简化处理，直接在文档末尾插入内容
            target_range.FormattedText = content_range.FormattedText
            
            logger.debug("内容已插入到文档末尾")
        except Exception as e:
            logger.error(f"插入内容到文档末尾时出错: {e}")
            raise