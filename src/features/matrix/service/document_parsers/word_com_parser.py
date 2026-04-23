"""
Word COM接口解析器
专门处理.doc格式文件
"""

from src.core.logger import logger
from src.infrastructure.office import OfficeFacade
from typing import List, Optional
import os


class WordCOMParser:
    """Word COM接口解析器"""
    
    def __init__(self, office_facade: OfficeFacade):
        """
        初始化Word COM解析器
        
        Args:
            office_facade: OfficeFacade实例，用于管理Word运行时生命周期
        """
        self._office_facade = office_facade
    
    def parse(self, file_path: str, page_number=None, keyword=None):
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
        session = None
        doc_already_opened = False
        try:
            logger.info(f"开始通过COM接口解析.doc文件: {file_path}")
            
            # 通过OfficeFacade获取Word应用程序
            session = self._office_facade.create_session("word")
            handle = session.acquire()
            word_app = handle.application
            
            # 设置Word应用程序为不可见
            try:
                word_app.Visible = False
            except AttributeError:
                logger.warning("无法设置Word应用程序可见性属性")
            
            # 检查文档是否已经在当前Word实例中打开
            abs_path = os.path.abspath(file_path)
            for opened_doc in word_app.Documents:
                try:
                    if os.path.abspath(opened_doc.FullName).lower() == abs_path.lower():
                        doc = opened_doc
                        doc_already_opened = True
                        logger.info("文档已在Word中打开")
                        break
                except Exception as e:
                    logger.warning(f"检查已打开文档时出错: {e}")
            
            # 如果文档未打开，则打开它
            if not doc:
                doc = word_app.Documents.Open(abs_path, ReadOnly=True)
                logger.info(f"成功打开文档: {file_path}")
            
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
            # 只关闭本次流程打开的文档，保留用户已打开的文档
            try:
                if doc and not doc_already_opened:
                    doc.Close()
                    logger.info("成功关闭本次打开的Word文档")
                elif doc and doc_already_opened:
                    logger.info("保留用户已打开的Word文档")
            except Exception as e:
                logger.warning(f"关闭Word文档时出错: {e}")
            
            # 释放session
            try:
                if session:
                    session.release()
                    logger.debug("Word session已释放")
            except Exception as e:
                logger.warning(f"释放Word session时出错: {e}")

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
