"""
Word docx解析器
专门处理.docx格式文件
"""

from src.core.logger import logger
from typing import List, Optional


class WordDocxParser:
    """Word docx解析器"""
    
    def parse(self, file_path: str, page_number=None, keyword=None):
        """
        使用python-docx库解析.docx文件

        Args:
            file_path: .docx文件路径
            page_number: 指定页码（从1开始）
            keyword: 关键字筛选

        Returns:
            解析出的表格数据列表
        """
        try:
            from docx import Document
            import os
            
            logger.info(f"开始使用python-docx解析.docx文件: {file_path}")
            
            # 加载文档
            doc = Document(file_path)
            logger.info(f"成功加载文档，共有 {len(doc.tables)} 个表格")
            
            # 存储找到的表格数据
            found_tables = []
            
            # 遍历所有表格
            for i, table in enumerate(doc.tables):
                table_index = i + 1
                logger.info(f"开始检查第 {table_index} 个表格")
                
                # 检查表格是否符合要求
                is_target = self._is_target_table_docx(table, table_index, keyword)
                if is_target:
                    logger.info(f"第 {table_index} 个表格符合要求")
                    # 提取表格数据
                    table_data = self._extract_table_data_docx(table)
                    found_tables.append(table_data)
                else:
                    logger.info(f"第 {table_index} 个表格不符合要求")
            
            logger.info(f"总共找到 {len(found_tables)} 个符合要求的表格")
            return found_tables
            
        except Exception as e:
            logger.error(f"使用python-docx解析Word文档时出错: {e}", exc_info=True)
            return []

    def _is_target_table_docx(self, table, table_index: int, keyword=None):
        """
        判断是否为目标表格 (用于python-docx)

        Args:
            table: 表格对象
            table_index: 表格索引
            keyword: 关键字筛选

        Returns:
            是否为目标表格
        """
        try:
            logger.info(f"开始判断第 {table_index} 个表格是否为目标表格 (python-docx)")
            
            # 默认关键字为"test"
            if keyword is None:
                keyword = "test"
                
            # 检查表格是否包含关键字
            has_keyword = self._check_table_for_keyword(table, keyword)
            logger.info(f"第 {table_index} 个表格是否包含关键字'{keyword}': {has_keyword}")
            
            # 对于.docx文件，由于无法准确获取页码信息，我们只根据关键字筛选
            result = has_keyword
            logger.info(f"第 {table_index} 个表格是否为目标表格: {result}")
            return result
        except Exception as e:
            logger.error(f"判断目标表格时出错: {e}", exc_info=True)
            return False

    def _check_table_for_keyword(self, table, keyword: str):
        """
        检查表格是否包含关键字 (用于python-docx)

        Args:
            table: 表格对象
            keyword: 关键字

        Returns:
            是否包含关键字
        """
        try:
            logger.info("开始检查表格是否包含关键字")
            # 遍历表格的所有单元格
            for row_idx, row in enumerate(table.rows):
                for col_idx, cell in enumerate(row.cells):
                    cell_text = cell.text.strip()
                    
                    # 清理文本内容（按照VBA方式处理特殊字符）
                    cell_text = self._clean_word_text(cell_text)
                    
                    # 显示检查的单元格内容，方便调试
                    logger.debug(f"检查单元格[{row_idx+1},{col_idx+1}]: '{cell_text}' 是否包含关键字 '{keyword}'")
                    
                    # 检查是否包含关键字（不区分大小写）
                    if keyword.lower() in cell_text.lower():
                        logger.info(f"在第 {row_idx+1} 行第 {col_idx+1} 列找到关键字'{keyword}': {cell_text}")
                        return True
            
            # 如果没找到，打印前几行的内容供调试
            logger.info(f"表格中未找到关键字'{keyword}'")
            return False
        except Exception as e:
            logger.error(f"检查表格关键字时出错: {e}", exc_info=True)
            return False

    def _clean_word_text(self, text):
        """
        清理Word文本内容（用于python-docx）
        参考VBA代码处理特殊字符的方式
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 去掉常见的Word特殊字符
        text = text.replace('\r', '')  # 去掉回车符
        text = text.replace('\x07', '')  # 去掉隐藏符号（Bell字符）
        text = text.replace('\x0b', '')  # 去掉垂直制表符
        text = text.replace('\x0c', '')  # 去掉换页符
        
        # 去掉多余的空格和换行
        import re
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def _extract_table_data_docx(self, table):
        """
        提取表格数据 (用于python-docx)

        Args:
            table: 表格对象

        Returns:
            表格数据（二维列表）
        """
        try:
            table_data = []
            
            # 遍历表格的每一行
            for i, row in enumerate(table.rows):
                row_data = []
                # 遍历行中的每个单元格
                for j, cell in enumerate(row.cells):
                    try:
                        # 清理单元格文本（去掉Word的特殊字符）
                        cell_text = cell.text
                        cell_text = self._clean_word_text(cell_text)
                        row_data.append(cell_text)
                    except Exception as e:
                        logger.warning(f"提取第 {i+1} 行第 {j+1} 列单元格时出错: {e}")
                        row_data.append("")  # 添加空字符串作为占位符
                table_data.append(row_data)
            
            return table_data
        except Exception as e:
            logger.error(f"提取表格数据时出错: {e}", exc_info=True)
            return None