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

    def __init__(self):
        """初始化Word解析器"""
        pass

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
            return self._parse_doc_via_com(file_path, page_number, keyword)
        elif file_path.lower().endswith('.docx'):
            # 对于.docx文件，使用python-docx库
            return self._parse_docx(file_path, page_number, keyword)
        else:
            raise ValueError(f"不支持的Word文件格式: {file_path}")

    def _parse_doc_via_com(self, file_path: str, page_number=None, keyword=None):
        """
        通过COM接口解析.doc文件

        Args:
            file_path: .doc文件路径
            page_number: 指定页码（从1开始）
            keyword: 关键字筛选

        Returns:
            解析出的表格数据列表
        """
        word_app = None
        doc = None
        existing_word_app = False
        doc_already_opened = False
        try:
            import win32com.client
            import pythoncom
            import os
            
            logger.info(f"开始通过COM接口解析.doc文件: {file_path}")
            
            # 初始化COM
            pythoncom.CoInitialize()
            
            try:
                # 尝试连接到现有的Word应用程序实例
                word_app = win32com.client.GetActiveObject("Word.Application")
                existing_word_app = True
                logger.info("连接到现有的Word应用程序实例")
            except:
                # 如果没有现有的实例，则创建新的实例
                word_app = win32com.client.Dispatch("Word.Application")
                logger.info("创建新的Word应用程序实例")
            
            # 检查文档是否已经打开
            doc_already_opened = False
            try:
                # 检查文档是否已经在当前Word实例中打开
                for opened_doc in word_app.Documents:
                    if os.path.abspath(opened_doc.FullName).lower() == os.path.abspath(file_path).lower():
                        doc = opened_doc
                        doc_already_opened = True
                        logger.info("文档已在Word中打开")
                        break
            except Exception as e:
                logger.warning(f"检查文档是否已打开时出错: {e}")

            # 如果文档未打开，则打开它
            if not doc:
                # 以只读模式打开文档
                doc = word_app.Documents.Open(os.path.abspath(file_path), ReadOnly=True)
                logger.info(f"成功打开文档: {file_path}")

            # 设置Word应用程序为不可见，不在前台显示文档
            try:
                word_app.Visible = False
            except AttributeError:
                logger.warning("无法设置Word应用程序可见性属性")
            
            # 存储找到的表格数据
            found_tables = []
            
            logger.info(f"文档中总共找到 {doc.Tables.Count} 个表格")
            
            # 必须指定页码，只检查该页码的表格
            if page_number is not None:
                logger.info(f"开始检查第 {page_number} 页的表格")
                # 获取指定页码的表格范围
                tables_on_page = []
                for i in range(1, doc.Tables.Count + 1):
                    table = doc.Tables(i)
                    # 检查表格是否在指定页码上
                    if self._check_table_on_page_com(doc, table, page_number):
                        tables_on_page.append((i, table))
                
                # 遍历指定页码的表格
                for i, table in tables_on_page:
                    logger.info(f"开始检查第 {page_number} 页的第 {i} 个表格")
                    
                    # 检查表格是否符合要求
                    is_target = self._is_target_table_com(doc, table, i, page_number, keyword)
                    if is_target:
                        logger.info(f"第 {page_number} 页的第 {i} 个表格符合要求")
                        # 提取表格数据
                        table_data = self._extract_table_data_com(table)
                        found_tables.append(table_data)
                    else:
                        logger.info(f"第 {page_number} 页的第 {i} 个表格不符合要求")
            else:
                # 没有指定页码时，检查所有表格
                logger.info("未指定页码，检查所有表格")
                for i in range(1, doc.Tables.Count + 1):
                    table = doc.Tables(i)
                    logger.info(f"开始检查第 {i} 个表格")
                    
                    # 检查表格是否符合要求
                    is_target = self._is_target_table_com(doc, table, i, page_number, keyword)
                    if is_target:
                        logger.info(f"第 {i} 个表格符合要求")
                        # 提取表格数据
                        table_data = self._extract_table_data_com(table)
                        found_tables.append(table_data)
                    else:
                        logger.info(f"第 {i} 个表格不符合要求")
            
            logger.info(f"总共找到 {len(found_tables)} 个符合要求的表格")
            return found_tables
            
        except Exception as e:
            logger.error(f"通过COM接口解析Word文档时出错: {e}", exc_info=True)
            return []
        finally:
            # 关闭文档和应用
            try:
                if doc and not doc_already_opened:
                    doc.Close()
                    logger.info("成功关闭我们打开的Word文档")
                elif doc and doc_already_opened:
                    logger.info("保持用户已打开的Word文档开启")
            except Exception as e:
                logger.warning(f"关闭Word文档时出错: {e}")
            
            try:
                if word_app and not existing_word_app:
                    word_app.Quit()
                    logger.info("退出新创建的Word应用程序实例")
                elif word_app and existing_word_app:
                    logger.info("保持现有Word应用程序实例运行")
            except Exception as e:
                logger.warning(f"退出Word应用程序时出错: {e}")
                
            try:
                # 反初始化COM
                pythoncom.CoUninitialize()
                logger.info("COM反初始化完成")
            except Exception as e:
                logger.warning(f"COM反初始化时出错: {e}")

    def _is_target_table_com(self, doc, table, table_index: int, page_number=None, keyword=None):
        """
        判断是否为目标表格 (用于COM接口)

        Args:
            doc: Word文档对象
            table: 表格对象
            table_index: 表格索引
            page_number: 指定页码
            keyword: 关键字筛选

        Returns:
            是否为目标表格
        """
        try:
            logger.info(f"开始判断第 {table_index} 个表格是否为目标表格 (COM接口)")
            
            # 默认关键字为"test"
            if keyword is None:
                keyword = "test"
                
            # 检查表格是否包含关键字
            has_keyword = self._check_table_for_keyword_com(table, keyword)
            logger.info(f"第 {table_index} 个表格是否包含关键字'{keyword}': {has_keyword}")
            
            # 必须同时检查关键字和页码
            if page_number is None:
                logger.warning("页码未指定，无法判断目标表格")
                return False
                
            # 检查表格是否在指定页码
            is_on_page = self._check_table_on_page_com(doc, table, page_number)
            logger.info(f"第 {table_index} 个表格是否在第{page_number}页: {is_on_page}")
            
            result = has_keyword and is_on_page
            logger.info(f"第 {table_index} 个表格是否为目标表格: {result}")
            return result
        except Exception as e:
            logger.error(f"判断目标表格时出错: {e}", exc_info=True)
            return False

    def _check_table_on_page_com(self, doc, table, page_number):
        """
        检查表格是否在指定页码上 (用于COM接口)

        Args:
            doc: Word文档对象
            table: 表格对象
            page_number: 页码

        Returns:
            是否在指定页码上
        """
        try:
            # 获取表格的范围
            table_range = table.Range
            
            # 获取表格所在页码
            table_page = table_range.Information(3)  # 3表示页码信息
            
            logger.debug(f"表格页码检查: 表格在第 {table_page} 页, 目标页码: 第 {page_number} 页")
            
            return table_page == page_number
        except Exception as e:
            logger.error(f"检查表格页码时出错: {e}", exc_info=True)
            # 出错时默认返回True，避免因为页码检查失败而错过目标表格
            # 但在实际应用中，这可能需要更精确的处理
            return True

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

    def _check_table_for_keyword_com(self, table, keyword: str):
        """
        检查表格是否包含关键字 (用于COM接口)

        Args:
            table: 表格对象
            keyword: 关键字

        Returns:
            是否包含关键字
        """
        try:
            logger.info("开始检查表格是否包含关键字 (COM接口)")
            # 遍历表格的所有单元格
            for row_idx in range(1, table.Rows.Count + 1):
                for col_idx in range(1, table.Columns.Count + 1):
                    try:
                        # 检查单元格是否存在
                        if row_idx <= table.Rows.Count and col_idx <= table.Columns.Count:
                            cell = table.Cell(row_idx, col_idx)
                            cell_text = cell.Range.Text
                            
                            # 清理文本内容（按照VBA方式处理特殊字符）
                            cell_text = self._clean_word_text_com(cell_text)
                            
                            # 显示检查的单元格内容，方便调试
                            logger.debug(f"检查单元格[{row_idx},{col_idx}]: '{cell_text}' 是否包含关键字 '{keyword}'")
                            
                            # 检查是否包含关键字（不区分大小写）
                            if keyword.lower() in cell_text.lower():
                                logger.info(f"在第 {row_idx} 行第 {col_idx} 列找到关键字'{keyword}': {cell_text}")
                                return True
                    except Exception as e:
                        logger.warning(f"访问第 {row_idx} 行第 {col_idx} 列单元格时出错: {e}")
                        continue
            
            # 如果没找到，记录日志
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
        
    def _clean_word_text_com(self, text):
        """
        清理Word文本内容（用于COM接口）
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
        text = text.replace('\a', '')    # 去掉段落标记
        
        # 去掉多余的空格和换行
        import re
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_table_data_com(self, table):
        """
        提取表格数据 (用于COM接口)

        Args:
            table: 表格对象

        Returns:
            表格数据（二维列表）
        """
        try:
            table_data = []
            
            # 遍历表格的每一行
            for i in range(1, table.Rows.Count + 1):
                row_data = []
                # 遍历行中的每个单元格
                for j in range(1, table.Columns.Count + 1):
                    try:
                        # 检查单元格是否存在
                        if i <= table.Rows.Count and j <= table.Columns.Count:
                            cell = table.Cell(i, j)
                            # 清理单元格文本（去掉Word的特殊字符）
                            cell_text = cell.Range.Text
                            cell_text = self._clean_word_text_com(cell_text)
                            row_data.append(cell_text)
                        else:
                            row_data.append("")  # 添加空字符串作为占位符
                    except Exception as e:
                        logger.warning(f"提取第 {i} 行第 {j} 列单元格时出错: {e}")
                        row_data.append("")  # 添加空字符串作为占位符
                table_data.append(row_data)
            
            return table_data
        except Exception as e:
            logger.error(f"提取表格数据时出错: {e}", exc_info=True)
            return None

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