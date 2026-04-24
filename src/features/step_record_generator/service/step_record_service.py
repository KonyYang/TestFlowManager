# src/features/step_record_generator/service/step_record_service.py
"""
Step Record生成服务
根据Matrix中的数据自动生成Step Record Word文档
"""

import json
import os
import shutil
from typing import Dict, Any, List, Optional

from src.core.config_manager import config_manager
from src.core.logger import logger
from src.features.step_record_generator.service.step_record_data_formatter import (
    EXCLUDE_REQUIREMENT_VALUES,
    filter_requirement_text,
    generate_sample_quantity_text,
    natural_sort_key,
)
from src.infrastructure.office.facade import OfficeFacade


class StepRecordService:
    """
    Step Record文档生成服务
    """

    def __init__(self, office_facade: OfficeFacade | None = None):
        self.template_prefix = "FDQF-E-036"
        self.template_dir = config_manager.get_template_dir()
        self._office_facade = office_facade
        self.exclude_requirement_values = list(EXCLUDE_REQUIREMENT_VALUES)

    def _get_office_facade(self) -> OfficeFacade:
        if self._office_facade is None:
            self._office_facade = OfficeFacade()
        return self._office_facade

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

    def _generate_sample_quantity_text(self, sample_size: str, group_name: str) -> str:
        """生成样品数量文本（委托到 step_record_data_formatter）"""
        return generate_sample_quantity_text(sample_size, group_name)

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

    def _filter_requirement_text(self, requirement_text):
        """过滤Requirement文本（委托到 step_record_data_formatter）"""
        return filter_requirement_text(requirement_text, self.exclude_requirement_values)

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
                    try:
                        table.Cell(current_row, 1).Range.Text = str(step_info.get("StepNumber", ""))
                        table.Cell(current_row, 2).Range.Text = str(step_info.get("Test", ""))
                        table.Cell(current_row, 3).Range.Text = str(step_info.get("TestMethod", ""))
                        table.Cell(current_row, 4).Range.Text = str(step_info.get("Condition", ""))
                        # 对Requirement文本进行过滤
                        requirement_text = step_info.get("Requirement", "")
                        filtered_requirement = self._filter_requirement_text(requirement_text)
                        table.Cell(current_row, 9).Range.Text = str(filtered_requirement)
                        current_row += 1
                    except Exception as cell_error:
                        logger.error(f"填充表格单元格时出错 (行 {current_row}): {cell_error}")
                        current_row += 1  # 即使出错也继续下一行
                else:
                    logger.warning(f"表格行数不足，需要第 {current_row} 行但只有 {table.Rows.Count} 行")
        except Exception as e:
            logger.error(f"Error filling record table: {e}")

    def _duplicate_template_sections(self, doc: Any, needed_groups: int) -> None:
        """
        简化版本的复制模板段落和表格方法
        
        Args:
            doc: Word文档对象
            needed_groups: 需要的组别数量
        """
        try:
            # 模板默认有1个组别（包含两个表格：一个用于数据填充，一个用于手工记录）
            default_groups = 1
            # 如果有n个组别，实际上需要复制n-1次（因为模板已经有1份）
            groups_to_add = needed_groups - default_groups
            
            logger.info(f"检查是否需要复制模板段落和表格: 当前组别数={needed_groups}, 默认组别数={default_groups}, 需要添加={groups_to_add}")
            
            if groups_to_add <= 0:
                logger.info("组别数量未超过默认值，无需复制模板段落和表格")
                return
            
            logger.info(f"需要复制 {groups_to_add} 个额外的段落和表格")
            logger.info(f"复制前文档表格数量: {doc.Tables.Count}")

            # 只选择前两个表格及其相关段落进行复制，避免指数增长
            # 定位到第二个表格的结束位置
            if doc.Tables.Count >= 2:
                # 获取第二个表格的范围
                second_table_range = doc.Tables(2).Range
                
                # 获取文档开始到第二个表格结束的范围
                copy_range = doc.Range(0, second_table_range.End)
                
                # 复制这个范围的内容
                copy_range.Copy()
                
                # 粘贴groups_to_add次
                for i in range(groups_to_add):
                    logger.debug(f"开始第 {i+1} 次粘贴")
                    # 粘贴到文档末尾
                    doc.Application.Selection.PasteAndFormat(0)  # 0 表示保持源格式
                    logger.debug(f"第 {i+1} 次粘贴完成")
                        
                logger.info(f"成功粘贴 {groups_to_add} 次模板内容，当前总表格数: {doc.Tables.Count}")
            else:
                logger.error("文档中表格数量不足，无法正确复制模板段落")
            
        except Exception as e:
            logger.exception(f"Error duplicating template sections: {e}")
            # 即使出错也继续执行，避免完全失败

    def _fill_header_info(self, doc: Any, project_data_file_path: str) -> bool:
        """
        填充页眉信息
        
        Args:
            doc: Word文档对象
            project_data_file_path: 项目数据文件路径
            
        Returns:
            是否成功填充页眉
        """
        try:
            logger.info(f"开始填充页眉信息，项目数据文件路径: {project_data_file_path}")
            
            # 检查数据文件是否存在
            if not os.path.exists(project_data_file_path):
                logger.error(f"项目数据文件不存在: {project_data_file_path}")
                return False
            
            # 读取JSON数据文件
            with open(project_data_file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 获取需要的信息
            dl_number = project_data.get("DL", "DL-UNKNOWN")
            product_description = project_data.get("product_description", "").strip()
            applicable_specifications = project_data.get("applicable_specifications", "").strip()
            
            logger.info(f"从JSON文件中读取到DL编号: '{dl_number}'")
            logger.info(f"从JSON文件中读取到产品描述: '{product_description}'")
            logger.info(f"从JSON文件中读取到适用标准: '{applicable_specifications}'")
            
            # 获取页眉部分
            header_section = doc.Sections(1)  # 页眉在第一个节中
            header_range = header_section.Headers(1).Range  # wdHeaderFooterPrimary = 1

            # 检查页眉中是否有表格
            if header_range.Tables.Count < 2:
                logger.error("页眉中未找到至少两个表格")
                return False

            # 获取页眉中的第一个表格
            header_table = header_range.Tables(1)
            
            # 检查表格行列数是否符合要求
            if header_table.Rows.Count < 1 or header_table.Columns.Count < 3:
                logger.error("页眉第一个表格行列数不足")
                return False
            
            # 在第一个表格的(1,3)单元格，添加项目编号
            cell_range = header_table.Cell(1, 3).Range
            # 确保至少存在4个段落（空行+两个标题+预留空行）
            while cell_range.Paragraphs.Count < 4:
                cell_range.InsertParagraphAfter()  # 追加缺失的段落
            
            # 定位并替换第三个段落（保留前两行标题）
            cell_range.Paragraphs(4).Range.Text = dl_number
            logger.info(f"已在页眉第一个表格(1,3)单元格中填入DL编号: {dl_number}")

            # 获取页眉中的第二个表格
            if header_range.Tables.Count >= 2:
                header_table = header_range.Tables(2)
                # 检查表格是否有足够的行和列
                if header_table.Rows.Count >= 1 and header_table.Columns.Count >= 4:
                    # 填充页眉第二个表格的 (1,2) 和 (1,4) 单元格
                    header_table.Cell(1, 2).Range.Text = product_description
                    header_table.Cell(1, 4).Range.Text = applicable_specifications
                    logger.info(f"已在页眉第二个表格(1,2)单元格中填入产品描述: {product_description}")
                    logger.info(f"已在页眉第二个表格(1,4)单元格中填入适用标准: {applicable_specifications}")
                else:
                    logger.error("页眉表格的行列数量不足")
                    return False
            else:
                logger.error("页眉中未找到第二个表格")
                return False
                
            logger.info("页眉信息填充完成")
            return True
            
        except Exception as e:
            logger.error(f"填充页眉信息时发生错误: {e}")
            return False

    def generate_step_record_with_structure(self, matrix_structure: Any, output_path: str) -> bool:
        """
        根据已解析的Matrix数据结构生成Step Record文档
        
        Args:
            matrix_structure: 已解析的Matrix数据结构
            output_path: 输出文件路径
            
        Returns:
            是否成功生成
        """
        word_session = None
        new_doc = None
        try:
            # 查找模板文件
            template_path = self._find_template_file()
            if not template_path:
                logger.error("Template file not found")
                return False
            
            logger.info(f"找到模板文件: {template_path}")
            
            # 检查模板文件是否存在
            if not os.path.exists(template_path):
                logger.error(f"模板文件不存在: {template_path}")
                return False

            # 标准化输出路径
            output_path = os.path.normpath(output_path)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"已创建输出目录: {output_dir}")

            # 直接复制模板文件到目标位置
            shutil.copy2(template_path, output_path)
            logger.info(f"成功复制模板文件到: {output_path}")

            # 初始化Word应用
            word_session = self._get_office_facade().create_session("word")
            word_handle = word_session.acquire()
            word_app = word_handle.application
            if not word_app:
                logger.error("Failed to initialize Word application")
                return False

            word_app.Visible = False
            word_app.DisplayAlerts = False

            # 打开已复制的文档
            try:
                new_doc = word_app.Documents.Open(output_path, ReadOnly=False)
            except Exception as open_error:
                logger.error(f"Failed to open copied document: {open_error}")
                return False

            # 从MatrixDataStructure获取解析好的数据
            group_steps = matrix_structure.group_steps
            group_sample_sizes = matrix_structure.group_sample_sizes

            # 获取组别数量
            group_count = len(group_steps)
            if group_count == 0:
                logger.warning("没有找到任何组别数据")
                return False

            # 如果组别数量超过1个，需要复制模板中的段落和表格
            if group_count > 1:
                logger.info(f"检测到 {group_count} 个组别，超过默认的1个，开始复制模板段落和表格")
                self._duplicate_template_sections(new_doc, group_count)
                logger.info(f"复制完成后文档表格数量: {new_doc.Tables.Count}")
            else:
                logger.info(f"组别数量 {group_count} 未超过默认值1，无需复制模板")

            logger.info(f"Matrix数据解析完成，共找到 {group_count} 个组别")

            # 填充页眉信息
            # 获取项目数据文件路径
            project_data_file_path = getattr(matrix_structure, 'project_data_file_path', None)
            if project_data_file_path and os.path.exists(project_data_file_path):
                logger.info(f"从MatrixDataStructure获取到项目数据文件路径: {project_data_file_path}")
                if not self._fill_header_info(new_doc, project_data_file_path):
                    logger.warning("页眉信息填充失败，但继续生成文档")
            else:
                logger.warning("未提供有效的项目数据文件路径，跳过页眉信息填充")

            # 填充文档
            # 按照组别顺序处理
            logger.info("开始将数据填入Word模板")
            logger.info(f"填充前文档表格数量: {new_doc.Tables.Count}")

            group_index = 1
            for group_name in sorted(group_steps.keys(), key=natural_sort_key):
                logger.info(f"处理组别 {group_name}，包含 {len(group_steps[group_name])} 个测试项")

                # 更新组别标题
                table_no = group_index * 2 - 1  # 奇数编号的表格 (1, 3, 5, ...)
                logger.debug(f"组别 {group_name} 对应的表格编号: {table_no}，当前文档总表格数: {new_doc.Tables.Count}")

                if table_no <= new_doc.Tables.Count:
                    success = self._update_group_title(new_doc, table_no, group_name, group_sample_sizes.get(group_name, ""))
                    if success:
                        logger.debug(f"成功更新组别 {group_name} 的标题")
                    else:
                        logger.warning(f"更新组别 {group_name} 的标题失败")

                    # 确保表格有足够的行数
                    steps_count = len(group_steps[group_name])
                    logger.debug(f"组别 {group_name} 需要 {steps_count} 行数据")
                    self._ensure_table_has_enough_rows(new_doc.Tables(table_no), steps_count + 1)

                    # 填充表格内容
                    self._fill_record_table_from_dict(new_doc.Tables(table_no), {i: step for i, step in enumerate(group_steps[group_name])})

                    logger.info(f"组别 {group_name} 数据已填入表格 {table_no}")
                else:
                    logger.warning(f"表格编号 {table_no} 超出文档表格数量 {new_doc.Tables.Count}")

                group_index += 1

            # 保存文档
            logger.info(f"准备保存文档到: {output_path}")

            new_doc.SaveAs2(output_path)
            logger.info("文档已保存")

            logger.info(f"Step Record document generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating Step Record document: {e}")
            return False
        finally:
            # 清理资源
            if new_doc:
                try:
                    new_doc.Close(SaveChanges=False)
                    logger.info("文档已关闭")
                except Exception as close_error:
                    logger.error(f"Failed to close Step Record document: {close_error}")
            if word_session:
                word_session.release()
