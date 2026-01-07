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
            
            # 打开Word文档
            doc = Document(document_path)
            logger.info(f"成功打开文档，包含 {len(doc.paragraphs)} 个段落和 {len(doc.tables)} 个表格")
            
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
            
            # 查找并填充Test Description表格
            description_table = self._find_table_by_paragraph(doc, "TEST DESCRIPTION")
            if description_table:
                logger.info("找到TEST DESCRIPTION表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Description表格...")
                self._fill_description_table(description_table, filtered_steps)
                # 设置最后一行的底纹为蓝色
                self._set_last_row_shading(description_table, len(filtered_steps))
            else:
                logger.warning("未找到TEST DESCRIPTION表格")
                if status_callback:
                    status_callback("警告: 未找到TEST DESCRIPTION表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 60)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找TEST METHODS/REQUIREMENTS段落...")
            
            # 查找并填充Test Method表格
            method_table = self._find_table_by_paragraph(doc, "TEST METHODS/REQUIREMENTS")
            if method_table:
                logger.info("找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Method表格...")
                self._fill_method_table(method_table, filtered_steps)
            else:
                logger.warning("未找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到TEST METHODS/REQUIREMENTS表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 90)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在保存文档...")
            
            # 保存文档
            doc.save(document_path)
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

    def _fill_description_table(self, table, steps: list) -> None:
        """
        填充Test Description表格
        
        根据要求：表格只有三行两列，需要依据matrix数据结构的行数和列数进行增减。
        把matrix的第一列（Test Item）和步骤列（StepNumber），行截取到"Sample size"填充进来。
        
        Args:
            table: Word表格对象
            steps: 步骤数据列表
        """
        logger.info(f"开始填充Test Description表格，共{len(steps)}个步骤")
        
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
        
        # 确保每行有2列
        for row in table.rows:
            current_cols = len(row.cells)
            if current_cols < 2:
                # 添加列直到有2列
                for _ in range(2 - current_cols):
                    row.cells[-1]._tc.addnext(row.cells[-1]._tc.clone())
                logger.info(f"添加了 {2 - current_cols} 列")
            elif current_cols > 2:
                # 删除多余列（保留前2列）
                for _ in range(current_cols - 2):
                    if len(row.cells) > 2:
                        row._tr.remove(row.cells[-1]._tc)
                logger.info(f"删除了 {current_cols - 2} 列")
        
        logger.info(f"最终表格行数: {len(table.rows)}, 列数: {len(table.rows[0].cells) if table.rows else 0}")
        
        # 填充数据 - 使用Matrix的第一列（Test Item）和步骤列（StepNumber）
        for i, step in enumerate(steps):
            if i < len(table.rows):
                row = table.rows[i]
                
                # 确保有2列
                if len(row.cells) >= 2:
                    # 第一列：Test Item（来自Matrix的第一列）
                    test_item = step.get("Test", "")
                    if test_item:  # 只有当内容不为空时才设置
                        row.cells[0].text = str(test_item)
                        logger.debug(f"第{i+1}行第1列填充: {test_item}")
                    
                    # 第二列：Step Number
                    step_number = step.get("StepNumber", "")
                    if step_number:  # 只有当内容不为空时才设置
                        row.cells[1].text = str(step_number)
                        logger.debug(f"第{i+1}行第2列填充: {step_number}")
                    
                    # 设置单元格格式
                    for cell in row.cells:
                        # 设置段落居中对齐
                        for paragraph in cell.paragraphs:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        # 设置单元格垂直居中对齐
                        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    def _fill_method_table(self, table, steps: list) -> None:
        """
        填充Test Method表格
        
        根据要求：表格只有两行三列，需要依据matrix数据结构的行数和列数进行增减。
        把matrix的第1,3,4,5列（Test, TestMethod, Condition, Requirement），
        行截取到"Sample size"前面一行填充进来。
        
        Args:
            table: Word表格对象
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
                        logger.debug(f"第{i+1}行第2列填充: {test_method}")
                    
                    # 第三列：Condition
                    condition = step.get("Condition", "")
                    if condition:  # 只有当内容不为空时才设置
                        row.cells[2].text = str(condition)
                        logger.debug(f"第{i+1}行第3列填充: {condition}")
                    
                    # 设置单元格格式
                    for cell in row.cells:
                        # 设置段落居中对齐
                        for paragraph in cell.paragraphs:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        # 设置单元格垂直居中对齐
                        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

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