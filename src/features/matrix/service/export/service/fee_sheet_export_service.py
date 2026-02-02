"""
费用表导出服务
提供生成费用表的业务逻辑服务
"""

from typing import Dict, Any, List, Optional
from src.core.logger import logger
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

    def __init__(self):
        """初始化费用表导出服务"""
        self.template_dir = r"D:\TestFlowManager\Template"
        self.output_dir = r"D:\OutFile"
        self.excel_app = None

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

    def _fill_group_tests_data(self, worksheet, group_tests_info: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        填充测试组别数据到Excel表格中
        :param worksheet: Excel工作表对象
        :param group_tests_info: 包含每个组别测试项目信息的字典
        :return: 是否成功填充
        """
        try:
            # 现在我们知道第5行是'Sample preparation (if needed)'，第6行是空白行模板
            base_row = 5  # 'Sample preparation (if needed)' 行
            template_row = 6  # 空白行模板
            
            # 检查基础行是否存在
            base_cell_value = worksheet.Cells(base_row, 3).Value  # C列第5行
            if not base_cell_value or 'Sample preparation' not in str(base_cell_value):
                logger.warning("未找到'Sample preparation (if needed)'行，无法按要求填充组别数据")
                return False
            
            template_cell_value = worksheet.Cells(template_row, 3).Value  # C列第6行
            if template_cell_value is not None:
                logger.warning("第6行不是空白行模板，无法按要求复制行")
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
                
                # 去重：对于每个组别，同名的test只需要保留一次
                unique_tests = []
                seen_tests = set()
                for test_info in tests_list:
                    test_name = test_info.get('test', '').strip().lower()
                    if test_name and test_name not in seen_tests:
                        unique_tests.append(test_info)
                        seen_tests.add(test_name)
                
                num_tests = len(unique_tests)
                
                # 获取第5行和第6行的列数
                max_cols = used_range.Columns.Count
                
                # 对于第一个组别(Group 1)
                if group_idx == 0:
                    # Group 1使用第6行作为第一个测试项目，但A列合并需要包含第5行
                    # 首先在第6行填入第一个测试项目
                    worksheet.Cells(current_row, 3).Value = unique_tests[0].get('test', '') if unique_tests else ''
                    
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
                            if i + 1 < len(unique_tests):
                                worksheet.Cells(insert_position, 3).Value = unique_tests[i + 1].get('test', '')
                                logger.debug(f"  在第{insert_position}行C列插入新行并填入测试项目: {unique_tests[i + 1].get('test', '')}")
                    
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
                        if i < len(unique_tests):
                            worksheet.Cells(insert_position, 3).Value = unique_tests[i].get('test', '')
                            logger.debug(f"  在第{insert_position}行插入新行并填入测试项目: {unique_tests[i].get('test', '')}")
                    
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
                    
                logger.debug(f"  组别{group_name}填充完成，原始测试数: {len(tests_list)}, 去重后测试数: {num_tests}")
            
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

    def export_fee_sheet(self, matrix_data_structure: MatrixDataStructure, 
                         dl_number: str = "DL-UNKNOWN", 
                         requested_by: str = "", 
                         location: str = "",
                         product_description: str = "",
                         tests_to_be_performed: str = "") -> bool:
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
            
            # 创建输出目录
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 查找费用表模板
            templates = self._find_fee_sheet_templates()
            if not templates:
                logger.error("未找到费用表模板文件")
                return False
            
            # 获取测试项目信息
            group_tests_info = self._get_group_tests_from_matrix(matrix_data_structure)
            
            # 初始化COM
            pythoncom.CoInitialize()
            
            # 处理每个模板文件
            for template_path in templates:
                logger.info(f"正在处理模板: {template_path}")
                
                # 生成输出文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_name = os.path.basename(template_path)
                name_part, ext = os.path.splitext(file_name)
                output_file_name = f"{dl_number}_{name_part}_FeeSheet_{timestamp}{ext}"
                output_path = os.path.join(self.output_dir, output_file_name)
                
                # 复制模板
                shutil.copy2(template_path, output_path)
                
                # 使用win32com打开Excel
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
                    
                    # 填充数据，保留原有格式
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
                    
                    # 填充测试组别数据
                    success = self._fill_group_tests_data(ws, group_tests_info)
                    
                    if not success:
                        logger.warning(f"填充测试组别数据失败: {output_path}")
                        continue
                    
                    logger.info(f"数据已填充到: {output_path}，格式已保留")
                    
                    # 保存
                    wb.Save()
                    
                except Exception as e:
                    logger.error(f"处理文件时出错: {e}", exc_info=True)
                    return False
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
            return True
            
        except Exception as e:
            logger.error(f"导出费用表时出错: {e}", exc_info=True)
            return False