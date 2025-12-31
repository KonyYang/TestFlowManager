"""
页眉处理模块
处理Word文档的页眉信息
"""

from src.core.logger import logger


class HeaderProcessor:
    """
    页眉处理器
    负责处理Word文档的页眉信息
    """
    
    @staticmethod
    def modify_header(source_doc, template_doc):
        """
        修改页眉信息
        
        Args:
            source_doc: 源文档对象
            template_doc: 模板文档对象
            
        Returns:
            bool: 是否成功修改页眉
        """
        try:
            # 获取源文档首页页眉表格
            logger.debug(f"源文档段落数: {source_doc.Paragraphs.Count}")
            logger.debug(f"源文档节段数: {source_doc.Sections.Count}")
            
            # 检查第一节是否存在
            if source_doc.Sections.Count < 1:
                logger.error("源文档没有节段")
                return False
                
            source_section = source_doc.Sections(1)
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
            logger.debug(f"模板文档段落数: {template_doc.Paragraphs.Count}")
            logger.debug(f"模板文档节段数: {template_doc.Sections.Count}")
            
            # 检查第一节是否存在
            if template_doc.Sections.Count < 1:
                logger.error("模板文档没有节段")
                return False
                
            template_section = template_doc.Sections(1)
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
            
            # 检查是否包含版本号（Rev.X格式）
            import re
            rev_match = re.search(r" Rev\.([A-Z]+)$", report_no_content)
            
            if rev_match:
                # 提取基础报告编号和版本号
                base_report_no = report_no_content[:rev_match.start()]
                version = rev_match.group(0)  # 包含空格的完整版本号，如" Rev.B"
                # 组合为新的报告编号格式
                new_report_no = base_report_no + "-CR" + version
            else:
                # 没有版本号的普通情况
                new_report_no = report_no_content + "-CR"
            
            # 填充模板页眉表格
            # 第3行第1列：处理后的报告编号
            template_header_table.Cell(3, 1).Range.Text = new_report_no
            logger.debug(f"已设置模板表格第3行第1列内容: {new_report_no}")
            
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
            logger.debug(f"模板文档节段数: {template_doc.Sections.Count}")
            if template_doc.Sections.Count >= 2:
                # 参考 fill_second_header_win32 方法，使用主要页眉 (wdHeaderFooterPrimary = 1)
                try:
                    second_section = template_doc.Sections(2)
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
                    cleaned_report_no = report_no_content.replace("\r", "").replace("\x07", "").strip()
                    
                    # 检查是否包含版本号（Rev.X格式）
                    import re
                    rev_match = re.search(r" Rev\.([A-Z]+)$", cleaned_report_no)
                    
                    if rev_match:
                        # 提取基础报告编号和版本号
                        base_report_no = cleaned_report_no[:rev_match.start()]
                        version = rev_match.group(0)  # 包含空格的完整版本号，如" Rev.B"
                        # 组合为新的报告编号格式
                        new_report_no = base_report_no + "-CR" + version
                    else:
                        # 没有版本号的普通情况
                        new_report_no = cleaned_report_no + "-CR"
                    
                    # 创建新范围，从 "Report No." 后开始
                    new_range = cell_range.Duplicate
                    report_no_end_pos = report_no_pos + len("Report No.")
                    new_range.Start = cell_range.Start + report_no_end_pos
                    new_range.End = cell_range.End - 1  # 去掉最后的 \x07（Word 的段落标记）
                    
                    # 替换为新的报告编号
                    new_range.Text = new_report_no
                    logger.debug(f"已在第二节页眉中将 'Report No.' 更新为: '{new_report_no}'")
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