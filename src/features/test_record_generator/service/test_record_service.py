# src/features/test_record_generator/service/test_record_service.py
"""
Test Record生成服务
根据Matrix中的数据自动生成Test Record Word文档
"""

import os
import re
from typing import Dict, Any, List, Optional
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.utils.word_utils import get_shared_word_app, release_word_app, open_word_file
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure


class TestRecordService:
    """
    Test Record文档生成服务
    """

    def __init__(self):
        self.template_prefix = "FDQF-E-036"
        self.template_dir = config_manager.get("paths.template_dir")
        self.word_app = None

    def _find_template_file(self) -> Optional[str]:
        """
        在模板目录中查找以FDQF-E-036开头的docx文件
        
        Returns:
            模板文件路径，如果未找到则返回None
        """
        try:
            if not os.path.exists(self.template_dir):
                logger.error(f"Template directory does not exist: {self.template_dir}")
                return None

            for file_name in os.listdir(self.template_dir):
                if (file_name.startswith(self.template_prefix) and 
                    file_name.endswith('.docx')):
                    return os.path.join(self.template_dir, file_name)
            
            logger.warning(f"No template file found with prefix '{self.template_prefix}' in {self.template_dir}")
            return None
        except Exception as e:
            logger.error(f"Error searching for template file: {e}")
            return None

    def _clean_sample_quantity(self, sample_quantity: str) -> str:
        """
        清理样品数量中的非数字和非+字符
        
        Args:
            sample_quantity: 原始样品数量字符串
            
        Returns:
            清理后的样品数量字符串
        """
        # 只保留数字和 + 符号
        cleaned = re.sub(r'[^0-9+]', '', sample_quantity)
        return cleaned

    def _generate_sample_quantity_text(self, sample_size: str, group_name: str) -> str:
        """
        生成样品数量文本
        
        Args:
            sample_size: 样品数量
            group_name: 组别名称
            
        Returns:
            格式化后的样品数量文本
        """
        try:
            cleaned_size = self._clean_sample_quantity(sample_size)
            
            # 处理复合样品 (包含+符号)
            if '+' in cleaned_size:
                parts = cleaned_size.split('+')
                start_number = 1
                sample_text = ""
                
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part.isdigit():
                        part_count = int(part)
                        end_number = start_number + part_count - 1
                        
                        if sample_text:
                            sample_text += " + "
                            
                        sample_text += f"{part_count} sets for (Group{group_name}-{start_number}#"
                        if start_number != end_number:
                            sample_text += f"~{end_number}#"
                        sample_text += ")"
                        
                        start_number = end_number + 1
                
                return sample_text
            else:
                # 处理单一数字
                if cleaned_size.isdigit():
                    total_quantity = int(cleaned_size)
                    if total_quantity == 1:
                        return "1 set (1#)"
                    else:
                        return f"{total_quantity} sets (Group{group_name}-1#~{total_quantity}#)"
                
                return ""
        except Exception as e:
            logger.error(f"Error generating sample quantity text: {e}")
            return ""

    def _update_group_title(self, doc: Any, table_no: int, group_name: str, sample_size: str) -> bool:
        """
        更新组别标题
        
        Args:
            doc: Word文档对象
            table_no: 表格编号
            group_name: 组别名称
            sample_size: 样品数量
            
        Returns:
            是否成功更新
        """
        try:
            # 定位到当前表格前的段落
            if table_no > doc.Tables.Count:
                logger.error(f"Table number {table_no} exceeds total tables {doc.Tables.Count}")
                return False
                
            table_range = doc.Tables(table_no).Range
            search_range = doc.Range(0, table_range.Start)
            
            # 查找模板文本
            search_text = "Group Number 组别编号: # ;   Sample Quantity & Number 样品数量及编号: #"
            found = search_range.Find.Execute(search_text)
            
            if found:
                # 替换组别编号
                fixed_text = search_range.Text.replace("#", group_name, 1)
                
                # 生成并替换样品数量文本
                sample_text = self._generate_sample_quantity_text(sample_size, group_name)
                fixed_text = fixed_text.replace("#", sample_text, 1)
                
                # 更新段落内容
                search_range.Text = fixed_text
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error updating group title: {e}")
            return False

    def _ensure_table_has_enough_rows(self, table: Any, required_rows: int) -> None:
        """
        确保表格有足够的行数
        
        Args:
            table: Word表格对象
            required_rows: 所需行数
        """
        try:
            while table.Rows.Count < required_rows:
                table.Rows.Add()
        except Exception as e:
            logger.error(f"Error ensuring table has enough rows: {e}")

    def _fill_record_table_from_dict(self, table: Any, step_dict: Dict) -> None:
        """
        从字典填充表格内容
        
        Args:
            table: Word表格对象
            step_dict: 步骤字典
        """
        try:
            current_row = 2  # 从第二行开始填充
            for step_key in sorted(step_dict.keys()):
                step_info = step_dict[step_key]
                
                # 填充基础信息
                if current_row <= table.Rows.Count:
                    table.Cell(current_row, 1).Range.Text = str(step_info.get("StepNumber", ""))
                    table.Cell(current_row, 2).Range.Text = str(step_info.get("Test", ""))
                    table.Cell(current_row, 3).Range.Text = str(step_info.get("TestMethod", ""))
                    table.Cell(current_row, 4).Range.Text = str(step_info.get("Condition", ""))
                    table.Cell(current_row, 9).Range.Text = str(step_info.get("Requirement", ""))
                    current_row += 1
        except Exception as e:
            logger.error(f"Error filling record table: {e}")

    def generate_test_record(self, matrix_data: List[List[str]], output_path: str) -> bool:
        """
        根据Matrix数据生成Test Record文档
        
        Args:
            matrix_data: Matrix数据
            output_path: 输出文件路径
            
        Returns:
            是否成功生成
        """
        try:
            logger.info(f"开始生成Test Record文档，Matrix数据行数: {len(matrix_data)}")
            
            # 使用MatrixDataStructure解析数据
            matrix_structure = MatrixDataStructure()
            matrix_structure.update_from_matrix(matrix_data)
            
            # 查找模板文件
            template_path = self._find_template_file()
            if not template_path:
                logger.error("Template file not found")
                return False
            
            logger.info(f"找到模板文件: {template_path}")

            # 初始化Word应用
            self.word_app = get_shared_word_app()
            if not self.word_app:
                logger.error("Failed to initialize Word application")
                return False

            self.word_app.Visible = False
            self.word_app.DisplayAlerts = False

            # 打开模板文档
            template_doc = open_word_file(template_path, read_only=True)
            if not template_doc:
                logger.error("Failed to open template document")
                return False

            # 创建新文档作为副本
            new_doc = self.word_app.Documents.Add()
            
            # 复制模板内容到新文档
            template_doc.Range().Copy()
            new_doc.Range().Paste()
            
            # 关闭模板文档
            template_doc.Close(SaveChanges=False)

            # 从MatrixDataStructure获取解析好的数据
            group_steps = matrix_structure.group_steps
            group_sample_sizes = matrix_structure.group_sample_sizes

            logger.info(f"Matrix数据解析完成，共找到 {len(group_steps)} 个组别")

            # 2. 填充文档
            # 按照组别顺序处理
            logger.info("开始将数据填入Word模板")
            
            for group_name in sorted(group_steps.keys()):
                logger.info(f"处理组别 {group_name}，包含 {len(group_steps[group_name])} 个测试项")
                
                # 更新组别标题
                table_no = int(group_name) * 2 - 1  # 奇数编号的表格
                if table_no <= new_doc.Tables.Count:
                    self._update_group_title(new_doc, table_no, group_name, group_sample_sizes.get(group_name, ""))
                    
                    # 确保表格有足够的行数
                    steps_count = len(group_steps[group_name])
                    self._ensure_table_has_enough_rows(new_doc.Tables(table_no), steps_count + 1)
                    
                    # 填充表格内容
                    self._fill_record_table_from_dict(new_doc.Tables(table_no), {i: step for i, step in enumerate(group_steps[group_name])})
                    
                    logger.info(f"组别 {group_name} 数据已填入表格 {table_no}")
                else:
                    logger.warning(f"表格编号 {table_no} 超出文档表格数量 {new_doc.Tables.Count}")

            # 保存文档
            new_doc.SaveAs2(output_path)
            new_doc.Close(SaveChanges=False)
            
            logger.info(f"Test Record document generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating Test Record document: {e}")
            return False
        finally:
            # 清理资源
            if self.word_app:
                release_word_app()
