"""
Word文档解析器
从Word文件中提取表格数据
"""

from src.core.logger import logger
from typing import List, Dict, Optional, Any
import os
import re


class WordParser:
    """
    Word文档解析器
    支持解析.doc和.docx格式的Word文档中的表格数据
    """

    def __init__(self, office_facade=None):
        """
        初始化Word解析器

        Args:
            office_facade: OfficeFacade实例（.doc格式解析必需）
        """
        self._office_facade = office_facade

    def parse(self, file_path: str, page_number=None, keyword=None):
        """
        解析Word文档并提取表格数据

        Args:
            file_path: Word文档路径
            page_number: 指定页码（从1开始）
            keyword: 关键字筛选

        Returns:
            解析出的表格数据列表
        """
        # 检查文件扩展名以决定使用哪种解析方法
        if file_path.lower().endswith('.doc'):
            # 对于.doc文件，使用COM接口
            if self._office_facade is None:
                from src.infrastructure.office import OfficeFacade
                self._office_facade = OfficeFacade()
            from .word_com_parser import WordCOMParser
            parser = WordCOMParser(self._office_facade)
            return parser.parse(file_path, page_number, keyword)
        elif file_path.lower().endswith('.docx'):
            # 对于.docx文件，使用python-docx库
            from .word_docx_parser import WordDocxParser
            parser = WordDocxParser()
            return parser.parse(file_path, page_number, keyword)
        else:
            raise ValueError(f"不支持的Word文件格式: {file_path}")

    def find_test_method_in_spec(self, doc, chapter_number: str) -> Optional[str]:
        """
        在规格书中查找测试方法标准
        
        Args:
            doc: Word文档对象
            chapter_number: 章节编号（如"3.1"）
            
        Returns:
            测试方法标准（如"EIA-364-18B"）或None
        """
        try:
            logger.info(f"开始在规格书中查找测试方法，章节号: {chapter_number}")
            
            # 使用新的工具模块查找测试标准
            from src.utils.test_standard_utils import find_test_standard_by_chapter
            test_method = find_test_standard_by_chapter(doc, chapter_number)
            
            if test_method:
                logger.info(f"成功找到测试方法: {test_method}")
                return test_method
            else:
                logger.warning(f"未找到章节 {chapter_number} 对应的测试方法")
                return None
                
        except Exception as e:
            logger.error(f"查找测试方法时出错: {e}", exc_info=True)
            return None
