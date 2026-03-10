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
        复制从"1. PURPOSE"到"7. EQUIPMENTS"的内容，并复制修订记录
        """
        try:
            import time
            total_start = time.time()
            logger.debug(f"[PERF] 开始复制 PURPOSE 到 EQUIPMENTS 内容")
                
            # 在源文档中查找"1. PURPOSE"
            step1_start = time.time()
            source_range = source_doc.Content
            find_purpose = source_range.Find
            find_purpose.Text = "1. PURPOSE"
            find_purpose.MatchCase = True
            find_purpose.MatchWholeWord = True
            found_purpose = find_purpose.Execute()
            step1_end = time.time()
            logger.debug(f"[PERF] 步骤 1 - 查找'1. PURPOSE'完成，耗时：{step1_end - step1_start:.2f}秒")
                
            if not found_purpose:
                logger.warning("未找到 '1. PURPOSE' 起始位置")
                return False
                
            start_pos = source_range.Start
                
            # 在源文档中查找"7. EQUIPMENTS"
            step2_start = time.time()
            source_range = source_doc.Content
            find_equipments = source_range.Find
            find_equipments.Text = "7. EQUIPMENTS"
            find_equipments.MatchCase = True
            find_equipments.MatchWholeWord = True
            found_equipments = find_equipments.Execute()
            step2_end = time.time()
            logger.debug(f"[PERF] 步骤 2 - 查找'7. EQUIPMENTS'完成，耗时：{step2_end - step2_start:.2f}秒")
                
            if not found_equipments:
                logger.warning("未找到 '7. EQUIPMENTS' 结束位置")
                return False
                
            end_pos = source_range.Start
                
            # 提取内容范围（1. PURPOSE 到 7. EQUIPMENTS）
            step3_start = time.time()
            content_range = source_doc.Range(start_pos, end_pos)
            logger.debug(f"[PERF] 步骤 3 - 提取内容范围完成，内容长度：{end_pos - start_pos}, 耗时：{time.time() - step3_start:.2f}秒")
                
            # 定位模板文档的第一节范围
            step4_start = time.time()
            section_one_range = template_doc.Sections(1).Range
            # 定位到第一节正文的结尾
            section_one_range.Collapse(0)  # wdCollapseEnd = 0
            logger.debug(f"[PERF] 步骤 4 - 定位模板第一节完成，耗时：{time.time() - step4_start:.2f}秒")
                
            # 复制内容到模板第一节
            step5_start = time.time()
            content_range.Copy()
            copy_time = time.time()
            logger.debug(f"[PERF] 步骤 5a - Copy 操作完成，耗时：{copy_time - step5_start:.2f}秒")
                
            section_one_range.Paste()
            paste_time = time.time()
            logger.debug(f"[PERF] 步骤 5b - Paste 操作完成，耗时：{paste_time - copy_time:.2f}秒")
            
            # ============================================
            # 新增：继续查找并复制修订记录（8. REVISION RECORD）
            # ============================================
            step6_start = time.time()
            
            # 在源文档中查找"8. REVISION RECORD"
            source_range = source_doc.Content
            find_revision = source_range.Find
            find_revision.Text = "8. REVISION RECORD"
            find_revision.MatchCase = True
            find_revision.MatchWholeWord = True
            found_revision = find_revision.Execute()
            
            if not found_revision:
                logger.warning("未找到 '8. REVISION RECORD'")
                return False
            
            revision_start_pos = source_range.Start
            
            # 在源文档中查找修订记录结束标记
            source_range = source_doc.Content
            find_note = source_range.Find
            find_note.Text = "Note: Each new revision replaces/supersedes all previous revisions."
            find_note.MatchCase = True
            found_note = find_note.Execute()
            
            if not found_note:
                logger.warning("未找到修订记录结束标记")
                return False
            
            revision_end_pos = source_range.End
            
            # 提取修订记录内容范围
            revision_content_range = source_doc.Range(revision_start_pos, revision_end_pos)
            step6_end = time.time()
            logger.debug(f"[PERF] 步骤 6 - 查找并提取修订记录完成，内容长度：{revision_end_pos - revision_start_pos}, 耗时：{step6_end - step6_start:.2f}秒")
            
            # 将修订记录插入到模板文档末尾
            step7_start = time.time()
            ContentCopier._insert_content_to_document_end(revision_content_range, template_doc)
            logger.debug(f"[PERF] 步骤 7 - 插入修订记录到文档末尾完成，耗时：{time.time() - step7_start:.2f}秒")
            
            # 在文档末尾添加 3 个空行和"*** End of Report ***"段落
            step8_start = time.time()
            target_range = template_doc.Range()
            target_range.Collapse(0)  # wdCollapseEnd = 0
            
            # 添加 3 个空行
            target_range.Text = "\n\n\n"
                
            # 添加"*** End of Report ***"段落并设置格式
            end_marker_range = template_doc.Range()
            end_marker_range.Collapse(0)  # wdCollapseEnd = 0
            end_marker_range.Text = "*** End of Report ***\n"
                
            # 设置格式：Times New Roman 字体、小四字号、加粗、倾斜、居中
            end_marker_range.Font.Name = "Times New Roman"
            end_marker_range.Font.Size = 12  # 小四对应 12 磅
            end_marker_range.Font.Bold = True
            end_marker_range.Font.Italic = True
            end_marker_range.ParagraphFormat.Alignment = 1  # 1 表示居中对齐
            step8_end = time.time()
            logger.debug(f"[PERF] 步骤 8 - 添加报告结束标记完成，耗时：{step8_end - step8_start:.2f}秒")
                
            total_end = time.time()
            logger.debug(f"[PERF] 从'1. PURPOSE'到'7. EQUIPMENTS'的内容复制完成（含修订记录），总耗时：{total_end - total_start:.2f}秒")
            return True
        except Exception as e:
            logger.error(f"复制内容时出错：{e}")
            import traceback
            logger.error(traceback.format_exc())
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
            import time
            start_time = time.time()
            logger.debug(f"[PERF] 开始插入内容到文档末尾，内容范围：Start={content_range.Start}, End={content_range.End}, 长度={content_range.End - content_range.Start}")
                
            # 定位到目标文档末尾
            target_range = template_doc.Range()
            target_range.Collapse(0)  # wdCollapseEnd = 0
            step1_time = time.time()
            logger.debug(f"[PERF] 步骤 1 - 定位文档末尾完成，耗时：{step1_time - start_time:.2f}秒")
                
            # 使用 FormattedText 属性复制格式（这是原始实现）
            target_range.FormattedText = content_range.FormattedText
            end_time = time.time()
            logger.debug(f"[PERF] 步骤 2 - FormattedText 赋值完成，耗时：{end_time - step1_time:.2f}秒")
            logger.debug(f"[PERF] 内容已插入到文档末尾，总耗时：{end_time - start_time:.2f}秒")
        except Exception as e:
            logger.error(f"插入内容到文档末尾时出错：{e}")
            raise