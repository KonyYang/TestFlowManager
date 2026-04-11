"""
费用表导出服务
提供生成费用表的业务逻辑服务
"""

from typing import Dict, Any, List, Optional
from src.core.config_manager import config_manager
from src.core.logger import logger
from src.core.output_paths import OutputPathResolver
from src.core.project_context import ProjectContext
from src.core.project_document_context import ProjectDocumentContext
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
import os
import pythoncom
import win32com.client as win32
import time
import shutil


class FeeSheetExportService:
    """
    费用表导出服务类
    提供生成费用表的业务逻辑服务
    """

    def __init__(self, project_context: Optional[ProjectContext] = None):
        """初始化费用表导出服务"""
        self.template_dir = config_manager.get_template_dir()
        self.output_dir = OutputPathResolver.get_default_output_dir()
        self.excel_app = None
        self.project_context = project_context

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        self.project_context = project_context

    def get_project_context(self) -> Optional[ProjectContext]:
        return self.project_context

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符
        :param filename: 原始文件名
        :return: 清理后的文件名
        """
        import re
        # 移除Windows文件系统中的非法字符
        illegal_chars = r'[<>:"/\|?*]'
        sanitized = re.sub(illegal_chars, '_', filename)
        # 移除首尾空格和点号
        sanitized = sanitized.strip('. ')
        # 限制长度
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized

    def _get_group_tests_from_matrix(self, matrix_data_structure: MatrixDataStructure) -> Dict[str, List[Dict[str, Any]]]:
        """
        从Matrix数据结构获取每个组别的测试项目信息
        :param matrix_data_structure: MatrixDataStructure实例
        :return: 包含每个组别测试项目信息的字典
        """
        if matrix_data_structure is None:
            # 返回空数据
            return {}
        
        # 获取所有组别
        all_groups = matrix_data_structure.get_all_groups()
        group_tests_info = {}

        for group in all_groups:
            # 获取该组的所有步骤
            group_step_data = matrix_data_structure.get_group_steps(group)

            tests_list = []
            # MatrixDataStructure.get_group_steps 返回的是包含步骤信息的列表
            for step in group_step_data:
                # 提取测试相关信息，映射到我们期望的字段
                test_info = {
                    "step_num": step.get("StepNumber", ""),
                    "test": step.get("Test", ""),
                    "test_method": step.get("TestMethod", ""),
                    "condition": step.get("Condition", ""),
                    "requirement": step.get("Requirement", ""),
                    "remark": step.get("StepDescription", "")
                }
                tests_list.append(test_info)

            group_tests_info[group] = tests_list

        return group_tests_info

    def _find_fee_sheet_folder_and_file(self, project_path: str, dl_number: str) -> Optional[tuple]:
        """
        在项目目录下查找包含DL编号的子文件夹，并在其中查找费用表文件
        :param project_path: 项目路径
        :param dl_number: DL编号
        :return: (子文件夹路径, 费用表文件路径)的元组，如果未找到子文件夹则返回None
        """
        try:
            logger.debug(f"在项目路径 {project_path} 中查找包含 '{dl_number}' 的子文件夹")
            
            # 查找包含DL编号的子文件夹
            if not os.path.exists(project_path):
                logger.warning(f"项目路径不存在: {project_path}")
                return None
                
            # 遍历项目目录下的所有子文件夹
            for item in os.listdir(project_path):
                item_path = os.path.join(project_path, item)
                if os.path.isdir(item_path) and dl_number in item:
                    logger.debug(f"找到包含DL编号的子文件夹: {item}")
                    folder_path = item_path
                    
                    # 在该子文件夹中查找包含"Testing Fee Evaluation"且以dl_number开头的Excel文件
                    fee_sheet_path = None
                    for file in os.listdir(item_path):
                        if (file.lower().endswith(('.xls', '.xlsx')) and 
                            "testing fee evaluation" in file.lower() and
                            file.startswith(dl_number)):
                            fee_sheet_path = os.path.join(item_path, file)
                            logger.info(f"找到费用表文件: {fee_sheet_path}")
                            break
                    
                    if fee_sheet_path:
                        logger.debug(f"在子文件夹 {item} 中找到费用表文件")
                        return (folder_path, fee_sheet_path)
                    else:
                        logger.debug(f"在子文件夹 {item} 中未找到费用表文件")
                        return (folder_path, None)
            
            logger.info(f"未找到包含 '{dl_number}' 的子文件夹")
            return None
            
        except Exception as e:
            logger.error(f"查找费用表文件夹和文件时出错: {e}", exc_info=True)
            return None
    
    def _find_existing_fee_sheet(self, project_path: str, dl_number: str) -> Optional[str]:
        """
        在项目目录下查找已存在的费用表文件（保持向后兼容）
        :param project_path: 项目路径
        :param dl_number: DL编号
        :return: 找到的费用表文件路径，未找到则返回None
        """
        try:
            logger.debug(f"在项目路径 {project_path} 中查找包含 '{dl_number}' 的子文件夹")
            
            # 查找包含DL编号的子文件夹
            if not os.path.exists(project_path):
                logger.warning(f"项目路径不存在: {project_path}")
                return None
                
            # 遍历项目目录下的所有子文件夹
            for item in os.listdir(project_path):
                item_path = os.path.join(project_path, item)
                if os.path.isdir(item_path) and dl_number in item:
                    logger.debug(f"找到包含DL编号的子文件夹: {item}")
                    
                    # 在该子文件夹中查找包含"Testing Fee Evaluation"且以dl_number开头的Excel文件
                    for file in os.listdir(item_path):
                        if (file.lower().endswith(('.xls', '.xlsx')) and 
                            "testing fee evaluation" in file.lower() and
                            file.startswith(dl_number)):
                            fee_sheet_path = os.path.join(item_path, file)
                            logger.info(f"找到费用表文件: {fee_sheet_path}")
                            return fee_sheet_path
                    
                    logger.debug(f"在子文件夹 {item} 中未找到符合条件的费用表文件")
            
            logger.info(f"未找到包含 '{dl_number}' 且含有费用表的子文件夹")
            return None
            
        except Exception as e:
            logger.error(f"查找现有费用表文件时出错: {e}", exc_info=True)
            return None
    
    def _find_fee_sheet_templates(self) -> List[str]:
        """
        查找费用表模板文件
        :return: 模板文件路径列表
        """
        fee_sheet_templates = []
        
        if not os.path.exists(self.template_dir):
            logger.warning(f"模板目录不存在: {self.template_dir}")
            return fee_sheet_templates
        
        for file in os.listdir(self.template_dir):
            if "Testing Fee" in file and (file.lower().endswith('.xls') or file.lower().endswith('.xlsx')):
                fee_sheet_templates.append(os.path.join(self.template_dir, file))
        
        logger.info(f"找到 {len(fee_sheet_templates)} 个费用表模板文件")
        return fee_sheet_templates

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符
        :param filename: 原始文件名
        :return: 清理后的文件名
        """
        import re
        # 移除Windows文件系统中的非法字符
        illegal_chars = r'[<>:"/\|?*]'
        sanitized = re.sub(illegal_chars, '_', filename)
        # 移除首尾空格和点号
        sanitized = sanitized.strip('. ')
        # 限制长度
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized

    def _fill_group_tests_data(self, worksheet, group_tests_info: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        填充测试组别数据到Excel表格中
        :param worksheet: Excel工作表对象
        :param group_tests_info: 包含每个组别测试项目信息的字典
        :return: 是否成功填充
        """
        try:
            anchor = self._find_sample_preparation_anchor(worksheet)
            if not anchor:
                logger.warning("未找到'Sample preparation (if needed)'行，无法按要求填充组别数据")
                return False

            base_row, template_row, template_col = anchor
            template_cell_value = worksheet.Cells(template_row, template_col).Value
            if template_cell_value not in (None, ""):
                logger.warning(f"第{template_row}行第{template_col}列不是空白模板单元格，无法按要求复制行")
                return False

            logger.debug(f"找到基础行 (第{base_row}行) 和模板行 (第{template_row}行)")
            
            # 记录插入前的行高，以防止插入操作影响原有行的行高
            # 获取当前工作表的总行数
            used_range = worksheet.UsedRange
            total_rows = used_range.Rows.Count
            
            # 记录从第13行到末尾的原始行高
            original_heights = {}
            for row in range(13, min(total_rows + 1, 50)):  # 记录最多50行的原始高度
                try:
                    original_heights[row] = worksheet.Rows(row).Height
                except:
                    # 如果无法获取某行的行高，跳过
                    continue
            
            # 从第6行开始插入新的组别数据
            current_row = 6
            
            # 遍历每个组别
            for group_idx, (group_name, tests_list) in enumerate(group_tests_info.items()):
                logger.info(f"正在填充组别: {group_name}")
                
                # 如果测试列表为空，则跳过
                if not tests_list:
                    continue
                
                # 不进行去重，显示所有步骤（包括重复的步骤）
                all_tests = tests_list
                num_tests = len(all_tests)
                
                # 获取第5行和第6行的列数
                max_cols = used_range.Columns.Count
                
                # 对于第一个组别(Group 1)
                if group_idx == 0:
                    # Group 1使用第6行作为第一个测试项目，但A列合并需要包含第5行
                    # 首先在第6行填入第一个测试项目
                    worksheet.Cells(current_row, 3).Value = all_tests[0].get('test', '') if all_tests else ''
                    
                    # 如果该组有多个测试项目，需要插入新的行来存放额外的测试项目
                    # 使用Insert方法插入新行而不是覆盖现有行
                    if num_tests > 1:
                        for i in range(num_tests - 1):
                            # 插入新行，基于第6行（模板行）
                            insert_position = current_row + 1 + i
                            row_to_insert = worksheet.Rows(insert_position)
                            
                            # 复制模板行到剪贴板
                            source_range_6th = worksheet.Range(
                                worksheet.Cells(template_row, 1), 
                                worksheet.Cells(template_row, max_cols)
                            )
                            source_range_6th.Copy()
                            
                            # 插入新行（这会将下面的行向下移动）
                            row_to_insert.Insert()
                            
                            # 填入对应的测试项目名称
                            if i + 1 < len(all_tests):
                                worksheet.Cells(insert_position, 3).Value = all_tests[i + 1].get('test', '')
                                logger.debug(f"  在第{insert_position}行C列插入新行并填入测试项目: {all_tests[i + 1].get('test', '')}")
                    
                    # Group 1的A列合并需要包含第5行到当前最后一行
                    # 所以合并范围是第5行到第(current_row + num_tests - 1)行
                    group_range = worksheet.Range(
                        worksheet.Cells(base_row, 1),  # 从第5行开始
                        worksheet.Cells(current_row + num_tests - 1, 1)  # 到当前组的最后一行
                    )
                    group_range.Merge()
                    # 在合并的单元格中填入组别名称
                    worksheet.Cells(base_row, 1).Value = group_name
                    logger.debug(f"  合并A列第{base_row}行到第{current_row + num_tests - 1}行，并填入组别名称: {group_name}")
                    
                    # 更新当前行号，为下一组留出空间
                    current_row = current_row + num_tests
                    
                else:  # 对于后续组别(Group 2及之后)
                    # 先插入n+1行：起始行(复制第5行) + 测试项目行(复制第6行)*测试项目数
                    # 首先插入一个新的'Sample preparation (if needed)'行，基于第5行
                    new_group_start = current_row
                    
                    # 复制第5行到剪贴板
                    source_range_5th = worksheet.Range(
                        worksheet.Cells(base_row, 1), 
                        worksheet.Cells(base_row, max_cols)
                    )
                    source_range_5th.Copy()
                    
                    # 插入新行（这会将下面的行向下移动）
                    row_to_insert = worksheet.Rows(new_group_start)
                    row_to_insert.Insert()
                    
                    # 因为第一个测试项目是起始行，后面的每个测试项目都需要插入一行
                    for i in range(num_tests):
                        # 插入新行，基于第6行（模板行）
                        insert_position = new_group_start + 1 + i
                        row_to_insert = worksheet.Rows(insert_position)
                        
                        # 复制模板行到剪贴板
                        source_range_6th = worksheet.Range(
                            worksheet.Cells(template_row, 1), 
                            worksheet.Cells(template_row, max_cols)
                        )
                        source_range_6th.Copy()
                        
                        # 插入新行（这会将下面的行向下移动）
                        row_to_insert.Insert()
                        
                        # 填入对应的测试项目名称
                        if i < len(all_tests):
                            worksheet.Cells(insert_position, 3).Value = all_tests[i].get('test', '')
                            logger.debug(f"  在第{insert_position}行插入新行并填入测试项目: {all_tests[i].get('test', '')}")
                    
                    # 计算合并范围：起始行(new_group_start) 到 结束行(new_group_start + num_tests)
                    # 如果有n个测试项目，总共需要n+1行（1个起始行 + n个测试项目行）
                    actual_end_row = new_group_start + num_tests  # 总共插入了1个起始行 + num_tests个测试项目行
                    
                    group_range = worksheet.Range(
                        worksheet.Cells(new_group_start, 1),
                        worksheet.Cells(actual_end_row, 1)
                    )
                    group_range.Merge()
                    # 在合并的单元格中填入组别名称
                    worksheet.Cells(new_group_start, 1).Value = group_name
                    logger.debug(f"  合并A列第{new_group_start}行到第{actual_end_row}行，并填入组别名称: {group_name}")
                    
                    # 更新当前行号，为下一组留出空间
                    current_row = actual_end_row + 1  # 跳过已使用的行
                    
                logger.debug(f"  组别{group_name}填充完成，测试数: {num_tests}（包含所有步骤）")
            
            # 尝试恢复原始行高，以防止插入操作影响原有行的行高
            for row, height in original_heights.items():
                try:
                    worksheet.Rows(row).Height = height
                except:
                    # 如果无法设置行高，跳过
                    continue
            
            # 设置插入行的自适应高度
            # 从第6行开始到当前行-1（即最后一个插入的行）
            if current_row > 6:
                try:
                    # 自动调整从第6行到最后一行的行高
                    auto_fit_range = worksheet.Range(
                        worksheet.Cells(6, 1),
                        worksheet.Cells(current_row - 1, max_cols)
                    )
                    # 自动调整行高以适应内容
                    auto_fit_range.EntireRow.AutoFit()
                    logger.info(f"已设置第6行到第{current_row - 1}行的自适应行高")
                except Exception as e:
                    logger.warning(f"设置自适应行高时出错: {e}")
            
            logger.info("测试组别数据填充完成")
            return True
            
        except Exception as e:
            logger.error(f"填充测试组别数据时出错: {e}", exc_info=True)
            return False

    def _find_sample_preparation_anchor(self, worksheet) -> Optional[tuple]:
        """在模板中搜索“Sample preparation”锚点，避免固定依赖 C5。"""
        try:
            used_range = worksheet.UsedRange
            max_rows = min(max(used_range.Rows.Count, 12), 40)
            max_cols = min(max(used_range.Columns.Count, 8), 12)

            for row in range(1, max_rows + 1):
                for col in range(1, max_cols + 1):
                    cell = worksheet.Cells(row, col)
                    candidates = self._get_fee_sheet_cell_candidates(cell)

                    for candidate in candidates:
                        normalized = self._normalize_fee_sheet_anchor_text(candidate)
                        if self._is_sample_preparation_anchor_text(normalized):
                            logger.debug(f"找到Sample preparation锚点: row={row}, col={col}, value={candidate}")
                            return row, row + 1, col

            self._log_fee_sheet_anchor_debug_cells(worksheet)
        except Exception as exc:
            logger.error(f"搜索Sample preparation锚点时出错: {exc}", exc_info=True)

        return None

    def _get_fee_sheet_cell_candidates(self, cell) -> List[Any]:
        candidates: List[Any] = []
        try:
            candidates.append(cell.Value)
        except Exception:
            pass
        try:
            candidates.append(cell.Text)
        except Exception:
            pass
        return candidates

    def _normalize_fee_sheet_anchor_text(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        text = str(value).replace("\r", " ").replace("\n", " ")
        return " ".join(text.lower().split())

    def _is_sample_preparation_anchor_text(self, normalized_text: str) -> bool:
        if not normalized_text:
            return False

        compact_text = normalized_text.replace(" ", "")
        if "samplepreparation(ifneeded)" in compact_text:
            return True
        if "sample preparation" in normalized_text:
            return True
        if "preparation (if needed)" in normalized_text and "sample" in normalized_text:
            return True
        return "sample" in normalized_text and "preparation" in normalized_text

    def _log_fee_sheet_anchor_debug_cells(self, worksheet) -> None:
        """在锚点定位失败时打印关键区域内容，便于适配模板。"""
        try:
            debug_rows = range(4, 9)
            debug_cols = range(1, 7)
            cell_snapshots = []
            for row in debug_rows:
                row_values = []
                for col in debug_cols:
                    cell = worksheet.Cells(row, col)
                    value = None
                    text = None
                    try:
                        value = cell.Value
                    except Exception:
                        pass
                    try:
                        text = cell.Text
                    except Exception:
                        pass
                    if value not in (None, "") or text not in (None, ""):
                        normalized_value = self._normalize_fee_sheet_anchor_text(value)
                        normalized_text = self._normalize_fee_sheet_anchor_text(text)
                        row_values.append(
                            f"R{row}C{col}=Value[{value}] Text[{text}] "
                            f"NormValue[{normalized_value}] NormText[{normalized_text}]"
                        )
                if row_values:
                    cell_snapshots.append(" | ".join(row_values))

            if cell_snapshots:
                logger.debug("费用表锚点调试区域内容:\n" + "\n".join(cell_snapshots))
        except Exception as exc:
            logger.error(f"输出费用表锚点调试信息时出错: {exc}", exc_info=True)

    def _rebuild_existing_fee_sheet_from_template(self, output_path: str) -> bool:
        """当现有费用表缺失模板主体结构时，用标准模板重建该文件。"""
        try:
            templates = self._find_fee_sheet_templates()
            if not templates:
                logger.error("未找到费用表模板文件，无法重建现有费用表")
                return False

            template_path = templates[0]
            backup_path = f"{output_path}.bak"
            if os.path.exists(output_path):
                try:
                    shutil.copy2(output_path, backup_path)
                    logger.info(f"已备份原费用表文件到: {backup_path}")
                except Exception as exc:
                    logger.warning(f"备份原费用表文件失败，将继续尝试直接重建: {exc}")

            shutil.copy2(template_path, output_path)
            logger.info(f"现有费用表缺失模板主体结构，已使用标准模板重建: {output_path}")
            return True
        except Exception as exc:
            logger.error(f"重建费用表文件时出错: {exc}", exc_info=True)
            return False

    def export_fee_sheet(self, matrix_data_structure: MatrixDataStructure,
                         dl_number: str = "DL-UNKNOWN", 
                         requested_by: str = "", 
                         location: str = "",
                         product_description: str = "",
                         tests_to_be_performed: str = "") -> tuple:
        """
        导出费用表
        :param matrix_data_structure: Matrix数据结构
        :param dl_number: DL编号
        :param requested_by: 申请人
        :param location: 地点
        :param product_description: 产品描述
        :param tests_to_be_performed: 测试项目
        :return: 是否成功导出
        """
        try:
            logger.info("开始导出费用表")
            document_context = ProjectDocumentContext.from_project_context(self.get_project_context())
            project_context = document_context.project_context
            current_project = project_context.project_path if project_context else None

            if dl_number == "DL-UNKNOWN" and document_context.dl_number:
                dl_number = document_context.dl_number
            if not requested_by:
                requested_by = document_context.get_field("requested_by", "")
            if not location:
                location = document_context.get_field("location", "")
            if not product_description:
                product_description = document_context.get_field("product_description", "")
            if not tests_to_be_performed:
                tests_to_be_performed = document_context.get_field("tests_to_be_performed", "")
            
            # 确定输出目录和文件名
            if current_project and os.path.exists(current_project):
                logger.info(f"检测到已打开项目: {current_project}")
                logger.info(f"使用项目名称作为DL编号: {dl_number}")
                
                # 在项目目录下查找子文件夹和现有费用表文件
                found_folder_info = self._find_fee_sheet_folder_and_file(current_project, dl_number)
                
                if found_folder_info:
                    folder_path, fee_sheet_path = found_folder_info
                    if fee_sheet_path:
                        # 找到已存在的费用表文件，直接操作该文件
                        logger.info(f"找到已存在的费用表文件: {fee_sheet_path}")
                        output_path = fee_sheet_path
                        output_dir = folder_path
                        # 跳过模板复制步骤，直接使用现有文件
                        use_existing_file = True
                        
                        # 从子文件夹名称中提取product_description
                        folder_name = os.path.basename(folder_path)
                        if folder_name.startswith(dl_number):
                            product_description = folder_name[len(dl_number):].strip()
                            logger.debug(f"从子文件夹名称提取的product_description: {product_description}")
                    else:
                        # 找到子文件夹但未找到费用表文件，需要生成新文件
                        logger.info(f"在子文件夹 {folder_path} 中未找到费用表文件，将生成新文件")
                        output_dir = folder_path
                        
                        # 构造费用表文件名
                        folder_name = os.path.basename(folder_path)
                        fee_sheet_filename = f"{folder_name} Testing Fee Evaluation.xls"
                        output_file_name = fee_sheet_filename
                        
                        # 构建目标文件路径
                        output_path = os.path.abspath(os.path.join(output_dir, output_file_name))
                        logger.debug(f"目标文件绝对路径: {output_path}")
                        
                        use_existing_file = False
                        
                        # 从子文件夹名称中提取product_description
                        folder_name = os.path.basename(folder_path)
                        if folder_name.startswith(dl_number):
                            product_description = folder_name[len(dl_number):].strip()
                            logger.debug(f"从子文件夹名称提取的product_description: {product_description}")
                else:
                    # 未找到包含DL编号的子文件夹，需要创建新文件夹
                    logger.info("未找到包含DL编号的子文件夹，将创建新文件夹并生成新文件")
                    
                    # 参考excel_initializer的路径构建思路
                    # 构造项目子文件夹名称
                    project_subfolder_name = f"{dl_number} {product_description} {tests_to_be_performed}".strip()
                    # 清理文件名中的非法字符
                    project_subfolder_name = self._sanitize_filename(project_subfolder_name)
                    
                    # 构建目标文件夹路径
                    output_dir = os.path.abspath(os.path.join(current_project, project_subfolder_name))
                    logger.debug(f"目标文件夹绝对路径: {output_dir}")
                    
                    # 确保目标文件夹存在
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # 构造费用表文件名
                    project_subfolder_name = f"{dl_number} {product_description} {tests_to_be_performed}".strip()
                    project_subfolder_name = self._sanitize_filename(project_subfolder_name)
                    fee_sheet_filename = f"{project_subfolder_name} Testing Fee Evaluation.xls"
                    output_file_name = fee_sheet_filename
                    
                    # 构建目标文件路径
                    output_path = os.path.abspath(os.path.join(output_dir, output_file_name))
                    logger.debug(f"目标文件绝对路径: {output_path}")
                    
                    use_existing_file = False
                    
                logger.info(f"费用表将保存到项目路径: {output_path}")
            else:
                # 没有打开项目，使用默认输出逻辑
                logger.info("未检测到打开的项目，使用默认输出路径")
                os.makedirs(self.output_dir, exist_ok=True)
                
                # 生成输出文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                templates = self._find_fee_sheet_templates()
                if not templates:
                    logger.error("未找到费用表模板文件")
                    return (False, None)
                
                template_path = templates[0]  # 使用第一个模板
                file_name = os.path.basename(template_path)
                name_part, ext = os.path.splitext(file_name)
                output_file_name = f"{dl_number}_{name_part}_FeeSheet_{timestamp}{ext}"
                output_path = os.path.join(self.output_dir, output_file_name)
                output_dir = self.output_dir
                
                # 在默认输出模式下总是生成新文件
                use_existing_file = False
                
                logger.info(f"费用表将保存到默认路径: {output_path}")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取测试项目信息
            group_tests_info = self._get_group_tests_from_matrix(matrix_data_structure)
            
            # 初始化COM
            pythoncom.CoInitialize()
            
            # 处理文件
            logger.info(f"正在处理费用表文件: {output_path}")
            
            # 只有在需要生成新文件时才复制模板
            if not use_existing_file:
                # 查找费用表模板
                templates = self._find_fee_sheet_templates()
                if not templates:
                    logger.error("未找到费用表模板文件")
                    return (False, None)
                
                template_path = templates[0]
                
                # 复制模板
                shutil.copy2(template_path, output_path)
                logger.info(f"已复制模板文件到: {output_path}")
            
            # 使用win32com打开Excel（无论是否使用现有文件都要执行）
            excel_app = None
            wb = None
            ws = None
            try:
                excel_app = win32.Dispatch("Excel.Application")
                # 有些版本的Excel可能不支持直接设置Visible和DisplayAlerts属性
                try:
                    excel_app.Visible = False
                except:
                    pass  # 如果不能设置Visible属性，就跳过
                try:
                    excel_app.DisplayAlerts = False
                except:
                    pass  # 如果不能设置DisplayAlerts属性，就跳过
                
                # 打开文件
                wb = excel_app.Workbooks.Open(output_path)
                ws = wb.Sheets(1)

                if use_existing_file:
                    existing_anchor = self._find_sample_preparation_anchor(ws)
                    if not existing_anchor:
                        logger.warning("现有费用表不包含标准模板主体结构，将使用标准模板重建后再填充")
                        try:
                            wb.Close(SaveChanges=False)
                        except Exception:
                            pass
                        wb = None
                        try:
                            excel_app.Quit()
                        except Exception:
                            pass
                        excel_app = None

                        rebuilt = self._rebuild_existing_fee_sheet_from_template(output_path)
                        if not rebuilt:
                            return (False, None)

                        use_existing_file = False
                        excel_app = win32.Dispatch("Excel.Application")
                        try:
                            excel_app.Visible = False
                        except Exception:
                            pass
                        try:
                            excel_app.DisplayAlerts = False
                        except Exception:
                            pass
                        wb = excel_app.Workbooks.Open(output_path)
                        ws = wb.Sheets(1)
                
                # 填充测试组别数据（这是主要功能，无论是否使用现有文件都要执行）
                success = self._fill_group_tests_data(ws, group_tests_info)
                
                if not success:
                    logger.warning(f"填充测试组别数据失败: {output_path}")
                    return (False, None)
                
                # 只有在不是使用现有文件时才填充基本信息
                if not use_existing_file:
                    # 填充基本信息，保留原有格式
                    # D2 (第2行第4列) - 只设置Value，不改变格式
                    if dl_number:
                        ws.Range("D2").Value = dl_number
                    # G2 (第2行第7列)
                    if product_description or tests_to_be_performed:
                        combined_desc = f"{product_description} {tests_to_be_performed}".strip()
                        ws.Range("G2").Value = combined_desc
                    # D3 (第3行第4列)
                    if requested_by:
                        ws.Range("D3").Value = requested_by
                    # G3 (第3行第7列)
                    if location:
                        ws.Range("G3").Value = location
                    
                    logger.info(f"基本信息和测试组别数据已填充到: {output_path}，格式已保留")
                else:
                    logger.info(f"使用现有费用表文件: {output_path}，已填充测试组别数据")
                
                # 保存
                wb.Save()
                
            except Exception as e:
                logger.error(f"处理文件时出错: {e}", exc_info=True)
                return (False, None)
            finally:
                # 正确关闭工作簿和Excel应用
                if wb:
                    try:
                        wb.Close(SaveChanges=True)
                    except:
                        pass
                if excel_app:
                    try:
                        excel_app.Quit()
                    except:
                        pass
        
            # 在所有文件处理完成后取消COM初始化
            pythoncom.CoUninitialize()
            
            logger.info("费用表导出完成！")
            return (True, output_path)
            
        except Exception as e:
            logger.error(f"导出费用表时出错: {e}", exc_info=True)
            return (False, None)
