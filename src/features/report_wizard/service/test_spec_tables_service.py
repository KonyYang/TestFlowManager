"""
Test Spec Tables服务模块
提供填充Test Description、Test Method和Test Result表格的业务逻辑服务

内部委托：
- Test Description 表格填充 → TestDescriptionTableService
- Test Method 表格填充 → TestMethodTableService
"""

from typing import Dict, Any, Callable, Optional, List
from src.core.logger import logger
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from src.features.report_wizard.service.test_result_service import TestResultService
from .utils.sample_data_extractor import SampleDataExtractor
from .test_sample_info_service import TestSampleInfoService
from .test_description_table_service import TestDescriptionTableService
from .test_method_table_service import TestMethodTableService
from src.infrastructure.office.facade import OfficeFacade


class TestSpecTablesService:
    """
    Test Spec Tables服务类
    提供填充Test Description、Test Method和Test Result表格的业务逻辑服务

    作为编排层，协调：
    - TestDescriptionTableService：Description 表格填充
    - TestMethodTableService：Method 表格填充
    - TestResultService：Result 表格生成
    - TestSampleInfoService：样品信息表格填充
    """

    def __init__(self, office_facade=None):
        """初始化Test Spec Tables服务"""
        self.test_result_service = TestResultService()
        self.test_sample_info_service = TestSampleInfoService()
        self._description_table_service = TestDescriptionTableService()
        self._method_table_service = TestMethodTableService()
        self._matrix_headers: List[str] = []
        self._matrix_rows: List[List[str]] = []
        self._office_facade = office_facade

    def _get_office_facade(self):
        if self._office_facade is None:
            self._office_facade = OfficeFacade()
        return self._office_facade

    def set_matrix_table_data(self, headers=None, rows=None) -> None:
        """设置当前处理所使用的 Matrix 表头和行数据快照。"""
        self._matrix_headers = list(headers or [])
        self._matrix_rows = list(rows or [])

    def _get_matrix_table_data(self):
        return self._matrix_headers, self._matrix_rows

    def _resolve_sample_data(
        self,
        matrix_data_structure: MatrixDataStructure,
        *,
        project_json_data: Optional[Dict[str, Any]] = None,
        sample_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """解析测试样品信息，只接受显式输入。"""
        if sample_data is not None:
            return list(sample_data)

        if project_json_data is not None:
            return SampleDataExtractor.extract_sample_info_from_json(project_json_data)

        return []
    
    def _safe_callback_call(self, callback, *args):
        """
        安全调用回调函数或Qt信号
        
        Args:
            callback: 回调函数或Qt信号
            *args: 传递给回调的参数
            
        Returns:
            调用结果，如果调用失败则返回None
        """
        if callback is None:
            return None
            
        try:
            if hasattr(callback, 'emit'):
                return callback.emit(*args)
            else:
                return callback(*args)
        except Exception as e:
            logger.error(f"回调调用失败: {e}")
            return None

    def fill_all_test_spec_tables(
        self, 
        document_path: str, 
        matrix_data_structure: MatrixDataStructure,
        matrix_headers=None,
        matrix_rows=None,
        project_json_data: Optional[Dict[str, Any]] = None,
        sample_data: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        填充Test Description、Test Method和Test Result表格
        
        Args:
            document_path: Word文档路径
            matrix_data_structure: Matrix数据结构
            progress_callback: 进度回调函数
            status_callback: 状态回调函数
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始填充Test Description、Test Method和Test Result表格，文档路径: {document_path}")
        self.set_matrix_table_data(matrix_headers, matrix_rows)
        word_app = None
        word_doc = None
        word_session = None
        
        try:
            # 通过 OfficeFacade 创建 Word session
            office_facade = self._get_office_facade()
            word_session = office_facade.create_session("word")
            handle = word_session.acquire()

            if status_callback:
                self._safe_callback_call(status_callback, "正在打开文档...")
            
            # 检查文档是否存在
            import os
            if not os.path.exists(document_path):
                logger.error(f"文档不存在: {document_path}")
                if status_callback:
                    self._safe_callback_call(status_callback, f"错误: 文档不存在 - {document_path}")
                return False
            
            # 使用 OfficeFacade session 提供的 Word 应用程序实例
            word_app = handle.application
            if word_app is None:
                logger.error("无法从 OfficeFacade session 获取 Word 应用程序实例")
                if status_callback:
                    self._safe_callback_call(status_callback, "错误: 无法获取 Word 应用程序实例")
                return False
            
            word_app.Visible = False
            word_app.DisplayAlerts = False
            
            word_doc = word_app.Documents.Open(document_path)
            logger.info(f"成功打开文档，包含 {word_doc.Paragraphs.Count} 个段落和 {word_doc.Tables.Count} 个表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 10)
            
            # --- 填充 Test Description 表格 ---
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找TEST DESCRIPTION段落...")
            
            from .utils.table_handler import TableHandler
            description_table = TableHandler.find_table_by_paragraph_win32com(word_doc, "TEST DESCRIPTION")
            if description_table:
                logger.info("找到TEST DESCRIPTION表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Description表格...")
                
                header_row, data_rows = self._get_matrix_table_data()
                self._description_table_service.fill_description_table(
                    description_table, header_row, data_rows, word_app
                )
            else:
                logger.warning("未找到TEST DESCRIPTION表格")
                if status_callback:
                    status_callback("警告: 未找到TEST DESCRIPTION表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 60)
            
            # --- 填充 Test Method 表格 ---
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找TEST METHODS/REQUIREMENTS段落...")
            
            method_table = TableHandler.find_table_by_paragraph_win32com(word_doc, "TEST METHODS/REQUIREMENTS")
            if method_table:
                logger.info("找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Method表格...")
                
                header_row, data_rows = self._get_matrix_table_data()
                self._method_table_service.fill_method_table(
                    method_table, header_row, data_rows, word_app
                )
            else:
                logger.warning("未找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到TEST METHODS/REQUIREMENTS表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 90)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在保存文档...")
            
            logger.info(f"Test Description和Test Method表格填充完成，等待Test Result处理完成")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 100)
            
            if status_callback:
                self._safe_callback_call(status_callback, "处理完成！表格已成功填充。")
            
            logger.info(f"Test Description、Test Method和Test Result表格填充完成")
            
            # --- 生成 Test Result 表格 ---
            if status_callback:
                self._safe_callback_call(status_callback, "正在生成Test Result表格...")
            
            result = self.test_result_service.generate_test_result_with_structure(
                matrix_structure=matrix_data_structure,
                document_path=document_path,
                progress_callback=progress_callback,
                status_callback=status_callback,
                word_app_instance=word_app,
                word_doc_instance=word_doc,
                should_save_doc=False
            )
            
            if result:
                logger.info("Test Result表格生成完成")
            else:
                logger.error("Test Result表格生成失败")
            
            # --- 填充测试样品信息表格 ---
            try:
                sample_data = self._resolve_sample_data(
                    matrix_data_structure,
                    project_json_data=project_json_data,
                    sample_data=sample_data,
                )

                if sample_data:
                    logger.info(f"开始填充测试样品信息表格，共 {len(sample_data)} 条数据")
                    sample_result = self.test_sample_info_service.fill_test_sample_info_table(
                        document_path=document_path,
                        sample_data=sample_data,
                        word_app_instance=word_app,
                        word_doc_instance=word_doc
                    )
                    
                    if sample_result:
                        logger.info("测试样品信息表格填充完成")
                    else:
                        logger.error("测试样品信息表格填充失败")
                else:
                    logger.info("没有找到测试样品信息数据，跳过填充")
            except Exception as e:
                logger.error(f"填充测试样品信息表格时出错: {e}")
                import traceback
                logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            return True
            
        except Exception as e:
            logger.error(f"填充Test Description和Test Method表格时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            if status_callback:
                self._safe_callback_call(status_callback, f"错误: {str(e)}")
            return False
        finally:
            # 关闭文档（如果已打开）
            try:
                if word_doc:
                    word_doc.Close(SaveChanges=False)
            except:
                pass
            
            # 释放 OfficeFacade session
            try:
                if word_session is not None:
                    word_session.release()
            except Exception as e:
                logger.error(f"释放 Word session 时出错: {e}")

    def fill_test_sample_info_table_from_json(
        self,
        document_path: str,
        json_data: Dict[str, Any],
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        word_app_instance=None,
        word_doc_instance=None
    ) -> bool:
        """
        从JSON数据填充测试样品信息表格
        
        Args:
            document_path: Word文档路径
            json_data: JSON数据字典
            progress_callback: 进度回调函数
            status_callback: 状态回调函数
            word_app_instance: Word应用程序实例（可选）
            word_doc_instance: Word文档实例（可选）
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始从JSON数据填充测试样品信息表格，文档路径: {document_path}")
        
        try:
            if status_callback:
                self._safe_callback_call(status_callback, "正在提取测试样品信息...")
            
            sample_data = SampleDataExtractor.extract_sample_info_from_json(json_data)
            
            if not sample_data:
                logger.warning("未从JSON数据中提取到测试样品信息")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到测试样品信息数据")
                return True
            
            if status_callback:
                self._safe_callback_call(status_callback, f"提取到 {len(sample_data)} 条测试样品信息")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 50)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在填充测试样品信息表格...")
            
            result = self.test_sample_info_service.fill_test_sample_info_table(
                document_path=document_path,
                sample_data=sample_data,
                word_app_instance=word_app_instance,
                word_doc_instance=word_doc_instance
            )
            
            if result:
                logger.info("测试样品信息表格填充完成")
                if status_callback:
                    self._safe_callback_call(status_callback, "测试样品信息表格填充完成")
            else:
                logger.error("测试样品信息表格填充失败")
                if status_callback:
                    self._safe_callback_call(status_callback, "错误: 测试样品信息表格填充失败")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 100)
            
            return result
            
        except Exception as e:
            logger.error(f"填充测试样品信息表格时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            if status_callback:
                self._safe_callback_call(status_callback, f"错误: {str(e)}")
            return False
