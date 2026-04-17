"""
正文内容填充服务模块
提供Word文档正文内容查找和填充的核心功能
"""

import os
import json
from typing import Dict, List, Optional, Tuple
import win32com.client
import pythoncom
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from src.core.logger import logger
from src.utils.word_utils import get_shared_word_app, release_word_app


class BodyContentService:
    """
    正文内容填充服务类
    提供Word文档正文内容查找和填充的核心功能
    """

    def __init__(self):
        """初始化正文内容填充服务"""
        self.predefined_descriptions = self._load_predefined_descriptions()
        self.word_app = None
        
        # 确保Word应用程序在后台运行
        self._ensure_word_app_background_mode()

    def _load_predefined_descriptions(self) -> Dict[str, List[str]]:
        """
        加载预定义描述内容

        Returns:
            预定义描述内容字典
        """
        # 默认预定义描述
        default_descriptions = {
            "PURPOSE": [
                "The purpose of this test is to verify the functionality and reliability of the sample under test conditions.",
                "This test is conducted to evaluate the performance characteristics of the submitted sample.",
                "The objective of this testing is to confirm compliance with specified requirements."
            ],
            "CONCLUSIONS": [
                "The sample has passed all required tests and meets the specified criteria.",
                "The sample has failed to meet the specified requirements and is not acceptable.",
                "The sample requires additional testing to confirm compliance with specifications."
            ],
            "SAMPLE DESCRIPTION": [
                "The sample provided is a standard electronic component with typical characteristics.",
                "The sample is a prototype unit requiring comprehensive evaluation.",
                "The sample represents a production unit for quality verification purposes."
            ]
        }

        # 尝试从配置文件加载预定义描述（兼容打包模式）
        from src.core.path_utils import get_resource_path
        config_path = get_resource_path(
            "content_editor_service", "body_content_config.json"
        )
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置，避免重复
                    for key, value in user_config.items():
                        if key in default_descriptions:
                            # 只添加不在默认列表中的描述
                            for desc in value:
                                if desc not in default_descriptions[key]:
                                    default_descriptions[key].append(desc)
                        else:
                            default_descriptions[key] = value
            except Exception as e:
                logger.warning(f"加载预定义描述配置失败: {e}")

        return default_descriptions

    def _find_all_section_headers(self, doc, target_sections=None):
        """
        在文档中查找所有指定的章节标题
        
        Args:
            doc: Document对象
            target_sections: 要查找的目标章节列表，如果为None则使用默认章节
            
        Returns:
            包含找到的段落信息的字典
        """
        if target_sections is None:
            target_sections = ["PURPOSE", "CONCLUSIONS", "SAMPLE DESCRIPTION"]
        
        found_paragraphs = {section: [] for section in target_sections}
        
        # 遍历文档段落
        for i, paragraph in enumerate(doc.paragraphs):
            para_text = paragraph.text.strip()
            if not para_text:
                continue

            # 检查是否匹配特定段落标题
            para_upper = para_text.upper()
            for key in found_paragraphs.keys():
                if self._is_matching_section_header(para_upper, key) and self._is_paragraph_bold(paragraph):
                    logger.info(f"找到段落 {key} 在段落 {i}，原始文本: '{para_text}'")
                    found_paragraphs[key].append({
                        "index": i,
                        "text": para_text,
                        "bold": self._is_paragraph_bold(paragraph),
                        "element": paragraph._element,
                        "type": "paragraph"
                    })

        # 查找表格中的内容
        for table in doc.tables:
            for i, row in enumerate(table.rows):
                for j, cell in enumerate(row.cells):
                    for k, paragraph in enumerate(cell.paragraphs):
                        para_text = paragraph.text.strip()
                        if not para_text:
                            continue

                        # 检查是否匹配特定段落标题
                        para_upper = para_text.upper()
                        for key in found_paragraphs.keys():
                            if self._is_matching_section_header(para_upper, key) and self._is_paragraph_bold(paragraph):
                                logger.info(f"找到表格中的段落 {key} 在表格 {doc.tables.index(table)} 单元格 ({i}, {j}) 段落 {k}，原始文本: '{para_text}'")
                                found_paragraphs[key].append({
                                    "index": (i, j, k),  # 表格位置
                                    "text": para_text,
                                    "bold": self._is_paragraph_bold(paragraph),
                                    "element": paragraph._element,
                                    "type": "table",
                                    "table_index": doc.tables.index(table),
                                    "cell_index": (i, j)
                                })
        
        return found_paragraphs

    def find_body_paragraphs(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        查找文档中的特定段落

        Args:
            file_path: Word文档路径

        Returns:
            包含找到的段落信息的字典
        """
        try:
            # 使用python-docx打开文档进行段落查找
            doc = Document(file_path)
            
            found_paragraphs = self._find_all_section_headers(doc)
            
            logger.info(f"在文档中找到段落: {found_paragraphs}")
            return found_paragraphs

        except Exception as e:
            logger.error(f"查找文档段落时出错: {e}")
            return {"PURPOSE": [], "CONCLUSIONS": [], "SAMPLE DESCRIPTION": []}

    def _is_paragraph_bold(self, paragraph) -> bool:
        """
        检查段落是否为粗体

        Args:
            paragraph: docx段落对象

        Returns:
            段落是否为粗体
        """
        try:
            # 检查段落中的所有run对象是否有粗体属性
            for run in paragraph.runs:
                if run.bold:
                    return True
            # 如果段落没有runs，检查段落的样式是否为粗体
            if hasattr(paragraph, 'style') and paragraph.style and hasattr(paragraph.style, 'bold'):
                return paragraph.style.bold
        except:
            pass
        return False

    def _is_matching_section_header(self, para_text: str, target_section: str) -> bool:
        """
        检查段落文本是否匹配目标章节标题，支持数字前缀和后缀空格
        
        Args:
            para_text: 段落文本（已转换为大写）
            target_section: 目标章节标题
            
        Returns:
            是否匹配
        """
        import re
        
        # 移除段落文本前的数字前缀（只支持单级数字，如 '1.'）
        # 匹配格式如 '1.' 等
        cleaned_text = re.sub(r'^\s*\d+\.?', '', para_text).strip()
        
        logger.debug(f"匹配章节标题: 原始文本='{para_text}', 清理后文本='{cleaned_text}', 目标='{target_section}'")
        
        # 检查清理后的文本是否完全匹配目标章节标题
        return cleaned_text == target_section

    def _find_section_positions(self, doc, target_sections: List[str]) -> Dict[str, int]:
        """
        在文档中一次性查找所有目标章节的位置
        
        Args:
            doc: Document对象
            target_sections: 要查找的目标章节列表
            
        Returns:
            包含章节名和位置的字典
        """
        section_positions = {}
        
        for i, paragraph in enumerate(doc.paragraphs):
            para_text = paragraph.text.strip().upper()
            logger.debug(f"检查段落 {i}: '{para_text}'")
            
            # 检查是否匹配任何目标章节
            for section in target_sections:
                if self._is_matching_section_header(para_text, section):
                    # 如果需要粗体检查且段落是粗体，或不需要粗体检查
                    if (section in ["PURPOSE", "CONCLUSIONS", "SAMPLE DESCRIPTION"] and self._is_paragraph_bold(paragraph)) or \
                       section not in ["PURPOSE", "CONCLUSIONS", "SAMPLE DESCRIPTION"]:  # 如果不是标准章节，不需要粗体检查
                        logger.info(f"找到章节 {section} 在段落 {i}，原始文本: '{paragraph.text.strip()}'")
                        if section not in section_positions:  # 只记录第一次出现的位置
                            section_positions[section] = i
            
            # 如果所有目标章节都已找到，提前结束遍历
            if len(section_positions) == len(target_sections):
                logger.info(f"已找到所有 {len(target_sections)} 个目标章节，提前结束遍历")
                break
        
        return section_positions

    def extract_content_between_sections(self, file_path: str, start_section: str, end_section: str) -> str:
        """
        提取两个章节之间的内容

        Args:
            file_path: Word文档路径
            start_section: 起始章节标题
            end_section: 结束章节标题

        Returns:
            两个章节之间的内容
        """
        try:
            logger.info(f"开始提取文档 {file_path} 中 {start_section} 到 {end_section} 之间的内容")
            doc = Document(file_path)
            
            # 一次性查找所有需要的章节位置
            all_sections = [start_section]
            if end_section:
                all_sections.append(end_section)
            
            section_positions = self._find_section_positions(doc, all_sections)
            
            start_index = section_positions.get(start_section, -1)
            end_index = section_positions.get(end_section, -1)
            
            if start_index == -1:
                logger.warning(f"未找到起始章节: {start_section}")
                return ""
            
            if end_section and end_index == -1:
                # 如果没有找到结束章节且不为空，则提取到文档末尾
                # 特别处理：如果提取的是CONCLUSIONS之后的内容且没有找到SAMPLE DESCRIPTION，则在遇到表格时停止
                if end_section == "SAMPLE DESCRIPTION":
                    logger.warning(f"未找到结束章节: {end_section}，将提取到文档末尾或遇到表格时停止")
                    end_index = len(doc.paragraphs)
                    # 检查起始章节之后的内容，如果遇到表格则停止
                    for i in range(start_index + 1, len(doc.paragraphs)):
                        paragraph = doc.paragraphs[i]
                        # 检查当前段落是否在表格中
                        if hasattr(paragraph, '_element'):
                            # 检查段落的父元素是否为表格单元格
                            parent = paragraph._element.getparent()
                            while parent is not None:
                                if parent.tag.endswith('tc'):  # tc = table cell
                                    logger.info(f"在段落 {i} 处遇到表格，停止提取")
                                    end_index = i
                                    break
                                # 检查是否直接是表格元素
                                if parent.tag.endswith('tbl'):  # tbl = table
                                    logger.info(f"在段落 {i} 处遇到表格，停止提取")
                                    end_index = i
                                    break
                                parent = parent.getparent()
                        if end_index != len(doc.paragraphs):
                            break
                else:
                    logger.warning(f"未找到结束章节: {end_section}，将提取到文档末尾")
                    end_index = len(doc.paragraphs)
            
            logger.info(f"提取范围: 从段落 {start_index} 到段落 {end_index}")
            
            # 提取两个章节之间的内容
            content = []
            for i in range(start_index + 1, end_index):
                para_text = doc.paragraphs[i].text
                logger.debug(f"提取段落 {i}: '{para_text[:50]}...'")
                if para_text.strip():  # 只添加非空段落
                    content.append(para_text)
            
            result = "\n".join(content)
            logger.info(f"成功提取内容，总长度: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"提取章节间内容时出错: {e}")
            return ""

    def _find_section_paragraph_win32com(self, doc, section_name: str):
        """
        在使用win32com的文档中查找指定章节
        
        Args:
            doc: win32com文档对象
            section_name: 要查找的章节名称
            
        Returns:
            找到的段落对象，如果未找到返回None
        """
        for para in doc.Paragraphs:
            para_text = para.Range.Text.strip().upper()
            if self._is_matching_section_header(para_text, section_name):
                logger.info(f"找到章节: {section_name}，原始文本: '{para.Range.Text.strip()}'")
                return para
        return None

    def _update_single_section_content(self, doc, start_index: int, end_index: int, new_content: str, is_end_of_doc: bool = False) -> bool:
        """
        更新文档中指定范围的内容
        
        Args:
            doc: Document对象
            start_index: 起始段落索引
            end_index: 结束段落索引
            new_content: 新内容
            is_end_of_doc: 是否是到文档末尾的更新
            
        Returns:
            是否成功更新
        """
        try:
            if start_index + 1 < len(doc.paragraphs):
                if is_end_of_doc:
                    # 如果是到文档末尾的更新，删除从起始段落后的所有段落，然后添加新内容
                    # 删除从start_index+1开始的所有段落
                    for i in range(len(doc.paragraphs) - 1, start_index + 1, -1):  # 反向删除避免索引问题
                        p = doc.paragraphs[i]._element
                        p.getparent().remove(p)
                    
                    # 更新紧跟在起始段落后的段落内容
                    doc.paragraphs[start_index + 1].text = new_content
                else:
                    # 用新内容替换第一个段落，删除其余段落
                    doc.paragraphs[start_index + 1].text = new_content
                    
                    # 删除多余的段落
                    for i in range(end_index - 1, start_index + 1, -1):  # 反向删除避免索引问题
                        if i < len(doc.paragraphs):
                            p = doc.paragraphs[i]._element
                            p.getparent().remove(p)
                
                return True
            return False
        except Exception as e:
            logger.error(f"更新单个章节内容时出错: {e}")
            return False
    
    def update_multiple_sections_content(self, file_path: str, updates: Dict[str, str]) -> bool:
        """
        一次性更新多个章节间的内容
        
        Args:
            file_path: Word文档路径
            updates: 包含章节范围和新内容的字典，格式为{"START-END": "new_content"} 或 {"START-END": "new_content", "START-END": "new_content"}
            
        Returns:
            是否成功更新
        """
        try:
            logger.info(f"开始批量更新文档 {file_path} 中的多个章节内容")
            
            # 获取所有需要更新的章节名称
            target_sections = set()
            section_pairs = []
            
            for section_range in updates.keys():
                if "-" in section_range:
                    start_section, end_section = section_range.split("-", 1)
                    # 如果end_section是"END"，表示到文档末尾
                    if end_section == "END":
                        target_sections.add(start_section)
                        section_pairs.append((start_section, "END", updates[section_range], True))
                    else:
                        target_sections.add(start_section)
                        target_sections.add(end_section)
                        section_pairs.append((start_section, end_section, updates[section_range], False))
            
            # 使用python-docx打开文档
            doc = Document(file_path)
            
            # 一次性查找所有需要的章节位置
            section_positions = self._find_section_positions(doc, list(target_sections))
            
            # 按照倒序排列段落索引，确保删除段落时不会影响后续操作的索引
            updates_with_positions = []
            for start_section, end_section, new_content, is_end in section_pairs:
                start_index = section_positions.get(start_section, -1)
                
                if start_index == -1:
                    logger.warning(f"未找到起始章节: {start_section}")
                    continue
                
                if is_end:
                    # 特殊处理：到文档末尾的更新
                    end_index = len(doc.paragraphs)  # 到文档末尾
                    updates_with_positions.append((start_index, end_index, new_content, True))
                else:
                    end_index = section_positions.get(end_section, -1)
                    if end_index == -1:
                        logger.warning(f"未找到结束章节: {end_section}")
                        continue
                    updates_with_positions.append((start_index, end_index, new_content, False))
            
            # 按起始索引倒序排列，以避免删除段落时影响后续操作
            updates_with_positions.sort(key=lambda x: x[0], reverse=True)
            
            # 执行更新
            for start_index, end_index, new_content, is_end in updates_with_positions:
                if not self._update_single_section_content(doc, start_index, end_index, new_content, is_end):
                    logger.error(f"更新章节内容失败: 从索引 {start_index} 到 {end_index}")
                    return False
            
            # 保存文档
            doc.save(file_path)
            logger.info(f"成功批量更新了 {len(updates_with_positions)} 个章节的内容")
            return True

        except Exception as e:
            logger.error(f"批量更新章节内容时出错: {e}")
            return False
    
    def update_content_between_sections(self, file_path: str, start_section: str, end_section: str, new_content: str) -> bool:
        """
        更新两个章节之间的内容

        Args:
            file_path: Word文档路径
            start_section: 起始章节标题
            end_section: 结束章节标题
            new_content: 新的内容

        Returns:
            是否成功更新
        """
        try:
            logger.info(f"开始更新文档 {file_path} 中 {start_section} 到 {end_section} 之间的内容")
            logger.info(f"新内容长度: {len(new_content)}, 内容预览: {new_content[:100] if len(new_content) > 0 else 'Empty'}")
            
            # 调用批量更新方法，只更新一个章节对
            updates = {f"{start_section}-{end_section}": new_content}
            return self.update_multiple_sections_content(file_path, updates)

        except Exception as e:
            logger.error(f"更新章节间内容时出错: {e}")
            return False

    def get_predefined_descriptions(self, category: str) -> List[str]:
        """
        获取预定义描述内容

        Args:
            category: 描述类别

        Returns:
            预定义描述内容列表
        """
        return self.predefined_descriptions.get(category, [])

    def add_predefined_description(self, category: str, description: str) -> bool:
        """
        添加预定义描述内容

        Args:
            category: 描述类别
            description: 描述内容

        Returns:
            是否成功添加
        """
        try:
            if category not in self.predefined_descriptions:
                self.predefined_descriptions[category] = []
            
            if description not in self.predefined_descriptions[category]:
                self.predefined_descriptions[category].append(description)
                logger.info(f"添加预定义描述: {category} -> {description}")
                return True
            return False
        except Exception as e:
            logger.error(f"添加预定义描述时出错: {e}")
            return False

    def update_paragraph_after_keyword(self, file_path: str, keyword: str, new_content: str) -> bool:
        """
        在文档中查找关键词，并更新其后的段落内容

        Args:
            file_path: Word文档路径
            keyword: 要查找的关键词
            new_content: 新的内容

        Returns:
            是否成功更新
        """
        doc = None
        try:
            # 使用win32com.client进行精确操作
            word_app = get_shared_word_app()
            if not word_app:
                logger.error("无法获取Word应用程序实例")
                return False

            # 确保Word应用程序不可见
            word_app.Visible = False
            word_app.DisplayAlerts = False

            doc = word_app.Documents.Open(file_path)
            found = False

            # 遍历所有段落查找关键词
            for para in doc.Paragraphs:
                para_text = para.Range.Text.strip()
                if keyword.upper() in para_text.upper():
                    # 找到关键词后，更新下一个段落的内容
                    next_para = self._find_next_paragraph(word_app, para)
                    if next_para:
                        next_para.Range.Text = new_content
                        found = True
                        logger.info(f"成功更新 {keyword} 后的段落内容")
                        break  # 只更新第一个匹配项

            if found:
                doc.Save()

            # 关闭文档
            doc.Close()
            doc = None

            return found

        except Exception as e:
            logger.error(f"更新关键词后段落时出错: {e}")
            return False
        finally:
            # 共享 Word 实例由 word_utils 管理；此处仅确保本方法打开的文档被关闭
            if doc is not None:
                try:
                    doc.Close(SaveChanges=False)
                except Exception:
                    pass
            # 与本方法内的 get_shared_word_app() 成对，避免引用计数泄漏
            try:
                release_word_app()
            except Exception:
                pass

    def _find_next_paragraph(self, word_app, current_paragraph) -> Optional:
        """
        查找下一个段落

        Args:
            word_app: Word应用程序对象
            current_paragraph: 当前段落对象

        Returns:
            下一个段落对象，如果不存在则返回None
        """
        try:
            # 获取当前段落在文档中的位置
            current_pos = current_paragraph.Range.End
            
            # 遍历后续段落
            for para in word_app.ActiveDocument.Paragraphs:
                if para.Range.Start > current_pos:
                    return para
        except Exception as e:
            logger.error(f"查找下一个段落时出错: {e}")
        return None
    
    def _ensure_word_app_background_mode(self):
        """
        确保Word应用程序在后台运行
        """
        try:
            self.word_app = get_shared_word_app()
            if self.word_app:
                self.word_app.Visible = False
                self.word_app.DisplayAlerts = False
        except Exception as e:
            logger.error(f"设置Word应用程序后台模式时出错: {e}")
    
    def __del__(self):
        """
        释放对共享 Word 实例的引用。

        不在此调用 Quit：word_app 来自 get_shared_word_app() 的全局单例，
        退出进程时由 cleanup_word_resources() 统一清理；若在析构时重复 Quit，
        COM 可能已断开，会触发 RPC 断开错误。
        """
        try:
            release_word_app()
        except Exception:
            pass

    def get_all_content_sections(self, file_path: str) -> Dict[str, str]:
        """
        获取文档中所有目标章节间的内容

        Args:
            file_path: Word文档路径

        Returns:
            包含各章节间内容的字典
        """
        try:
            logger.info(f"开始提取文档 {file_path} 中的所有目标章节内容")
            doc = Document(file_path)
            
            # 一次性查找所有目标章节位置
            target_sections = ["PURPOSE", "CONCLUSIONS", "SAMPLE DESCRIPTION"]
            section_positions = self._find_section_positions(doc, target_sections)
            
            logger.info(f"找到章节位置: {section_positions}")
            
            sections_content = {}
            
            # 获取 PURPOSE 到 CONCLUSIONS 的内容
            if "PURPOSE" in section_positions and "CONCLUSIONS" in section_positions:
                purpose_pos = section_positions["PURPOSE"]
                conclusions_pos = section_positions["CONCLUSIONS"]
                
                content = []
                for i in range(purpose_pos + 1, conclusions_pos):
                    para_text = doc.paragraphs[i].text
                    logger.debug(f"提取段落 {i}: '{para_text[:50]}...'")
                    if para_text.strip():  # 只添加非空段落
                        content.append(para_text)
                
                if content:
                    result = "\n".join(content)
                    logger.info(f"PURPOSE-CONCLUSIONS内容长度: {len(result)}")
                    sections_content["PURPOSE-CONCLUSIONS"] = result
            
            # 获取 CONCLUSIONS 到 SAMPLE DESCRIPTION 的内容
            if "CONCLUSIONS" in section_positions and "SAMPLE DESCRIPTION" in section_positions:
                conclusions_pos = section_positions["CONCLUSIONS"]
                sample_desc_pos = section_positions["SAMPLE DESCRIPTION"]
                
                content = []
                for i in range(conclusions_pos + 1, sample_desc_pos):
                    para_text = doc.paragraphs[i].text
                    logger.debug(f"提取段落 {i}: '{para_text[:50]}...'")
                    if para_text.strip():  # 只添加非空段落
                        content.append(para_text)
                
                if content:
                    result = "\n".join(content)
                    logger.info(f"CONCLUSIONS-SAMPLE DESCRIPTION内容长度: {len(result)}")
                    sections_content["CONCLUSIONS-SAMPLE DESCRIPTION"] = result
            
            # 如果没有 SAMPLE DESCRIPTION，获取 CONCLUSIONS 之后的所有内容
            elif "CONCLUSIONS" in section_positions:
                conclusions_pos = section_positions["CONCLUSIONS"]
                
                content = []
                end_index = len(doc.paragraphs)
                
                # 特别处理：如果没有找到SAMPLE DESCRIPTION，碰到表格就截止
                for i in range(conclusions_pos + 1, len(doc.paragraphs)):
                    paragraph = doc.paragraphs[i]
                    # 检查当前段落是否在表格中
                    if hasattr(paragraph, '_element'):
                        # 检查段落的父元素是否为表格单元格
                        parent = paragraph._element.getparent()
                        while parent is not None:
                            if parent.tag.endswith('tc'):  # tc = table cell
                                logger.info(f"在段落 {i} 处遇到表格，停止提取")
                                end_index = i
                                break
                            # 检查是否直接是表格元素
                            if parent.tag.endswith('tbl'):  # tbl = table
                                logger.info(f"在段落 {i} 处遇到表格，停止提取")
                                end_index = i
                                break
                            parent = parent.getparent()
                    if end_index != len(doc.paragraphs):
                        break
                
                for i in range(conclusions_pos + 1, end_index):
                    para_text = doc.paragraphs[i].text
                    logger.debug(f"提取段落 {i}: '{para_text[:50]}...'")
                    if para_text.strip():  # 只添加非空段落
                        content.append(para_text)
                
                if content:
                    result = "\n".join(content)
                    logger.info(f"CONCLUSIONS-END内容长度: {len(result)}")
                    sections_content["CONCLUSIONS-END"] = result
            
            return sections_content
            
        except Exception as e:
            logger.error(f"提取所有章节内容时出错: {e}")
            return {}