"""
Test Spec Tables服务模块
提供填充Test Description和Test Method表格的业务逻辑服务
"""

from typing import Dict, Any, Callable, Optional
from src.core.logger import logger
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from docx import Document
from docx.shared import Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
from docx.text.paragraph import Paragraph
from docx.table import Table
import re
import inspect


class TestSpecTablesService:
    """
    Test Spec Tables服务类
    提供填充Test Description和Test Method表格的业务逻辑服务
    """

    def __init__(self):
        """初始化Test Spec Tables服务"""
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

    def fill_test_description_and_methods(
        self, 
        document_path: str, 
        matrix_data_structure: MatrixDataStructure,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        填充Test Description和Test Method表格
        
        Args:
            document_path: Word文档路径
            matrix_data_structure: Matrix数据结构
            progress_callback: 进度回调函数
            status_callback: 状态回调函数
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始填充Test Description和Test Method表格，文档路径: {document_path}")
        try:
            if status_callback:
                self._safe_callback_call(status_callback, "正在打开文档...")
            
            # 检查文档是否存在
            import os
            if not os.path.exists(document_path):
                logger.error(f"文档不存在: {document_path}")
                if status_callback:
                    self._safe_callback_call(status_callback, f"错误: 文档不存在 - {document_path}")
                return False
            
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
            all_groups = matrix_data_structure.get_all_groups()
            logger.info(f"从Matrix数据结构获取到 {len(all_groups)} 个组别")
            if not all_groups:
                logger.warning("Matrix数据结构中没有找到任何组别")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: Matrix数据中没有找到任何组别")
                return False
            
            # 合并所有组别的步骤数据
            all_steps = []
            for group_name in all_groups:
                steps = matrix_data_structure.get_group_steps(group_name)
                logger.info(f"组别 {group_name} 包含 {len(steps)} 个步骤")
                # 为每个步骤添加组别信息
                for step in steps:
                    step_with_group = step.copy()
                    step_with_group['GroupName'] = group_name
                    all_steps.append(step_with_group)
            
            if not all_steps:
                logger.warning("所有组别中都没有找到任何步骤数据")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 所有组别中都没有找到任何步骤数据")
                return False
            
            # 过滤掉"Sample size"行之后的数据
            filtered_steps = []
            for step in all_steps:
                test_item = step.get("Test", "").lower()
                if test_item.startswith("sample"):
                    logger.info(f"遇到Sample行，停止添加后续步骤，当前已添加 {len(filtered_steps)} 个步骤")
                    break  # 遇到Sample行则停止添加
                filtered_steps.append(step)
            
            if len(filtered_steps) != len(all_steps):
                logger.info(f"过滤后剩余 {len(filtered_steps)} 个步骤（原 {len(all_steps)} 个）")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 30)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找TEST DESCRIPTION段落...")
            
            # 使用win32com方式查找并填充Test Description表格
            # 通过查找TEST DESCRIPTION表格并填充
            description_table = self._find_table_by_paragraph_win32com(word_doc, "TEST DESCRIPTION")
            if description_table:
                logger.info("找到TEST DESCRIPTION表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Description表格...")
                
                # 将查找到的表格对象直接传递给_fill_description_table方法，避免重复查找
                self._fill_description_table(description_table, document_path, word_app)
            else:
                logger.warning("未找到TEST DESCRIPTION表格")
                if status_callback:
                    status_callback("警告: 未找到TEST DESCRIPTION表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 60)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找TEST METHODS/REQUIREMENTS段落...")
            
            # 查找并填充Test Method表格
            method_table = self._find_table_by_paragraph_win32com(word_doc, "TEST METHODS/REQUIREMENTS")
            if method_table:
                logger.info("找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Method表格...")
                
                # 使用win32com填充Test Method表格
                self._fill_method_table_win32com(method_table, filtered_steps)
            else:
                logger.warning("未找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到TEST METHODS/REQUIREMENTS表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 90)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在保存文档...")
            
            # 保存文档
            word_doc.Save()
            logger.info(f"文档已保存: {document_path}")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 100)
            
            if status_callback:
                self._safe_callback_call(status_callback, "处理完成！表格已成功填充。")
            
            logger.info(f"Test Description和Test Method表格填充完成，共处理{len(filtered_steps)}个步骤")
            return True
            
        except Exception as e:
            logger.error(f"填充Test Description和Test Method表格时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            if status_callback:
                self._safe_callback_call(status_callback, f"错误: {str(e)}")
            return False
        finally:
            # 关闭Word应用
            try:
                word_app.Quit()
            except:
                pass

    def _find_table_by_paragraph(self, doc, target_text: str) -> Optional[Table]:
        """
        根据段落文本查找对应的表格
        
        Args:
            doc: Word文档对象
            target_text: 目标段落文本
            
        Returns:
            找到的表格对象，如果未找到则返回None
        """
        logger.info(f"正在查找包含 '{target_text}' 的段落...")
        # 遍历所有段落
        for i, paragraph in enumerate(doc.paragraphs):
            # 检查段落文本是否包含目标文本且为粗体大写格式
            para_text = paragraph.text.strip()
            if target_text.upper() in para_text.upper() and self._is_bold_uppercase(paragraph):
                logger.info(f"找到目标段落: {para_text}")
                
                # 查找该段落之后的表格
                # 遍历文档的XML元素，查找紧跟在该段落之后的表格
                body_elements = list(doc.element.body)
                para_element = paragraph._element
                
                para_idx = -1
                for idx, elem in enumerate(body_elements):
                    if elem == para_element:
                        para_idx = idx
                        break
                
                # 在段落之后查找表格元素
                if para_idx != -1:
                    for j in range(para_idx + 1, len(body_elements)):
                        element = body_elements[j]
                        # 检查是否为表格元素
                        if element.tag.endswith('tbl'):
                            # 创建表格对象并返回
                            from docx.table import Table
                            table = Table(element, doc)
                            logger.info(f"找到紧跟在段落后的表格")
                            return table
        
        # 如果通过段落查找失败，尝试通过表格内容查找
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if target_text.upper() in cell.text.upper() and self._is_bold_uppercase_in_cell(cell):
                        logger.info(f"在表格中找到目标文本: {target_text}")
                        return table
        
        logger.warning(f"未找到包含 '{target_text}' 的段落或表格")
        return None

    def _is_bold_uppercase(self, paragraph: Paragraph) -> bool:
        """
        检查段落是否为粗体且全部大写
        
        Args:
            paragraph: 段落对象
            
        Returns:
            是否为粗体且全部大写
        """
        try:
            # 检查段落是否包含粗体文本
            for run in paragraph.runs:
                if run.bold and run.text.isupper():
                    return True
            # 如果没有runs，直接检查文本是否大写
            return paragraph.text.isupper()
        except:
            return paragraph.text.isupper()

    def _is_bold_uppercase_in_cell(self, cell) -> bool:
        """
        检查单元格中是否包含粗体且全部大写的文本
        
        Args:
            cell: 单元格对象
            
        Returns:
            是否包含粗体且全部大写的文本
        """
        try:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    if run.bold and run.text.isupper():
                        return True
            return False
        except:
            return True

    def _find_table_by_paragraph_win32com(self, word_doc, paragraph_keyword: str):
        """
        使用win32com在Word文档中根据段落关键字查找紧跟其后的表格
        
        Args:
            word_doc: win32com Word文档对象
            paragraph_keyword: 段落中的关键字（如"TEST DESCRIPTION"）
            
        Returns:
            找到的表格对象，如果未找到则返回None
        """
        logger.info(f"使用win32com查找关键字 '{paragraph_keyword}' 后的表格")
        
        # 遍历文档中的所有段落
        for i in range(1, word_doc.Paragraphs.Count + 1):
            paragraph = word_doc.Paragraphs(i)
            para_text = paragraph.Range.Text.strip()
            
            # 检查段落文本是否包含目标关键字
            if paragraph_keyword.upper() in para_text.upper():
                # 检查段落是否为粗体且有下划线
                if paragraph.Range.Font.Bold and paragraph.Range.Font.Underline:
                    logger.info(f"找到包含 '{paragraph_keyword}' 的粗体下划线段落: {para_text}")
                    
                    # 获取文档中所有表格的位置
                    table_positions = []
                    for j, doc_table in enumerate(word_doc.Tables):
                        # 记录表格在文档中的位置
                        table_positions.append((doc_table.Range.Start, doc_table))
                    
                    # 按表格起始位置排序
                    table_positions.sort(key=lambda x: x[0])
                    
                    # 查找紧跟在此段落后的第一个表格
                    paragraph_end_pos = paragraph.Range.End
                    for pos, table in table_positions:
                        if pos >= paragraph_end_pos:
                            logger.info(f"找到紧跟在段落后的表格")
                            return table
        
        # 如果通过段落查找失败，尝试通过表格内容查找
        for j, doc_table in enumerate(word_doc.Tables):
            # 检查表格第一行的单元格内容
            if doc_table.Rows.Count > 0:
                first_row = doc_table.Rows(1)
                for cell in first_row.Cells:
                    cell_text = cell.Range.Text.strip()
                    if paragraph_keyword.upper() in cell_text.upper():
                        # 检查字体是否为粗体
                        if cell.Range.Font.Bold:
                            logger.info(f"在表格中找到包含 '{paragraph_keyword}' 的单元格")
                            return doc_table
        
        logger.warning(f"未找到关键字 '{paragraph_keyword}' 后的表格")
        return None

    def _apply_table_formatting(self, target_table):
        """
        应用表格格式设置，包括边框、自动调整和垂直对齐
        
        Args:
            target_table: Word表格对象（win32com对象）
        """
        try:
            # 设置表格边框线
            target_table.Borders.Enable = True
            # 设置边框线宽
            for border_id in range(7):  # Word中边框的ID范围是0-6
                target_table.Borders(border_id).Visible = True
                target_table.Borders(border_id).LineWidth = 0.5  # 设置线宽

            # 设置表格根据窗口自动调整
            target_table.PreferredWidthType = 3  # wdPreferredWidthType = wdPreferredWidthPercent
            target_table.AllowAutoFit = True
            target_table.AutoFitBehavior(1)  # wdAutoFitWindow - 根据窗口自动调整

            # 设置所有单元格垂直对齐方式为居中
            target_table.CellRange.VerticalAlignment = 1  # wdCellAlignVerticalCenter = 1
        except Exception as e:
            logger.warning(f"设置表格格式时出错: {e}")
    
    def _fill_description_table(self, target_table, document_path: str, word_app_instance=None) -> None:
        """
        填充Test Description表格
        
        根据要求：动态获取Matrix页面表格中的首列和第6列及之后的组别列，
        行截止到"Time"所在行的上一行，列截止于"Notes"所在列的前一列。
        表格列数根据组别列数量动态调整，第一列为Test Item，其余列为各组别数据。
        
        Args:
            target_table: Word表格对象（win32com对象）
            document_path: Word文档路径
            word_app_instance: Word应用程序实例，如果为None则创建新的实例
        """
        logger.info("开始填充Test Description表格")
        
        # 从MatrixService获取当前数据
        from src.features.matrix.service.matrix_service import MatrixService
        matrix_service = MatrixService()
        
        # 获取表头行
        header_row = matrix_service.data_model.headers if hasattr(matrix_service.data_model, 'headers') else []
        
        logger.info(f"Matrix表头: {header_row}")
        
        # 确定列范围：从第6列（索引5）开始，到"Notes"列的前一列结束（不包含Notes列）
        start_col_index = 5  # 第6列开始（固定）
        end_col_index = len(header_row) - 1  # 默认为最后一列
        
        for i, col_header in enumerate(header_row):
            if col_header.lower() == "notes":
                end_col_index = i - 1  # 截止到"Notes"列的前一列（不包含Notes列）
                logger.info(f"找到Notes列在索引 {i}，所以截止到索引 {end_col_index}")
                break
        
        # 获取组别列数量（注意：这里计算的是需要填充的列数，不包含Notes列）
        group_columns_count = max(0, end_col_index - start_col_index)
        if group_columns_count < 0:
            group_columns_count = 0
        
        logger.info(f"组别列数量: {group_columns_count}, 起始列索引: {start_col_index}, 结束列索引: {end_col_index}")
        
        # 总列数 = 首列(Test Item) + 组别列数量
        target_cols = 1 + group_columns_count  # 1为Test Item列，其余为组别列
        
        # 获取数据行，直到"Time"行的上一行
        data_rows = matrix_service.data_model.rows if hasattr(matrix_service.data_model, 'rows') else []
        rows_to_process = []
        
        time_row_found = False
        for row in data_rows:
            if len(row) > 0 and row[0].lower().startswith("time"):
                time_row_found = True
                logger.info(f"找到Time行: {row[0]}")
                break
            rows_to_process.append(row)

        logger.info(f"处理 {len(rows_to_process)} 行数据，包含标题行")
        
        # 使用现有的Word应用程序实例或创建新的实例
        import win32com.client
        if word_app_instance is None:
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False  # 隐藏Word窗口
            word_app.DisplayAlerts = False  # 关闭警告提示
            need_to_quit = True  # 标记需要在退出时关闭应用
        else:
            word_app = word_app_instance
            word_app.DisplayAlerts = False  # 关闭警告提示
            need_to_quit = False  # 不需要关闭外部传入的应用实例
        
        try:
            # 打开文档
            word_doc = word_app.Documents.Open(document_path)
            
            # 检查是否成功找到表格
            if not target_table:
                logger.warning("未找到TEST DESCRIPTION表格")
                return
            
            # 调整表格行数以匹配数据行数
            current_rows = target_table.Rows.Count
            required_rows = len(rows_to_process)
            logger.info(f"当前表格行数: {current_rows}, 需要行数: {required_rows}")
            
            if required_rows > current_rows:
                # 添加新行，同时保持原有格式
                for _ in range(required_rows - current_rows):
                    target_table.Rows.Add()
                logger.info(f"添加了 {required_rows - current_rows} 行")
            elif required_rows < current_rows:
                # 删除多余行，但至少保留1行
                for _ in range(current_rows - required_rows):
                    if target_table.Rows.Count > required_rows and required_rows > 0:
                        target_table.Rows(target_table.Rows.Count).Delete()
                logger.info(f"删除了 {current_rows - required_rows} 行")
        
            # 调整表格列数以匹配组别列数量+1（第一列为Test Item）
            logger.info(f"当前表格列数: {target_table.Columns.Count}, 需要列数: {target_cols}")
            
            current_cols = target_table.Columns.Count
            if current_cols < target_cols:
                # 添加新列，同时保持原有格式
                for _ in range(target_cols - current_cols):
                    target_table.Columns.Add()
                logger.info(f"添加了 {target_cols - current_cols} 列")
            elif current_cols > target_cols:
                for _ in range(current_cols - target_cols):
                    if target_table.Columns.Count > target_cols:
                        target_table.Columns(target_table.Columns.Count).Delete()
                logger.info(f"删除了 {current_cols - target_cols} 列")
            
            logger.info(f"最终表格尺寸 - 行数: {target_table.Rows.Count}, 列数: {target_table.Columns.Count}")
            
            # 填充数据（包含标题行）
            for i, row_data in enumerate(rows_to_process):
                actual_row_index = i  # 从0开始
                if actual_row_index < target_table.Rows.Count:
                    row = target_table.Rows(actual_row_index + 1)  # Win32COM索引从1开始
                    
                    # 第一列：Test Item（来自Matrix的第一列）
                    if len(row_data) > 0:
                        test_item = row_data[0] if row_data[0] else ""
                        if test_item:
                            row.Cells(1).Range.Text = str(test_item).rstrip('\x07')  # 移除段落标记
                            logger.debug(f"第{actual_row_index+1}行第1列填充: {test_item}")
                    
                    # 其余列：各组别列内容（从第6列开始到Notes列前一列）
                    for j in range(group_columns_count):
                        col_index = start_col_index + j  # 固定从索引5（第6列）开始
                        if col_index < len(row_data) and row_data[col_index]:
                            cell_content = str(row_data[col_index]).rstrip('\x07')  # 移除段落标记
                            # 确保单元格存在
                            if j + 2 <= row.Cells.Count:
                                row.Cells(j + 2).Range.Text = cell_content  # Win32COM索引从1开始，第一列是索引1
                                logger.debug(f"第{actual_row_index+1}行第{j+2}列填充: {cell_content}")
                    
                    # 保持原有的单元格格式，而不是强制设置格式
                    # 只对内容进行处理，保留原始表格样式
                    actual_cols = min(target_cols, row.Cells.Count)
                    for j in range(actual_cols):
                        # 确保单元格存在
                        if j + 1 <= row.Cells.Count:
                            cell = row.Cells(j + 1)  # Win32COM索引从1开始
                            # 保留原有格式，只做必要的格式调整
                            # 保持原有的字体、对齐方式等格式
                            try:
                                # 保持原有的格式，仅在必要时设置
                                pass
                            except:
                                logger.warning(f"无法保留第{actual_row_index+1}行第{j+1}列的格式")
            
            # 应用表格格式设置
            self._apply_table_formatting(target_table)

            # 保存文档
            word_doc.Save()
            logger.info(f"文档已保存: {document_path}")
        
        except Exception as e:
            logger.error(f"使用win32com操作Word文档时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
        finally:
            # 只在需要时关闭Word应用（即外部没有传入实例的情况下）
            if need_to_quit:
                try:
                    word_app.Quit()
                except:
                    pass

    def _fill_method_table_win32com(self, table, steps: list) -> None:
        """
        使用win32com填充Test Method表格

        根据要求：表格只有两行三列，需要依据matrix数据结构的行数和列数进行增减。
        把matrix的第1,3,4,5列（Test, TestMethod, Condition, Requirement），
        行截取到"Sample size"前面一行填充进来。

        Args:
            table: Word表格对象（win32com对象）
            steps: 步骤数据列表
        """
        logger.info(f"开始使用win32com填充Test Method表格，共{len(steps)}个步骤")

        # 调整表格行数以匹配步骤数量
        current_rows = table.Rows.Count
        if len(steps) > current_rows:
            # 添加行
            for _ in range(len(steps) - current_rows):
                table.Rows.Add()
            logger.info(f"添加了 {len(steps) - current_rows} 行")
        elif len(steps) < current_rows:
            # 删除多余行（从后往前删除）
            for _ in range(current_rows - len(steps)):
                if table.Rows.Count > len(steps) and len(steps) > 0:
                    table.Rows(table.Rows.Count).Delete()
            logger.info(f"删除了 {current_rows - len(steps)} 行")

        # 确保每行有3列
        for row_idx in range(1, min(len(steps) + 1, table.Rows.Count + 1)):  # 遍历所有需要填充的行
            current_cols = table.Rows(row_idx).Cells.Count
            if current_cols < 3:
                # 添加列直到有3列
                for _ in range(3 - current_cols):
                    table.Columns.Add()
                logger.info(f"添加了 {3 - current_cols} 列")
            elif current_cols > 3:
                # 删除多余列（保留前3列）
                for _ in range(current_cols - 3):
                    if table.Columns.Count > 3:
                        table.Columns(table.Columns.Count).Delete()
                logger.info(f"删除了 {current_cols - 3} 列")

        logger.info(f"最终表格行数: {table.Rows.Count}, 列数: {table.Columns.Count}")

        # 填充数据 - 使用Matrix的第1,3,4列（Test, TestMethod, Condition）
        for i, step in enumerate(steps):
            if i < table.Rows.Count:
                row = table.Rows(i + 1)  # Win32COM索引从1开始

                # 确保有3列
                if row.Cells.Count >= 3:
                    # 第一列：Test Item
                    test_item = step.get("Test", "")
                    if test_item:  # 只有当内容不为空时才设置
                        row.Cells(1).Range.Text = str(test_item).rstrip('\x07')  # 移除段落标记
                        logger.debug(f"第{i+1}行第1列填充: {test_item}")

                    # 第二列：Test Method
                    test_method = step.get("TestMethod", "")
                    if test_method:  # 只有当内容不为空时才设置
                        row.Cells(2).Range.Text = str(test_method).rstrip('\x07')  # 移除段落标记
                        logger.debug(f"第{i+1}行第2列填充: {test_method}")

                    # 第三列：Condition
                    condition = step.get("Condition", "")
                    if condition:  # 只有当内容不为空时才设置
                        row.Cells(3).Range.Text = str(condition).rstrip('\x07')  # 移除段落标记
                        logger.debug(f"第{i+1}行第3列填充: {condition}")

        # 应用表格格式设置
        self._apply_table_formatting(table)

        logger.info("Test Method表格填充完成")

    def _fill_method_table(self, table, steps: list) -> None:
        """
        填充Test Method表格

        根据要求：表格只有两行三列，需要依据matrix数据结构的行数和列数进行增减。
        把matrix的第1,3,4,5列（Test, TestMethod, Condition, Requirement），
        行截取到"Sample size"前面一行填充进来。

        Args:
            table: Word表格对象（python-docx对象）
            steps: 步骤数据列表
        """
        logger.info(f"开始填充Test Method表格，共{len(steps)}个步骤")

        # 调整表格行数以匹配步骤数量
        current_rows = len(table.rows)
        if len(steps) > current_rows:
            # 添加行
            for _ in range(len(steps) - current_rows):
                table.add_row()
            logger.info(f"添加了 {len(steps) - current_rows} 行")
        elif len(steps) < current_rows:
            # 删除多余行（从后往前删除）
            for _ in range(current_rows - len(steps)):
                if len(table.rows) > len(steps) and len(steps) > 0:
                    # 通过删除行的XML元素来删除行
                    table._tbl.remove(table.rows[-1]._tr)
            logger.info(f"删除了 {current_rows - len(steps)} 行")

        # 确保每行有3列
        for row in table.rows:
            current_cols = len(row.cells)
            if current_cols < 3:
                # 添加列直到有3列
                for _ in range(3 - current_cols):
                    row.cells[-1]._tc.addnext(row.cells[-1]._tc.clone())
                logger.info(f"添加了 {3 - current_cols} 列")
            elif current_cols > 3:
                # 删除多余列（保留前3列）
                for _ in range(current_cols - 3):
                    if len(row.cells) > 3:
                        row._tr.remove(row.cells[-1]._tc)
                logger.info(f"删除了 {current_cols - 3} 列")

        logger.info(f"最终表格行数: {len(table.rows)}, 列数: {len(table.rows[0].cells) if table.rows else 0}")

        # 填充数据 - 使用Matrix的第1,3,4列（Test, TestMethod, Condition）
        for i, step in enumerate(steps):
            if i < len(table.rows):
                row = table.rows[i]

                # 确保有3列
                if len(row.cells) >= 3:
                    # 第一列：Test Item
                    test_item = step.get("Test", "")
                    if test_item:  # 只有当内容不为空时才设置
                        row.cells[0].text = str(test_item)
                        logger.debug(f"第{i+1}行第1列填充: {test_item}")

                    # 第二列：Test Method
                    test_method = step.get("TestMethod", "")
                    if test_method:  # 只有当内容不为空时才设置
                        row.cells[1].text = str(test_method)
                        logger.debug(f"第{i+1}行第2列填充: {test_item}")

                    # 第三列：Condition
                    condition = step.get("Condition", "")
                    if condition:  # 只有当内容不为空时才设置
                        row.cells[2].text = str(condition)
                        logger.debug(f"第{i+1}行第3列填充: {condition}")

        logger.info("Test Method表格填充完成")
    def _set_last_row_shading(self, table, total_rows: int) -> None:
        """
        设置表格最后一行的底纹为蓝色

        Args:
            table: Word表格对象
            total_rows: 总行数
        """
        logger.info(f"设置表格最后一行底纹为蓝色，总行数: {total_rows}")
        if total_rows <= 0 or len(table.rows) < total_rows:
            logger.warning(f"无法设置底纹，总行数: {total_rows}, 实际行数: {len(table.rows)}")
            return

        # 获取最后一行（基于实际数据行数）
        last_row_idx = min(total_rows, len(table.rows)) - 1
        if last_row_idx >= 0:
            last_row = table.rows[last_row_idx]
            for cell in last_row.cells:
                # 设置单元格背景色为蓝色
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:fill'), '0070C0')  # 蓝色的十六进制值
                shading_elm.set(qn('w:val'), 'clear')
                shading_elm.set(qn('w:color'), 'auto')
                cell._tc.get_or_add_tcPr().append(shading_elm)
                logger.debug(f"设置单元格底纹为蓝色")