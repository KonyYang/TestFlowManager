"""
格式处理模块
处理Word文档的格式化功能
"""

from src.core.logger import logger


class FormatProcessor:
    """
    格式处理器
    负责处理Word文档的格式化功能
    """
    
    @staticmethod
    def remove_number_and_dot_in_formatted_paragraphs(template_doc):
        """
        清理章节标题格式（去除数字和点）
        """
        try:
            # 遍历模板文档中的每个段落
            for i in range(1, template_doc.Paragraphs.Count + 1):
                paragraph = template_doc.Paragraphs(i)
                paragraph_range = paragraph.Range
                
                # 检查段落是否为粗体且带单下划线
                if (paragraph_range.Font.Bold and 
                    paragraph_range.Font.Underline == 1):  # wdUnderlineSingle = 1
                    
                    para_text = paragraph_range.Text
                    
                    # 检查段落是否以数字和"."开头
                    if len(para_text) >= 2 and para_text[0].isdigit() and para_text[1] == '.':
                        # 删除前两个字符
                        new_start = paragraph_range.Start + 2
                        remove_range = template_doc.Range(paragraph_range.Start, new_start)
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

    @staticmethod
    def move_and_format_text(template_doc):
        """
        移动并格式化特定文本
        """
        try:
            # 定义要查找的文本
            search_text = "The results of testing only apply to the sample"
            target_text = "Unless otherwise specified, assessment of conformity to requirements is based on simple acceptance."
            
            # 查找源文本
            source_range = template_doc.Content
            find_source = source_range.Find
            find_source.Text = search_text
            find_source.Forward = True
            find_source.Wrap = 1  # wdFindStop = 1
            found_source = find_source.Execute()
            
            # 查找目标位置文本
            target_range = template_doc.Content
            find_target = target_range.Find
            find_target.Text = target_text
            find_target.Forward = True
            find_target.Wrap = 1  # wdFindStop = 1
            found_target = find_target.Execute()
            
            if not found_source and not found_target:
                # 如果两个文本都没找到，添加组合文本到文档末尾
                logger.info(f"未找到源文本和目标文本，添加组合文本到文档末尾")
                combined_text = target_text + " " + search_text + "s as received in the laboratory."
                
                paste_range = template_doc.Range()
                paste_range.Collapse(0)  # wdCollapseEnd = 0
                paste_range.Text = combined_text + "\n"
                
                # 设置格式：粗体、字体 Arial，大小 10
                paste_range.Font.Bold = True
                paste_range.Font.Name = "Arial"
                paste_range.Font.Size = 10
            elif not found_source and found_target:
                # 如果只找到目标文本但没找到源文本，将源文本追加到目标文本后面
                logger.info(f"只找到目标文本，追加源文本到目标文本后")
                combined_text = " " + search_text + "s as received in the laboratory."
                
                # 在目标文本后添加内容
                target_range.Collapse(0)  # wdCollapseEnd = 0
                target_range.Text = combined_text
                
                # 设置格式：粗体、字体 Arial，大小 10
                target_range.Font.Bold = True
                target_range.Font.Name = "Arial"
                target_range.Font.Size = 10
            elif found_source and found_target:
                # 如果两个文本都找到了，按原逻辑移动文本
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
                
                # 在目标文本后粘贴剪切的内容
                paste_range = target_range.Duplicate
                paste_range.Collapse(0)  # wdCollapseEnd = 0
                paste_range.Paste()
                
                # 设置格式：粗体、字体 Arial，大小 10
                paste_range.Font.Bold = True
                paste_range.Font.Name = "Arial"
                paste_range.Font.Size = 10
            elif found_source and not found_target:
                # 如果只找到源文本但没找到目标文本，在文档末尾添加目标文本和源文本
                logger.info(f"只找到源文本，添加目标文本和源文本到文档末尾")
                
                # 先提取源文本范围
                text_to_move_range = source_range.Duplicate
                text_to_move_range.End = text_to_move_range.Start
                while text_to_move_range.Characters.Last.Text != ".":
                    text_to_move_range.MoveEnd(1, 1)
                    # 防止无限循环
                    if text_to_move_range.End - text_to_move_range.Start > 1000:
                        break
                
                # 剪切源文本
                text_to_move_range.Cut()
                
                # 添加目标文本到文档末尾
                paste_range = template_doc.Range()
                paste_range.Collapse(0)  # wdCollapseEnd = 0
                paste_range.Text = target_text + " "
                
                # 在目标文本后粘贴源文本
                paste_range.Collapse(0)  # wdCollapseEnd = 0
                paste_range.Paste()
                
                # 添加补充文字
                paste_range.Text = "s as received in the laboratory.\n"
                
                # 设置格式：粗体、字体 Arial，大小 10
                paste_range.Font.Bold = True
                paste_range.Font.Name = "Arial"
                paste_range.Font.Size = 10
            
            logger.debug("文本移动和格式化完成")
            return True
        except Exception as e:
            logger.error(f"移动和格式化文本时出错: {e}")
            return False