"""
正文内容填充服务模块
提供Word文档正文内容查找和填充的核心功能
"""

import os
import json
from typing import Dict, List, Optional
from src.core.logger import logger
from src.infrastructure.office.facade import OfficeFacade
from .section_discovery_service import SectionDiscoveryService
from .section_update_service import SectionUpdateService


class BodyContentService:
    """
    正文内容填充服务类
    提供Word文档正文内容查找和填充的核心功能

    内部委托：
    - 章节发现/提取 → SectionDiscoveryService
    - 章节更新（python-docx）→ SectionUpdateService
    """

    def __init__(self, office_facade: OfficeFacade | None = None):
        """初始化正文内容填充服务"""
        self._section_discovery = SectionDiscoveryService()
        self._section_update = SectionUpdateService(self._section_discovery)
        self.predefined_descriptions = self._load_predefined_descriptions()
        self._office_facade = office_facade

    # --- 公共 API：章节发现（委托到 SectionDiscoveryService）---

    def find_body_paragraphs(self, file_path: str) -> Dict[str, List[Dict]]:
        """查找文档中的特定段落"""
        return self._section_discovery.find_body_paragraphs(file_path)

    def extract_content_between_sections(self, file_path: str, start_section: str, end_section: str) -> str:
        """提取两个章节之间的内容"""
        return self._section_discovery.extract_content_between_sections(file_path, start_section, end_section)

    def get_all_content_sections(self, file_path: str) -> Dict[str, str]:
        """获取文档中所有目标章节间的内容"""
        return self._section_discovery.get_all_content_sections(file_path)

    # --- 公共 API：章节更新（委托到 SectionUpdateService）---

    def update_multiple_sections_content(self, file_path: str, updates: Dict[str, str]) -> bool:
        """一次性更新多个章节间的内容"""
        return self._section_update.update_multiple_sections_content(file_path, updates)

    def update_content_between_sections(self, file_path: str, start_section: str, end_section: str, new_content: str) -> bool:
        """更新两个章节之间的内容"""
        return self._section_update.update_content_between_sections(file_path, start_section, end_section, new_content)

    # --- 公共 API：win32com 关键词段落更新路径 ---

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
        word_session = None
        doc = None
        try:
            # 使用 Word COM 进行精确操作
            word_session = self._get_office_facade().create_session("word")
            word_handle = word_session.acquire()
            word_app = word_handle.application
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
            if doc is not None:
                try:
                    doc.Close(SaveChanges=False)
                except Exception:
                    pass
            if word_session is not None:
                word_session.release()

    # --- 公共 API：预定义描述 ---

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

    # --- 内部方法 ---

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
            if self._section_discovery._is_matching_section_header(para_text, section_name):
                logger.info(f"找到章节: {section_name}，原始文本: '{para.Range.Text.strip()}'")
                return para
        return None

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

    def _get_office_facade(self) -> OfficeFacade:
        if self._office_facade is None:
            self._office_facade = OfficeFacade()
        return self._office_facade
