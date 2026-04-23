"""
Test Result服务模块
提供生成Test Result表格的业务逻辑服务

内部委托：
- 表格模板查找/复制/标题更新 → TestResultTableTemplateService
"""

from typing import Dict, Any, List, Optional
from src.core.logger import logger
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
import re
import os
from .test_result_table_template_service import TestResultTableTemplateService
from src.infrastructure.office.facade import OfficeFacade


class TestResultService:
    """
    Test Result服务类
    提供生成Test Result表格的业务逻辑服务

    作为编排层，协调：
    - TestResultTableTemplateService：表格模板查找/复制/标题更新
    - 自身负责：row/cell filling、text normalization、callback/生命周期
    """

    def __init__(self):
        """初始化Test Result服务"""
        self._template_service = TestResultTableTemplateService()

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

    def _replace_greater_lesser_symbols(self, text: str) -> str:
        """
        替换文本中的大于小于符号后跟随的数字和小数点为下划线
        """
        if not text or not isinstance(text, str):
            return text
        
        pattern = r'([≥≤])((?:\d+\.?)+)'
        def replace_numbers(match):
            symbol = match.group(1)
            numbers = match.group(2)
            processed_numbers = re.sub(r'\d+|\.', '_', numbers)
            return symbol + processed_numbers
        
        result = re.sub(pattern, replace_numbers, text)
        return result

    def _clean_text(self, text: str) -> str:
        """
        清理文本：移除首尾空格，压缩内部连续空格
        """
        if not text or not isinstance(text, str):
            return text
        
        cleaned = ' '.join(text.split())
        return cleaned

    def _filter_requirement(self, requirement: str) -> str:
        """
        过滤Requirement值：若等于"No detrimental condition"或"No damage"，则返回空字符串
        """
        if not requirement or not isinstance(requirement, str):
            return requirement
        
        return requirement

    def generate_test_result_with_structure(
        self, 
        matrix_structure: MatrixDataStructure, 
        document_path: str,
        progress_callback=None,
        status_callback=None,
        word_app_instance=None,
        word_doc_instance=None,
        should_save_doc=True
    ) -> bool:
        """
        使用Matrix数据结构生成Test Result表格
        
        Args:
            matrix_structure: Matrix数据结构
            document_path: Word文档路径
            progress_callback: 进度回调函数
            status_callback: 状态回调函数
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始生成Test Result表格，文档路径: {document_path}")
        
        # 通过 OfficeFacade 创建 Word session（仅在自己创建时才需要）
        office_facade = None
        word_session = None
        handle = None
        owns_word_doc = False
        
        try:
            if status_callback:
                self._safe_callback_call(status_callback, "正在打开文档...")
            
            # 检查文档是否存在
            if not os.path.exists(document_path):
                logger.error(f"文档不存在: {document_path}")
                if status_callback:
                    self._safe_callback_call(status_callback, f"错误: 文档不存在 - {document_path}")
                return False
            
            # 使用传入的Word文档实例（如果提供），否则使用传入的应用程序实例或创建新的实例
            if word_doc_instance is not None:
                word_doc = word_doc_instance
                word_app = word_doc.Application
            elif word_app_instance is not None:
                word_app = word_app_instance
                word_doc = word_app.Documents.Open(document_path)
                owns_word_doc = True
            else:
                # 通过 OfficeFacade 创建 Word session
                office_facade = OfficeFacade()
                word_session = office_facade.create_session("word")
                handle = word_session.acquire()
                
                word_app = handle.application
                if word_app is None:
                    logger.error("无法从 OfficeFacade session 获取 Word 应用程序实例")
                    if status_callback:
                        self._safe_callback_call(status_callback, "错误: 无法获取 Word 应用程序实例")
                    return False
                
                word_app.Visible = False
                word_app.DisplayAlerts = False
                
                word_doc = word_app.Documents.Open(document_path)
                owns_word_doc = True
            logger.info(f"成功打开文档，包含 {word_doc.Paragraphs.Count} 个段落和 {word_doc.Tables.Count} 个表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 10)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在从Matrix数据中提取所有组别信息...")
            
            # 从Matrix数据结构中获取所有组别的数据
            all_groups = matrix_structure.get_all_groups()
            logger.info(f"从Matrix数据结构获取到 {len(all_groups)} 个组别")
            if not all_groups:
                logger.warning("Matrix数据结构中没有找到任何组别")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: Matrix数据中没有找到任何组别")
                return False
            
            # 对组别名称进行自然排序（数值优先）
            sorted_groups = self._natural_sort_groups(all_groups)
            logger.info(f"排序后的组别: {sorted_groups}")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 30)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找Group # Test Results段落...")
            
            # 查找Group # Test Results段落
            test_results_paragraph = self._template_service.find_group_test_results_paragraph(word_doc)
            if not test_results_paragraph:
                logger.warning("未找到Group # Test Results段落")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到Group # Test Results段落")
                return False
            
            # 根据组别数量复制表格
            if status_callback:
                self._safe_callback_call(status_callback, "正在复制Test Result表格...")
            
            if len(sorted_groups) > 1:
                self._template_service.duplicate_test_result_tables(word_doc, len(sorted_groups))
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 60)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在填充Test Result表格...")
            
            # 填充每个组别的表格
            start_table_index = self._template_service.find_first_test_result_table_index(word_doc)
            if start_table_index == -1:
                logger.error("未找到第一个Test Result表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "错误: 未找到第一个Test Result表格")
                return False
            
            for i, group_name in enumerate(sorted_groups):
                table_index = start_table_index + i
                if table_index <= word_doc.Tables.Count:
                    table = word_doc.Tables(table_index)
                    
                    # 更新表格前的标题
                    self._template_service.update_group_title(word_doc, table_index, group_name)
                    
                    # 获取该组别的步骤数据
                    steps = matrix_structure.get_group_steps(group_name)
                    
                    # 填充表格
                    self._fill_test_result_table_from_dict(table, steps)
                    
                    logger.info(f"已填充组别 {group_name} 的表格，包含 {len(steps)} 个步骤")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 90)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在保存文档...")
            
            # 根据参数决定是否保存文档
            if should_save_doc:
                word_doc.Save()
                logger.info(f"文档已保存: {document_path}")
            else:
                logger.info(f"跳过保存文档，由调用者处理: {document_path}")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 100)
            
            if status_callback:
                self._safe_callback_call(status_callback, "处理完成！Test Result表格已成功生成。")
            
            logger.info(f"Test Result表格生成完成，共处理{len(sorted_groups)}个组别")
            return True
            
        except Exception as e:
            logger.error(f"生成Test Result表格时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            if status_callback:
                self._safe_callback_call(status_callback, f"错误: {str(e)}")
            return False
        finally:
            try:
                if owns_word_doc and word_doc is not None:
                    word_doc.Close(SaveChanges=False)
            except Exception as e:
                logger.error(f"关闭 Test Result 文档时出错: {e}")

            # 只有关闭自己创建的 session
            try:
                if word_session is not None:
                    word_session.release()
            except Exception as e:
                logger.error(f"释放 Word session 时出错: {e}")

    def _fill_test_result_table_from_dict(self, table, step_list: List[Dict[str, Any]]):
        """
        根据步骤字典列表填充Test Result表格
        
        Args:
            table: Word表格对象
            step_list: 步骤列表
        """
        # 确保表格有足够的行数（标题行 + 步骤数）
        required_rows = len(step_list) + 1  # +1 for header
        current_rows = table.Rows.Count
        
        # 调整表格行数
        if required_rows > current_rows:
            for _ in range(required_rows - current_rows):
                table.Rows.Add()
        elif required_rows < current_rows:
            for _ in range(current_rows - required_rows):
                if table.Rows.Count > 1:
                    table.Rows(table.Rows.Count).Delete()
        
        # 确保表格有6列
        required_cols = 6
        current_cols = table.Columns.Count
        if current_cols < required_cols:
            for _ in range(required_cols - current_cols):
                table.Columns.Add()
        elif current_cols > required_cols:
            for _ in range(current_cols - required_cols):
                if table.Columns.Count > required_cols:
                    table.Columns(table.Columns.Count).Delete()
        
        # 跳过标题行，只填充数据行
        for i, step in enumerate(step_list):
            row_index = i + 2  # +2 because index starts at 1 and first row is header
            row = table.Rows(row_index)
            
            step_number = step.get('StepNumber', f'Step {i + 1}')
            
            test_item = step.get('Test', '')
            requirement = step.get('Requirement', '')
            step_desc = step.get('StepDescription', '')

            filtered_requirement = self._filter_requirement(requirement)
            
            processed_requirement = self._replace_greater_lesser_symbols(filtered_requirement)
            processed_requirement = self._clean_text(processed_requirement)
            
            logger.debug(
                "Requirement pipeline: requirement=%r, filtered=%r, processed=%r",
                requirement,
                filtered_requirement,
                processed_requirement,
            )
            
            cells = [step_number, test_item, requirement, step_desc, processed_requirement, 'Pass']
            
            for j, cell_value in enumerate(cells):
                if j + 1 <= row.Cells.Count:
                    cell_content = str(cell_value) if cell_value else ''
                    cell_content = cell_content.rstrip('\x07')
                    row.Cells(j + 1).Range.Text = cell_content

    def _natural_sort_groups(self, groups: List[str]) -> List[str]:
        """
        对组别名称进行自然排序（数值优先）
        """
        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]

        return sorted(groups, key=alphanum_key)
