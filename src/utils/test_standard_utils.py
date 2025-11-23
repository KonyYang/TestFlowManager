"""
测试标准工具模块
提供测试标准识别和提取的通用功能
"""

import re
from typing import Optional, List, Dict
from src.core.logger import logger


class TestStandardExtractor:
    """测试标准提取器"""
    
    def __init__(self):
        """初始化测试标准提取器"""
        # 定义支持的测试标准模式
        self.standard_patterns = {
            'EIA': r'EIA\s*[-\s]?\s*364\s*[-\s]?\s*(?:[A-Z]*\d+[A-Z0-9]*|[A-Z]+\s*\d+|TP\d{2,3})',
            'IEC': r'IEC[-\s]?60[\d]{3}[-\s]?[\d]{0,2}',
            'IEEE': r'IEEE[-\s]?(Std[.\s])?[\d]{4}',
            'MIL': r'MIL[-\s]STD[-\s]?[\d]{4}',
            'ISO': r'ISO[-\s]?[\d]{4,5}',
            'ANSI': r'ANSI[-\s]?[A-Z]{1,2}[-\s]?[\d]{4}',
            'JIS': r'JIS[-\s]?[A-Z]{1,2}[-\s]?[\d]{4}',
            'GB': r'GB[-\s]?[A-Z]?[-\s]?[\d]{4,5}',
        }
        
    def extract_standard_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        从文本中提取所有支持的测试标准
        
        Args:
            text: 要搜索的文本
            
        Returns:
            找到的测试标准列表，每个元素包含类型和标准号
        """
        found_standards = []
        
        try:
            for standard_type, pattern in self.standard_patterns.items():
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    standard_number = self._normalize_standard_format(match.group(), standard_type)
                    found_standards.append({
                        'type': standard_type,
                        'number': standard_number,
                        'original': match.group()
                    })
                    logger.debug(f"找到{standard_type}标准: {standard_number}")
                    
        except Exception as e:
            logger.error(f"提取测试标准时出错: {e}", exc_info=True)
            
        return found_standards
    
    def extract_specific_standard(self, text: str, standard_type: str) -> Optional[str]:
        """
        从文本中提取指定类型的测试标准
        
        Args:
            text: 要搜索的文本
            standard_type: 标准类型 (如 'EIA', 'IEC' 等)
            
        Returns:
            找到的标准号或None
        """
        try:
            if standard_type not in self.standard_patterns:
                logger.warning(f"不支持的标准类型: {standard_type}")
                return None
                
            pattern = self.standard_patterns[standard_type]
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                standard_number = self._normalize_standard_format(match.group(), standard_type)
                logger.debug(f"找到{standard_type}标准: {standard_number}")
                return standard_number
                
        except Exception as e:
            logger.error(f"提取{standard_type}标准时出错: {e}", exc_info=True)
            
        return None
    
    def _normalize_standard_format(self, standard_text: str, standard_type: str) -> str:
        """
        标准化测试标准格式
        
        Args:
            standard_text: 原始标准文本
            standard_type: 标准类型
            
        Returns:
            标准化后的标准文本
        """
        try:
            # 标准化格式，将空格和连字符统一处理
            normalized = re.sub(r'[-\s]+', '-', standard_text)
            # 清理多余的连字符
            normalized = re.sub(r'-+', '-', normalized)
            # 移除开头和结尾的连字符
            normalized = normalized.strip('-')
            return normalized
        except Exception as e:
            logger.error(f"标准化{standard_type}格式时出错: {e}")
            return standard_text
    
    def find_standard_by_chapter(self, doc, chapter_number: str) -> Optional[str]:
        """
        根据章节号在文档中查找测试标准
        
        Args:
            doc: Word文档对象
            chapter_number: 章节编号
            
        Returns:
            找到的测试标准或None
        """
        try:
            logger.info(f"开始在文档中查找章节 {chapter_number} 的测试标准")
            
            # 获取文档内容
            content = doc.Content.Text
            logger.debug(f"文档总长度: {len(content)} 字符")
            
            # 查找章节位置
            chapter_positions = self._find_chapter_positions(content, chapter_number)
            if not chapter_positions:
                logger.warning(f"未在文档中找到章节: {chapter_number}")
                return None
                
            logger.debug(f"找到 {len(chapter_positions)} 个章节位置")
                
            # 获取章节范围
            start_pos = chapter_positions[0]
            
            # 查找下一个同级章节
            next_chapter_number = self._get_next_chapter_number(chapter_number)
            next_positions = self._find_chapter_positions(content, next_chapter_number) if next_chapter_number else []
            
            # 如果没找到同级章节，查找上级章节
            if not next_positions:
                upper_chapter_number = self._get_upper_level_chapter_number(chapter_number)
                next_positions = self._find_chapter_positions(content, upper_chapter_number) if upper_chapter_number else []
            
            # 确定结束位置 - 修正逻辑，选择下一个有效位置而不是简单地取第一个
            end_pos = len(content)  # 默认为文档末尾
            if next_positions:
                # 寻找第一个在当前章节之后的位置
                for pos in next_positions:
                    if pos > start_pos:
                        end_pos = pos
                        break
            
            # 验证范围合理性
            if end_pos <= start_pos:
                logger.warning(f"章节范围不合理: {start_pos} - {end_pos}, 使用文档末尾作为结束位置")
                end_pos = len(content)
            
            # 确保起始位置是有效的
            if start_pos < 0 or start_pos >= len(content):
                logger.error(f"章节起始位置无效: {start_pos}, 无法提取章节内容")
                return None
            
            logger.debug(f"章节范围: {start_pos} - {end_pos}")
            
            # 提取章节范围内的内容
            section_content = content[start_pos:end_pos]
            logger.debug(f"章节范围内容长度: {len(section_content)} 字符")
            
            # 从章节内容中提取测试标准
            standard = self._extract_standard_from_section(section_content)
            return standard
            
        except Exception as e:
            logger.error(f"根据章节查找测试标准时出错: {e}", exc_info=True)
            return None
    
    def _find_chapter_positions(self, content: str, chapter_number: str) -> List[int]:
        """
        在文档内容中查找章节号的位置
        
        Args:
            content: 文档内容
            chapter_number: 章节编号
            
        Returns:
            章节号在文档中的位置列表
        """
        positions = []
        try:
            logger.debug(f"尝试多种方式查找章节号: {chapter_number}")
            
            # 处理特殊字符如星号(*)等，生成适用于正则表达式的章节号模式
            escaped_chapter = self._escape_chapter_number(chapter_number)
            
            # 方式1: 精确匹配章节号后跟非数字字符
            pattern1 = rf'\b{escaped_chapter}(?=\D)'
            logger.debug(f"查找章节模式1: {pattern1}")
            
            # 方式2: 章节号在行首
            pattern2 = rf'^\s*{escaped_chapter}(?=\D)'
            logger.debug(f"查找章节模式2: {pattern2}")
            
            # 方式3: 章节号后跟空格和文字
            pattern3 = rf'\b{escaped_chapter}\s+'
            logger.debug(f"查找章节模式3: {pattern3}")
            
            patterns = [pattern1, pattern2, pattern3]
            found = False
            
            for i, pattern in enumerate(patterns, 1):
                logger.debug(f"尝试模式{i}: {pattern}")
                for match in re.finditer(pattern, content, re.MULTILINE):
                    start_pos = match.start()
                    positions.append(start_pos)
                    logger.debug(f"模式{i}找到章节 {chapter_number} 位置: {start_pos}")
                    found = True
                    
            # 如果常规方法找不到，尝试更宽松的匹配
            if not positions:
                logger.debug(f"使用宽松匹配方式查找章节号: {chapter_number}")
                # 查找类似 "5.4" 这样的模式，不严格要求边界
                loose_pattern = rf'{escaped_chapter}(?=\D)'
                for match in re.finditer(loose_pattern, content):
                    start_pos = match.start()
                    # 检查是否在行首附近
                    line_start = content.rfind('\n', 0, start_pos) + 1 if content.rfind('\n', 0, start_pos) != -1 else 0
                    if start_pos - line_start < 10:  # 章节号在行首10个字符内
                        positions.append(start_pos)
                        logger.debug(f"宽松匹配找到章节 {chapter_number} 位置: {start_pos}")
                        
            logger.debug(f"总共找到 {len(positions)} 个匹配位置")
            # 对位置进行排序
            positions.sort()
                    
        except Exception as e:
            logger.error(f"查找章节位置时出错: {e}", exc_info=True)
            
        return positions
    
    def _escape_chapter_number(self, chapter_number: str) -> str:
        """
        转义章节号中的特殊字符以用于正则表达式匹配
        
        Args:
            chapter_number: 原始章节号
            
        Returns:
            适用于正则表达式的章节号模式
        """
        # 先去除末尾的特殊符号，只保留数字和点
        # 改进处理：更精确地提取章节号的核心部分（数字和点），忽略末尾的*, #, (a)等特殊字符
        cleaned_match = re.match(r'^(\d+(?:\.\d+)*)(.*)', chapter_number)
        if cleaned_match:
            cleaned = cleaned_match.group(1)  # 只保留数字和点的部分
        else:
            # 如果没有匹配到标准格式，则使用原始逻辑
            cleaned = re.sub(r'^(\d+(?:\.\d+)?)?.*', r'\1', chapter_number)
        
        if not cleaned:
            # 如果清洗后为空，则使用原始章节号的一部分
            cleaned = ''.join(re.findall(r'[\d.]', chapter_number))
        
        # 转义点号用于正则表达式
        escaped = cleaned.replace('.', r'\.')
        
        # 添加模式以匹配末尾可能的特殊字符，如*、#、(a)等
        # 允许章节号后跟零个或多个非数字字符（包括*, #, (a)等）
        escaped = escaped + r'[^0-9]*'
        
        return escaped
    
    def _get_next_chapter_number(self, chapter_number: str) -> Optional[str]:
        """
        获取下一个同级章节号
        
        Args:
            chapter_number: 当前章节号
            
        Returns:
            下一个同级章节号
        """
        try:
            # 处理带有特殊字符的章节号（如6.5*）
            clean_chapter = re.sub(r'[^\d.]', '', chapter_number)  # 移除非数字和点的字符
            if not clean_chapter:
                logger.warning(f"无法解析章节号: {chapter_number}")
                return None
                
            parts = clean_chapter.split('.')
            if len(parts) > 1:
                # 增加最后一级编号
                last_part = int(parts[-1])
                parts[-1] = str(last_part + 1)
            return '.'.join(parts)
        except Exception as e:
            logger.error(f"计算下一个章节号时出错: {e}")
            return None
    
    def _get_upper_level_chapter_number(self, chapter_number: str) -> Optional[str]:
        """
        获取上一级章节号
        
        Args:
            chapter_number: 当前章节号
            
        Returns:
            上一级章节号
        """
        try:
            # 处理带有特殊字符的章节号（如6.5*）
            clean_chapter = re.sub(r'[^\d.]', '', chapter_number)  # 移除非数字和点的字符
            if not clean_chapter:
                logger.warning(f"无法解析章节号: {chapter_number}")
                return None
                
            parts = clean_chapter.split('.')
            if len(parts) > 1:
                # 增加上一级编号，重置最后一级为1
                upper_part = int(parts[-2])
                parts[-2] = str(upper_part + 1)
                parts[-1] = "1"
            return '.'.join(parts)
        except Exception as e:
            logger.error(f"计算上一级章节号时出错: {e}")
            return None
    
    def _extract_standard_from_section(self, content: str) -> Optional[str]:
        """
        从章节内容中提取测试标准
        
        Args:
            content: 章节内容
            
        Returns:
            找到的测试标准或None
        """
        try:
            # 优先查找EIA标准，因为这是最常用的标准
            eia_standard = self.extract_specific_standard(content, 'EIA')
            if eia_standard:
                return eia_standard
                
            # 如果没有找到EIA标准，查找其他标准
            all_standards = self.extract_standard_from_text(content)
            if all_standards:
                # 返回第一个找到的标准
                return all_standards[0]['number']
                
            return None
        except Exception as e:
            logger.error(f"从章节内容提取标准时出错: {e}", exc_info=True)
            return None


# 创建全局实例
test_standard_extractor = TestStandardExtractor()


def extract_test_standard_from_text(text: str) -> List[Dict[str, str]]:
    """
    从文本中提取所有支持的测试标准
    
    Args:
        text: 要搜索的文本
        
    Returns:
        找到的测试标准列表
    """
    return test_standard_extractor.extract_standard_from_text(text)


def extract_specific_test_standard(text: str, standard_type: str) -> Optional[str]:
    """
    从文本中提取指定类型的测试标准
    
    Args:
        text: 要搜索的文本
        standard_type: 标准类型
        
    Returns:
        找到的标准号或None
    """
    return test_standard_extractor.extract_specific_standard(text, standard_type)


def find_test_standard_by_chapter(doc, chapter_number: str) -> Optional[str]:
    """
    根据章节号在文档中查找测试标准
    
    Args:
        doc: Word文档对象
        chapter_number: 章节编号
        
    Returns:
        找到的测试标准或None
    """
    return test_standard_extractor.find_standard_by_chapter(doc, chapter_number)