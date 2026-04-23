"""
规格书提取服务
从不同格式的文档中提取Matrix表格数据
"""
import os

from src.core.logger import logger
from src.infrastructure.office import OfficeFacade
from src.features.matrix.service.document_parsers.excel_parser import ExcelParser
from src.features.matrix.service.document_parsers.word_parser import WordParser


class SpecExtractor:
    """
    规格书提取器
    支持从PDF、Word、Excel文档中提取Matrix表格数据
    """

    def __init__(self, office_facade=None):
        """初始化规格书提取器"""
        self._office_facade = office_facade

    def _get_office_facade(self):
        """Lazily create the shared OfficeFacade dependency."""
        if self._office_facade is None:
            self._office_facade = OfficeFacade()
        return self._office_facade

    def extract_from_document(self, file_path: str, page_number=None, keyword=None):
        """
        从文档中提取Matrix表格数据

        Args:
            file_path: 文档路径
            page_number: 指定页码（从1开始）
            keyword: 关键字筛选

        Returns:
            提取的表格数据，格式与Matrix数据模型兼容
        """
        try:
            logger.info(f"开始从文档提取Matrix表格数据: {file_path}")
            
            # 根据文件扩展名选择合适的解析器
            if file_path.lower().endswith('.pdf'):
                logger.info("检测到PDF文件，使用PDF解析器")
                return self._extract_from_pdf(file_path, page_number, keyword)
            elif file_path.lower().endswith(('.doc', '.docx')):
                logger.info("检测到Word文件，使用Word解析器")
                return self._extract_from_word(file_path, page_number, keyword)
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                logger.info("检测到Excel文件，使用Excel解析器")
                return self._extract_from_excel(file_path, page_number, keyword)
            else:
                logger.warning(f"不支持的文件格式: {file_path}")
                return None
        except Exception as e:
            logger.error(f"从文档提取数据时出错: {e}")
            return None

    def extract_test_methods(self, file_path: str, chapter_mappings: dict) -> dict:
        """
        从规格书文档中提取测试方法标准
        
        Args:
            file_path: 规格书文件路径
            chapter_mappings: 章节号映射字典 {matrix_row_index: chapter_number}
            
        Returns:
            测试方法标准字典 {matrix_row_index: test_method}
        """
        try:
            logger.info(f"开始从规格书提取测试方法标准: {file_path}")
            logger.info(f"章节映射数量: {len(chapter_mappings)}")
            logger.debug(f"章节映射详情: {chapter_mappings}")
            test_methods = {}

            if not chapter_mappings:
                logger.info("章节映射为空，跳过测试方法提取")
                return test_methods
            
            # 根据文件扩展名选择合适的解析器
            if file_path.lower().endswith(('.doc', '.docx')):
                logger.info("检测到Word文件，使用Word解析器提取测试方法")
                parser = WordParser(self._office_facade)
                doc = None
                session = None
                
                try:
                    office_facade = self._get_office_facade()
                    session = office_facade.create_session("word")
                    handle = session.acquire()
                    word_app = handle.application
                    word_app.Visible = False
                    doc = word_app.Documents.Open(os.path.abspath(file_path), ReadOnly=True)
                    
                    # 为每个章节号查找测试方法
                    for row_index, chapter_number in chapter_mappings.items():
                        if chapter_number and str(chapter_number).strip():
                            logger.info(f"查找第{row_index}行的测试方法，章节号: {chapter_number}")
                            test_method = parser.find_test_method_in_spec(doc, str(chapter_number))
                            if test_method:
                                test_methods[row_index] = test_method
                                logger.info(f"第{row_index}行找到测试方法: {test_method}")
                            else:
                                logger.info(f"第{row_index}行未找到测试方法，章节号: {chapter_number}")
                finally:
                    try:
                        if doc:
                            doc.Close()
                    except Exception as e:
                        logger.warning(f"关闭Word文档时出错: {e}")
                    
                    try:
                        if session:
                            session.release()
                    except Exception as e:
                        logger.warning(f"释放Word session时出错: {e}")
                    
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                logger.info("检测到Excel文件，跳过测试方法提取")
                # Excel文件不支持测试方法提取
                return test_methods
            elif file_path.lower().endswith('.pdf'):
                logger.info("检测到PDF文件，跳过测试方法提取")
                # PDF文件暂不支持测试方法提取
                return test_methods
            else:
                logger.warning(f"不支持的文件格式: {file_path}")
                return test_methods
                
            logger.info(f"测试方法提取完成，共找到 {len(test_methods)} 个测试方法")
            logger.debug(f"提取的测试方法详情: {test_methods}")
            return test_methods
            
        except Exception as e:
            logger.error(f"从规格书提取测试方法时出错: {e}", exc_info=True)
            return {}

    def _extract_from_pdf(self, file_path: str, page_number=None, keyword=None):
        """
        从PDF文档中提取Matrix表格数据

        Args:
            file_path: PDF文件路径
            page_number: 指定页码（从1开始）
            keyword: 关键字筛选

        Returns:
            提取的表格数据
        """
        try:
            # TODO: 实现PDF解析逻辑
            logger.info(f"开始解析PDF文档: {file_path}")
            # 这里将调用pdf_parser.py中的具体实现
            logger.warning("PDF解析功能尚未实现")
            return None
        except Exception as e:
            logger.error(f"解析PDF文档时出错: {e}")
            return None

    def _extract_from_word(self, file_path: str, page_number=None, keyword=None):
        """
        从Word文档中提取Matrix表格数据

        Args:
            file_path: Word文件路径
            page_number: 指定页码（从1开始）
            keyword: 关键字筛选

        Returns:
            提取的表格数据
        """
        try:
            logger.info(f"开始解析Word文档: {file_path}")
            logger.info(f"指定页码: {page_number}, 关键字: {keyword}")
            # 使用WordParser解析文档，传递页码和关键字参数
            parser = WordParser()
            tables = parser.parse(file_path, page_number, keyword)
            
            # 如果找到表格，返回第一个（或者根据需要选择合适的表格）
            if tables:
                logger.info(f"从Word文档中找到 {len(tables)} 个表格")
                logger.info("返回第一个找到的表格")
                return tables[0]  # 返回第一个找到的表格
            
            # 如果没有找到符合严格条件的表格，保持Matrix对话框默认的表格不变
            if not tables:
                logger.info("未找到符合条件的表格，保持Matrix对话框默认的表格不变")
                return None
            
            # 返回第一个找到的表格
            return tables[0]
        except Exception as e:
            logger.error(f"解析Word文档时出错: {e}")
            # 提供更友好的错误信息
            if "is not a Word file" in str(e):
                logger.error("文件可能已损坏或不是有效的Word文档")
            return None

    def _extract_from_excel(self, file_path: str, page_number=None, keyword=None):
        """
        从Excel文档中提取Matrix表格数据

        Args:
            file_path: Excel文件路径
            page_number: 指定页码（从1开始）
            keyword: 关键字筛选

        Returns:
            提取的表格数据和合并单元格信息
        """
        try:
            logger.info(f"开始解析Excel文档: {file_path}")
            # 使用ExcelParser解析文档
            parser = ExcelParser()
            # 注意：Excel解析不使用page_number和keyword参数
            result = parser.parse(file_path)
            tables = result['data']
            merged_cells = result['merged_cells']
            
            # 如果找到数据，返回它和合并单元格信息
            if tables and len(tables) > 0:
                logger.info(f"从Excel文档中提取到数据，行数: {len(tables)}")
                logger.debug(f"合并单元格信息: {merged_cells}")
                return {
                    'data': tables,
                    'merged_cells': merged_cells
                }
            
            # 如果没有找到数据
            logger.info("未从Excel文档中提取到数据")
            return None
        except Exception as e:
            logger.error(f"解析Excel文档时出错: {e}")
            return None
