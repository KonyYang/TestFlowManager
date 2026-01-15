"""
Test Result服务模块
提供生成Test Result表格的业务逻辑服务
"""

from typing import Dict, Any, List, Optional
from src.core.logger import logger
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
import re
import os


class TestResultService:
    """
    Test Result服务类
    提供生成Test Result表格的业务逻辑服务
    """

    def __init__(self):
        """初始化Test Result服务"""
        pass

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
            # 检查是否是Qt信号
            # Qt信号对象通常有emit方法
            if hasattr(callback, 'emit'):
                # 这是一个Qt信号，使用emit方法调用
                return callback.emit(*args)
            else:
                # 这是一个普通函数，直接调用
                return callback(*args)
        except Exception as e:
            logger.error(f"回调调用失败: {e}")
            return None

    def _replace_greater_lesser_symbols(self, text: str) -> str:
        """
        替换文本中的大于小于符号后跟随的数字和小数点为下划线
        
        Args:
            text: 输入文本
            
        Returns:
            处理后的文本
        """
        if not text or not isinstance(text, str):
            return text
        
        # 使用正则表达式匹配 ≥ 或 ≤ 符号后跟随的数字和小数点
        # 例如：≥1.2.3 → ≥_._._
        pattern = r'([≥≤])((?:\d+\.?)+)'
        def replace_numbers(match):
            symbol = match.group(1)
            numbers = match.group(2)
            # 将数字和小数点替换为下划线
            processed_numbers = re.sub(r'\d+|\.', '_', numbers)
            return symbol + processed_numbers
        
        result = re.sub(pattern, replace_numbers, text)
        return result

    def _clean_text(self, text: str) -> str:
        """
        清理文本：移除首尾空格，压缩内部连续空格
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        if not text or not isinstance(text, str):
            return text
        
        # 移除首尾空格并压缩内部连续空格
        cleaned = ' '.join(text.split())
        return cleaned

    def _filter_requirement(self, requirement: str) -> str:
        """
        过滤Requirement值：若等于"No detrimental condition"或"No damage"，则返回空字符串
        
        Args:
            requirement: 原始Requirement值
            
        Returns:
            过滤后的Requirement值
        """
        if not requirement or not isinstance(requirement, str):
            return requirement
        
        # requirement_lower = requirement.lower().strip()
        # if requirement_lower in ['no detrimental condition', 'no damage']:
        #     return ''
        
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
                # 使用传入的Word文档实例
                word_doc = word_doc_instance
                word_app = word_doc.Application
            elif word_app_instance is not None:
                # 使用传入的Word应用程序实例
                word_app = word_app_instance
                word_doc = word_app.Documents.Open(document_path)
            else:
                # 使用win32com打开Word文档
                import win32com.client
                word_app = win32com.client.Dispatch("Word.Application")
                word_app.Visible = False  # 隐藏Word窗口
                word_app.DisplayAlerts = False  # 关闭警告提示
                
                word_doc = word_app.Documents.Open(document_path)
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
            test_results_paragraph = self._find_group_test_results_paragraph(word_doc)
            if not test_results_paragraph:
                logger.warning("未找到Group # Test Results段落")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到Group # Test Results段落")
                return False
            
            # 根据组别数量复制表格
            if status_callback:
                self._safe_callback_call(status_callback, "正在复制Test Result表格...")
            
            # 复制表格（如果有多于1个组别，则需要复制）
            if len(sorted_groups) > 1:
                self._duplicate_test_result_tables(word_doc, len(sorted_groups))
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 60)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在填充Test Result表格...")
            
            # 填充每个组别的表格
            # 从第4个表格开始（假设前3个不是Test Result表格）
            start_table_index = self._find_first_test_result_table_index(word_doc)
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
                    self._update_group_title(word_doc, table_index, group_name)
                    
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
            # 只有在我们创建了Word应用实例时才关闭它
            # 如果使用了传入的实例，不要关闭它，因为它可能还在其他地方使用
            # 同样，文档实例也不应关闭，因为它由调用者管理
            try:
                if word_app_instance is None and word_doc_instance is None and word_app is not None:
                    word_app.Quit()
            except:
                pass

    def _find_group_test_results_paragraph(self, word_doc):
        """
        查找带有"Group # Test Results"的段落
        
        Args:
            word_doc: Word文档对象
            
        Returns:
            段落对象或None
        """
        for i in range(1, word_doc.Paragraphs.Count + 1):
            paragraph = word_doc.Paragraphs(i)
            para_text = paragraph.Range.Text.strip()
            
            # 检查段落文本是否包含"Group # Test Results"（不区分大小写）
            if 'Group # Test Results' in para_text:
                logger.info(f"找到Group # Test Results段落: {para_text}")
                return paragraph
        
        logger.warning("未找到Group # Test Results段落")
        return None

    def _find_first_test_result_table_index(self, word_doc):
        """
        查找第一个Test Result表格的索引
        
        Args:
            word_doc: Word文档对象
            
        Returns:
            表格索引（从1开始），如果未找到返回-1
        """
        # 查找Group # Test Results段落
        test_results_para = self._find_group_test_results_paragraph(word_doc)
        if not test_results_para:
            return -1
        
        # 获取TEST RESULTS段落的位置
        paragraph_end_pos = test_results_para.Range.End
        
        # 查找紧跟在此段落后的第一个表格
        for i in range(1, word_doc.Tables.Count + 1):
            table = word_doc.Tables(i)
            if table.Range.Start >= paragraph_end_pos:
                # 返回第一个在TEST RESULTS段落之后的表格
                logger.info(f"找到第一个Test Result表格，索引: {i}")
                return i
        
        # 如果找不到紧跟的表格，返回第4个表格作为默认值
        if word_doc.Tables.Count >= 4:
            logger.info("使用第4个表格作为第一个Test Result表格")
            return 4
        
        logger.warning("未找到Test Result表格")
        return -1

    def _duplicate_test_result_tables(self, word_doc, needed_count: int):
        """
        根据所需数量复制Test Result表格
        
        Args:
            word_doc: Word文档对象
            needed_count: 需要的表格总数
        """
        # 模板从第4个表格开始
        first_table_index = 4
        if first_table_index > word_doc.Tables.Count:
            logger.warning("文档中没有第 {} 个表格，无法复制".format(first_table_index))
            return
        
        # 获取第4个表格
        table4 = word_doc.Tables(first_table_index)
        
        # 获取第4个表格前的段落（包含"Group # Test Results"）
        table4_start_pos = table4.Range.Start
        search_range = word_doc.Range(0, table4_start_pos)
        
        # 查找包含"Group # Test Results"的段落
        found_range = search_range.Duplicate
        found = found_range.Find.Execute(FindText="Group # Test Results", Forward=True)
        
        if not found:
            logger.warning("未找到包含 'Group # Test Results' 的段落")
            # 如果没找到特定段落，使用原来的简单方法
            # 需要复制的次数 = 总数 - 1（因为已有1个模板）
            copy_times = needed_count - 1
            if copy_times <= 0:
                return  # 不需要复制
            
            # 复制表格
            for i in range(copy_times):
                # 复制第一个表格
                table4.Range.Copy()
                
                # 找到插入位置（在第4个表格之后）
                table4_end_pos = table4.Range.End
                # 在第4个表格后插入一个空白段落
                doc_range = word_doc.Range(table4_end_pos, table4_end_pos)
                doc_range.InsertParagraph()
                # 获取刚插入的段落位置作为粘贴位置
                paste_pos = table4_end_pos + 1  # 段落标记位置
                paste_range = word_doc.Range(paste_pos, paste_pos)
                
                paste_range.Paste()
                
                logger.info("已复制第 {} 个Test Result表格".format(i + 1))
            return
        
        # 确定要复制的完整范围（标题段落 + 第4个表格）
        copy_start_pos = found_range.Start
        copy_end_pos = table4.Range.End
        
        # 创建复制范围
        copy_range = word_doc.Range(copy_start_pos, copy_end_pos)
        
        # 需要复制的次数 = 总数 - 1（因为已有1个模板）
        copy_times = needed_count - 1
        if copy_times <= 0:
            return  # 不需要复制
        
        # 复制表格和标题段落
        for i in range(copy_times):
            # 获取第4个表格的结束位置
            table4_end_pos = table4.Range.End
            # 在第4个表格后插入一个空白段落
            doc_range = word_doc.Range(table4_end_pos, table4_end_pos)
            doc_range.InsertParagraph()
            # 获取刚插入的段落位置作为粘贴位置
            paste_pos = table4_end_pos + 1  # 段落标记位置
            paste_range = word_doc.Range(paste_pos, paste_pos)
            
            # 粘贴复制的内容
            copy_range.Copy()
            paste_range.Paste()
            
            logger.info("已复制第 {} 个Test Result表格及其标题".format(i + 1))

    def _update_group_title(self, word_doc, table_index: int, group_name: str):
        """
        更新表格前的组别标题
        
        Args:
            word_doc: Word文档对象
            table_index: 表格索引
            group_name: 组别名称
        """
        # 从文档开头到表格开始位置之间搜索
        table = word_doc.Tables(table_index)
        search_range = word_doc.Range(0, table.Range.Start)
        
        # 查找包含"Group # Test Results"的段落
        found_range = search_range.Duplicate
        found = found_range.Find.Execute(FindText="Group # Test Results", Forward=True)
        
        if found:
            # 替换#为实际组名
            new_text = found_range.Text.replace('#', group_name)
            found_range.Text = new_text
            logger.info("已更新组别标题: {}".format(new_text))
            return
        
        # 如果没有找到确切的模板文本，尝试查找其他可能的格式
        # 遍历搜索范围内的所有段落
        for i in range(1, search_range.Paragraphs.Count + 1):
            try:
                paragraph = search_range.Paragraphs(i)
                para_text = paragraph.Range.Text.strip()
                
                # 查找包含"Group # Test Results"的段落
                if 'Group # Test Results' in para_text or ('Group' in para_text and 'Test Results' in para_text and '#' in para_text):
                    # 替换#为实际组名
                    new_text = para_text.replace('#', group_name)
                    paragraph.Range.Text = new_text
                    logger.info("已更新组别标题: {}".format(new_text))
                    return
            except Exception as e:
                logger.warning("处理段落 {} 时出错: {}".format(i, e))
                continue

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
            # 添加新行
            for _ in range(required_rows - current_rows):
                table.Rows.Add()
        elif required_rows < current_rows:
            # 删除多余行（保留标题行）
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
        # 保持模板中原有的标题行格式和内容不变
        for i, step in enumerate(step_list):
            row_index = i + 2  # +2 because index starts at 1 and first row is header
            row = table.Rows(row_index)
            
            # 生成步骤号（如果没有提供）
            step_number = step.get('StepNumber', f'Step {i + 1}')
            
            # 获取其他字段
            test_item = step.get('Test', '')
            requirement = step.get('Requirement', '')
            step_desc = step.get('StepDescription', '')

            # 过滤requirement
            filtered_requirement = self._filter_requirement(requirement)
            
            # 处理requirement，将/后的数字替换为_
            processed_requirement = self._replace_greater_lesser_symbols(filtered_requirement)
            processed_requirement = self._clean_text(processed_requirement)
            
            # 打印获取的值
            print(f"DEBUG: requirement='{requirement}', filtered_requirement='{filtered_requirement}', processed_requirement='{processed_requirement}'")
            
            # 填充单元格
            cells = [step_number, test_item, requirement, step_desc, processed_requirement, 'Pass']
            
            for j, cell_value in enumerate(cells):
                if j + 1 <= row.Cells.Count:
                    cell_content = str(cell_value) if cell_value else ''
                    # 移除特殊字符
                    cell_content = cell_content.rstrip('\x07')  # 移除段落标记
                    row.Cells(j + 1).Range.Text = cell_content

    def _natural_sort_groups(self, groups: List[str]) -> List[str]:
        """
        对组别名称进行自然排序（数值优先）
        
        Args:
            groups: 组别名称列表
            
        Returns:
            排序后的组别名称列表
        """
        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]

        return sorted(groups, key=alphanum_key)