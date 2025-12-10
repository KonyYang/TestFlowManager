from src.features.matrix.service.export.service.base_export_service import BaseExportService
from src.features.matrix.service.export.service.excel_formatting_service import ExcelFormattingService
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
from openpyxl.utils import get_column_letter
from src.core.logger import logger
import re


class LLCRExportService(BaseExportService):
    """LLCR导出服务"""
    
    def __init__(self, data_model):
        super().__init__(data_model)
        self.formatting_service = ExcelFormattingService()
    
    def export_to_excel(self, file_path=None, sample_count=5, point_array=None, is_delta_r_checked=False, test_category_dict=None):
        """导出LLCR到Excel"""
        # 设置默认文件路径和文件名
        default_dir = "D:\\outfile"
        default_filename = "test llcr.xlsx"
        
        # 如果没有提供文件路径，使用默认路径和文件名
        if file_path is None:
            import os
            if not os.path.exists(default_dir):
                os.makedirs(default_dir)
            file_path = os.path.join(default_dir, default_filename)
        
        logger.debug(f"开始导出LLCR到 {file_path}")
        try:
            # 创建工作簿
            wb = Workbook()
            
            # 如果提供了test_category_dict，按分组创建多个工作表
            if test_category_dict and isinstance(test_category_dict, dict):
                # 删除默认工作表
                wb.remove(wb.active)
                
                # 为每个类别创建一个工作表
                for category_name, points in test_category_dict.items():
                    # 创建工作表并命名（限制工作表名称长度不超过31个字符）
                    safe_category_name = category_name[:31] if len(category_name) > 31 else category_name
                    ws = wb.create_sheet(safe_category_name)

                    # 插入体积电阻表格
                    self._insert_bulk_resistance_table(ws, "LLCR", "")
                    # 插入测试信息表格
                    self._insert_test_info_table(ws)
                    # 插入记录数据表格
                    self._insert_record_data_table(ws, sample_count, points, is_delta_r_checked)
            else:
                # 如果没有提供test_category_dict，使用原有的逻辑
                # 如果没有提供测试点位数组，则从数据模型中提取
                if point_array is None:
                    point_array = self._extract_point_array()
                
                # 创建工作表并填充数据
                ws = wb.active
                ws.title = "LLCR"
                
                # 插入记录数据表格
                self._insert_record_data_table(ws, sample_count, point_array, is_delta_r_checked)
            
            # 保存文件
            return self._save_workbook_safely(wb, file_path)
        except Exception as e:
            logger.error(f"导出LLCR失败: {e}", exc_info=True)
            return False
    
    def _extract_point_array(self):
        """从Matrix数据中提取测试点位数组"""
        point_array = []
        rows = self.data_model.rows
        
        # 从数据中提取测试点位（通常在"Sample size"行之后）
        sample_size_found = False
        for row in rows:
            if len(row) > 0 and "Sample size" in str(row[0]):
                sample_size_found = True
                continue
                
            if sample_size_found and len(row) > 0 and row[0]:  # 找到非空的第一列
                point_array.append(row[0])
                
        return point_array

    def _insert_bulk_resistance_table(self, ws, testType, crCurrentValue):
        """插入体积电阻表格"""
        BulkTblStartRow = 1  # 体积电阻起始行

        # 体积电阻表头
        if testType == "CR":
            ws.cell(row=BulkTblStartRow, column=1).value = "unit:mV"
            ws.cell(row=BulkTblStartRow, column=2).value = "Voltage"
            ws.cell(row=BulkTblStartRow + 5, column=1).value = "Current(Unit:A)"
            ws.cell(row=BulkTblStartRow + 5, column=2).value = crCurrentValue
        else:
            ws.cell(row=BulkTblStartRow, column=1).value = "unit:mΩ"
            ws.cell(row=BulkTblStartRow, column=2).value = "Resistance"

        # 体积电阻列
        bulk_labels = ["bulk1", "bulk2", "bulk3", "Avg"]
        for i, label in enumerate(bulk_labels):
            ws.cell(row=BulkTblStartRow + 1 + i, column=1).value = label
            ws.cell(row=BulkTblStartRow + 1 + i, column=2).value = 0 if i < 3 else None

        if testType == "CR":
            # 设置数据范围的数字格式为三位小数
            for row in range(BulkTblStartRow + 1, BulkTblStartRow + 5):
                ws.cell(row=row, column=2).number_format = "0.000"
        else:
            # 设置数据范围的数字格式为一位小数
            for row in range(BulkTblStartRow + 1, BulkTblStartRow + 5):
                ws.cell(row=row, column=2).number_format = "0.0"

        # 插入统计公式
        data_range = f"B{BulkTblStartRow + 1}:B{BulkTblStartRow + 3}"
        ws.cell(row=BulkTblStartRow + 4, column=2).value = f"=AVERAGE({data_range})"

        # 设置体积电阻表格格式
        self._set_table_format(ws, BulkTblStartRow, 1, BulkTblStartRow + 5, 2, 0)

    def _insert_test_info_table(self, ws, test_info=None):
        """插入测试信息表格 - 使用默认值"""
        TestInfoStartRow = 1  # 测试信息起始行

        # 使用固定的默认值
        targetFolderName = "Default Folder"  # 可以根据需要修改这个默认值

        # 插入测试信息 - 严格按照VBA代码的逻辑
        ws.cell(row=TestInfoStartRow, column=4).value = "LTR"
        ws.cell(row=TestInfoStartRow + 1, column=4).value = "Tested By"
        ws.cell(row=TestInfoStartRow + 2, column=4).value = "Test Equipment ID"
        ws.cell(row=TestInfoStartRow + 3, column=4).value = "Test Condition"
        ws.cell(row=TestInfoStartRow + 4, column=4).value = "Test Requirement"
        ws.cell(row=TestInfoStartRow, column=6).value = targetFolderName
        ws.cell(row=TestInfoStartRow + 1, column=6).value = "Even Yang"
        ws.cell(row=TestInfoStartRow + 2, column=6).value = "DG-Q-0639/0640"
        ws.cell(row=TestInfoStartRow + 3, column=6).value = "20mV,100mA Max"

        # 注意：VBA代码中还有一行调用 AssignLLCRorCRRequirementFromConfirmSpec 来获取 Test Requirement
        # 这里暂时留空，因为该函数需要额外实现
        ws.cell(row=TestInfoStartRow + 4, column=6).value = ""  # Test Requirement 暂时留空

        # 合并单元格
        for i in range(0, 5):  # 从第0行（TestInfoStartRow）到第4行（TestInfoStartRow + 4）
            # 合并第4列和第5列
            start_cell = ws.cell(row=TestInfoStartRow + i, column=4)
            end_cell = ws.cell(row=TestInfoStartRow + i, column=5)
            ws.merge_cells(start_row=start_cell.row, start_column=start_cell.column,
                           end_row=end_cell.row, end_column=end_cell.column)

            # 合并第6列和第9列
            start_cell = ws.cell(row=TestInfoStartRow + i, column=6)
            end_cell = ws.cell(row=TestInfoStartRow + i, column=9)
            ws.merge_cells(start_row=start_cell.row, start_column=start_cell.column,
                           end_row=end_cell.row, end_column=end_cell.column)

        # 设置测试信息表格格式
        self._set_table_format(ws, TestInfoStartRow, 4, TestInfoStartRow + 4, 9, 0)

        # 设置单元格格式
        for row in range(TestInfoStartRow, TestInfoStartRow + 5):
            for col in range(4, 10):
                cell = ws.cell(row=row, column=col)
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

        # 设置日期环境记录背景格式
        self._set_environment_column_format(ws, TestInfoStartRow, 4, TestInfoStartRow + 4, 9)

    def _insert_record_data_table(self, ws, sample_count, point_array, is_delta_r_checked):
        """插入记录数据表格"""
        try:
            # 初始化变量
            headers_cols = 3
            record_start_col = headers_cols + 1  # 原始记录开始列，头三列是测试组别和测试点位名称
            record_end_col = headers_cols + sample_count
            calculateheader_col = record_end_col + 2 + 1  # 中间空格两列
            calculate_start_col = calculateheader_col + headers_cols  # 开始计算扣除体积电阻的值
            calculate_end_col = calculate_start_col + sample_count - 1
            stat_start_col = calculate_end_col + 1  # 开始统计列

            # 如果勾选了 Delta R，统计列需要延后
            if is_delta_r_checked:
                delta_r_start_col = stat_start_col
                stat_start_col = delta_r_start_col + sample_count

            record_data_tbl_title_row = 9  # 记录数据表头
            total_rows = len(point_array)  # 数据行数

            # 填写原始记录组别和步骤列表头
            ws.cell(row=record_data_tbl_title_row, column=1).value = "LLCR"  # 使用固定值而不是公式
            ws.merge_cells(start_row=record_data_tbl_title_row, start_column=1, end_row=record_data_tbl_title_row, end_column=2)
            ws.cell(row=record_data_tbl_title_row, column=3).value = "S/N"
            
            # 填写统计记录组别和步骤列表头
            ws.cell(row=record_data_tbl_title_row, column=calculateheader_col).value = "unit:mΩ"
            ws.merge_cells(start_row=record_data_tbl_title_row, start_column=calculateheader_col, 
                          end_row=record_data_tbl_title_row, end_column=calculateheader_col + 1)
            ws.cell(row=record_data_tbl_title_row, column=calculateheader_col + 2).value = "S/N"
            
            # 填写原始记录样品编号表头
            for i in range(1, sample_count + 1):
                ws.cell(row=record_data_tbl_title_row, column=i + 3).value = f"{i}#"
            
            # 填写统计记录样品编号表头
            for i in range(1, sample_count + 1):
                ws.cell(row=record_data_tbl_title_row, column=calculate_start_col + i - 1).value = f"{i}#"
            
            # 如果勾选了 Delta R，插入 Delta R 表格
            if is_delta_r_checked:
                # 填写样品编号Delta R表头
                for i in range(1, sample_count + 1):
                    ws.cell(row=record_data_tbl_title_row, column=delta_r_start_col + i - 1).value = f"{i}#" + "ΔR"
            
            # 填写统计标题和日期环境记录
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col).value = "Min"
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 1).value = "Max"
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 2).value = "Average"
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 3).value = "Std Dev"
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 4).value = "Test Date"
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 5).value = "Amb Temp(°C)"
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 6).value = "Rel. Hum.:%"
            
            # 填写测试点位数据
            # 遍历所有组别，插入记录数据表格
            if hasattr(self.data_model, 'group_steps'):
                total_row_offset = 0
                initial_test_row = {}  # 记录每个组的Initial测试行
                
                for group_index, (group_name, steps) in enumerate(self.data_model.group_steps.items()):
                    # 计算当前表格的起始行
                    current_row = record_data_tbl_title_row + 1 + total_row_offset
                    step_count = len(steps)
                    
                    # 填写步骤
                    for step_index, step in enumerate(steps):
                        step_description = step.get("StepDescription", step.get("Test", ""))
                        # 原始记录第二列填充步骤描述
                        ws.cell(row=current_row, column=2).value = step_description.strip()
                        # 统计记录第二列填充步骤描述
                        ws.cell(row=current_row, column=calculateheader_col + 1).value = step_description.strip()
                        
                        # 填写测试点位（第三列显示点位名称）
                        for point_index, point in enumerate(point_array):
                            row_idx = current_row + point_index
                            # 原始记录第三列
                            ws.cell(row=row_idx, column=3).value = point
                            # 统计记录第三列
                            ws.cell(row=row_idx, column=calculateheader_col + 2).value = point
                            
                            # 填写计算公式
                            for i in range(sample_count):
                                # 获取体积电阻平均值的单元格地址
                                bulk_avg_cell = ws.cell(row=5, column=2).coordinate
                                # 插入统计公式
                                calc_cell = ws.cell(row=row_idx, column=calculate_start_col + i)
                                # 原始记录值单元格
                                original_value_cell = ws.cell(row=row_idx, column=i + 4).coordinate
                                calc_cell.value = f"={original_value_cell}-{bulk_avg_cell}"
                        
                        # 处理ΔR计算
                        if is_delta_r_checked:
                            is_initial_step = "Initial" in step_description
                            # 如果是Initial测试步骤，ΔR值等于计算值
                            if is_initial_step:
                                initial_test_row[group_name] = current_row
                                # 填写Delta R公式
                                for point_index, point in enumerate(point_array):
                                    row_idx = current_row + point_index
                                    for i in range(sample_count):
                                        calc_cell_addr = ws.cell(row=row_idx, column=calculate_start_col + i).coordinate
                                        delta_cell = ws.cell(row=row_idx, column=delta_r_start_col + i)
                                        delta_cell.value = f"={calc_cell_addr}"
                            else:
                                # 对于其他步骤，ΔR值等于当前值减去Initial步骤的值
                                if group_name in initial_test_row:
                                    initial_row = initial_test_row[group_name]
                                    for point_index, point in enumerate(point_array):
                                        row_idx = current_row + point_index
                                        initial_row_idx = initial_row + point_index
                                        for i in range(sample_count):
                                            calc_cell_addr = ws.cell(row=row_idx, column=calculate_start_col + i).coordinate
                                            initial_calc_cell_addr = ws.cell(row=initial_row_idx, column=calculate_start_col + i).coordinate
                                            delta_cell = ws.cell(row=row_idx, column=delta_r_start_col + i)
                                            delta_cell.value = f"={calc_cell_addr}-{initial_calc_cell_addr}"
                                else:
                                    # 如果没有找到Initial步骤，给出错误提示
                                    logger.warning(f"未找到Initial步骤，组: {group_name}")
                        
                        # 插入统计公式
                        start_data_cell = ws.cell(row=current_row, column=calculate_start_col).coordinate
                        end_data_cell = ws.cell(row=current_row + len(point_array) - 1, column=calculate_end_col).coordinate
                        data_range = f"{start_data_cell}:{end_data_cell}"
                        
                        ws.cell(row=current_row, column=stat_start_col).value = f"=MIN({data_range})"
                        ws.cell(row=current_row, column=stat_start_col + 1).value = f"=MAX({data_range})"
                        ws.cell(row=current_row, column=stat_start_col + 2).value = f"=AVERAGE({data_range})"
                        ws.cell(row=current_row, column=stat_start_col + 3).value = f"=STDEV({data_range})"
                        
                        # 如果启用了ΔR，也为ΔR列添加统计公式
                        if is_delta_r_checked:
                            start_delta_cell = ws.cell(row=current_row, column=delta_r_start_col).coordinate
                            end_delta_cell = ws.cell(row=current_row + len(point_array) - 1, column=delta_r_start_col + sample_count - 1).coordinate
                            delta_range = f"{start_delta_cell}:{end_delta_cell}"
                            
                            ws.cell(row=current_row, column=stat_start_col + 7).value = f"=MIN({delta_range})"
                            ws.cell(row=current_row, column=stat_start_col + 8).value = f"=MAX({delta_range})"
                            ws.cell(row=current_row, column=stat_start_col + 9).value = f"=AVERAGE({delta_range})"
                            ws.cell(row=current_row, column=stat_start_col + 10).value = f"=STDEV({delta_range})"
                        
                        # 合并统计和日期环境记录的单元格
                        # 总共有11列统计和环境信息（不含ΔR统计时为7列）
                        stat_cols_count = 11 if is_delta_r_checked else 7
                        for i in range(stat_cols_count):
                            ws.merge_cells(
                                start_row=current_row, 
                                start_column=stat_start_col + i,
                                end_row=current_row + len(point_array) - 1,
                                end_column=stat_start_col + i
                            )
                        
                        # 合并第二列步骤
                        ws.merge_cells(
                            start_row=current_row,
                            start_column=2,
                            end_row=current_row + len(point_array) - 1,
                            end_column=2
                        )
                        ws.merge_cells(
                            start_row=current_row,
                            start_column=calculateheader_col + 1,
                            end_row=current_row + len(point_array) - 1,
                            end_column=calculateheader_col + 1
                        )
                        
                        # 更新当前行
                        current_row = current_row + len(point_array)
                    
                    # 填写第一列组名
                    group_start_row = record_data_tbl_title_row + 1 + total_row_offset
                    group_end_row = group_start_row + step_count * len(point_array) - 1
                    
                    ws.cell(row=group_start_row, column=1).value = f"Group {group_name}"
                    ws.merge_cells(
                        start_row=group_start_row,
                        start_column=1,
                        end_row=group_end_row,
                        end_column=1
                    )
                    ws.cell(row=group_start_row, column=calculateheader_col).value = f"Group {group_name}"
                    ws.merge_cells(
                        start_row=group_start_row,
                        start_column=calculateheader_col,
                        end_row=group_end_row,
                        end_column=calculateheader_col
                    )
                    
                    total_row_offset += step_count * len(point_array)
                
                # 设置统计数据背景格式
                end_row = record_data_tbl_title_row + total_row_offset
                self._set_stat_column_format(ws, record_data_tbl_title_row, stat_start_col, end_row, stat_start_col + 3)
                
                # 设置日期环境记录背景格式
                self._set_environment_column_format(ws, record_data_tbl_title_row, stat_start_col + 4, end_row, stat_start_col + 6)
                
                # 如果启用了ΔR，还需要为ΔR统计列设置背景格式
                if is_delta_r_checked:
                    self._set_stat_column_format(ws, record_data_tbl_title_row, stat_start_col + 7, end_row, stat_start_col + 10)
            else:
                # 原有逻辑，如果没有group_steps属性
                for row_idx, point in enumerate(point_array, 1):
                    actual_row = record_data_tbl_title_row + row_idx
                    # 填写测试点位列
                    ws.cell(row=actual_row, column=2).value = point
                    
                    # 填写样品编号列（留空让用户填写）
                    for i in range(sample_count):
                        # 不需要显式设置值，保持为空即可
                        pass
                    
                    # 填写计算公式
                    for i in range(sample_count):
                        # 获取体积电阻平均值的单元格地址
                        bulk_avg_cell = ws.cell(row=5, column=2).coordinate
                        # 插入统计公式
                        calc_cell = ws.cell(row=actual_row, column=calculate_start_col + i)
                        # 原始记录值单元格
                        original_value_cell = ws.cell(row=actual_row, column=i + 4).coordinate
                        calc_cell.value = f"={original_value_cell}-{bulk_avg_cell}"
                        
                    # 插入统计公式
                    start_data_cell = ws.cell(row=actual_row, column=calculate_start_col).coordinate
                    end_data_cell = ws.cell(row=actual_row, column=calculate_end_col).coordinate
                    data_range = f"{start_data_cell}:{end_data_cell}"
                    
                    ws.cell(row=actual_row, column=stat_start_col).value = f"=MIN({data_range})"
                    ws.cell(row=actual_row, column=stat_start_col + 1).value = f"=MAX({data_range})"
                    ws.cell(row=actual_row, column=stat_start_col + 2).value = f"=AVERAGE({data_range})"
                    ws.cell(row=actual_row, column=stat_start_col + 3).value = f"=STDEV({data_range})"
                    
                    # 填写计算列标题
                    if row_idx == 1:  # 只在第一行填写
                        ws.cell(row=actual_row, column=calculateheader_col).value = "Max"
                        ws.cell(row=actual_row, column=calculateheader_col + 1).value = "Min"
                
                # 填写统计列标题
                ws.cell(row=record_data_tbl_title_row, column=stat_start_col).value = "Min"
                ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 1).value = "Max"
                ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 2).value = "Average"
                ws.cell(row=record_data_tbl_title_row, column=stat_start_col + 3).value = "Std Dev"
            
            # 应用格式化
            self._apply_formatting(ws, record_data_tbl_title_row, sample_count, len(point_array), 
                                 calculateheader_col, calculate_start_col, stat_start_col, is_delta_r_checked)
                                 
        except Exception as e:
            logger.error(f"插入记录数据表格时出错: {e}", exc_info=True)

    def _set_table_format(self, ws, start_row, start_col, end_row, end_col, column_color_count):
        """设置表格格式 - 参考VBA SetTableFormat函数"""
        # 设置整个范围的字体为 Arial
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell = ws.cell(row=row, column=col)
                # 设置字体为 Arial
                if cell.font is None:
                    cell.font = Font(name='Arial')
                else:
                    # 创建新的字体对象而不是修改现有对象
                    cell.font = Font(name='Arial', bold=cell.font.bold, size=cell.font.size, color=cell.font.color)

        # 设置单元格边框 - 使用较粗的边框样式
        thick_border = Border(
            left=Side(style='medium'),  # 对应VBA LineStyle=1, Weight=2
            right=Side(style='medium'),
            top=Side(style='medium'),
            bottom=Side(style='medium')
        )

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = thick_border

        # 设置单元格内容水平和垂直居中，并启用自动换行
        center_alignment = Alignment(
            horizontal='center',
            vertical='center',
            wrap_text=True  # 启用自动换行
        )

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell = ws.cell(row=row, column=col)
                cell.alignment = center_alignment

        # 设置首行（表头）格式 - 加粗和浅灰色背景
        header_fill = PatternFill(start_color="DCDCDC", end_color="DCDCDC", fill_type="solid")  # RGB(220,220,220)
        for col in range(start_col, end_col + 1):
            cell = ws.cell(row=start_row, column=col)
            cell.font = Font(name='Arial', bold=True)
            cell.fill = header_fill

        # 设置前几列的格式（根据column_color_count参数）
        first_col_fill = PatternFill(start_color="DCDCDC", end_color="DCDCDC", fill_type="solid")  # RGB(220,220,220)
        # 注意：这里start_col + column_color_count可能需要根据实际需求调整
        # VBA中是设置从第start_col列到第start_col + ColumnColorCount列
        for row in range(start_row, end_row + 1):
            for col in range(start_col, min(start_col + column_color_count + 1, end_col + 1)):
                cell = ws.cell(row=row, column=col)
                cell.font = Font(name='Arial', bold=True)
                cell.fill = first_col_fill

        # 设置第二列宽度为12
        column_letter = get_column_letter(2)
        ws.column_dimensions[column_letter].width = 12

    def _set_stat_column_format(self, worksheet, title_row, start_col, end_row, end_col):
        """设置统计数据背景格式"""
        try:
            # 获取环境记录列范围
            for row in range(title_row, end_row + 1):
                for col in range(start_col, end_col + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")
            
            # 设置 start_col + 1 列的字体加粗 (Max列)
            for row in range(title_row + 1, end_row + 1):
                cell = worksheet.cell(row=row, column=start_col + 1)
                cell.font = Font(bold=True)
        except Exception as e:
            logger.error(f"设置统计数据背景格式时出错: {e}", exc_info=True)
            
    def _set_environment_column_format(self, worksheet, title_row, start_col, end_row, end_col):
        """设置日期环境记录格式"""
        try:
            # 获取环境记录列范围
            for row in range(title_row, end_row + 1):
                for col in range(start_col, end_col + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")  # 淡黄色
                    cell.font = Font(bold=True)
        except Exception as e:
            logger.error(f"设置环境记录背景格式时出错: {e}", exc_info=True)


    def _apply_formatting(self, worksheet, title_row, sample_count, point_count, 
                         calculateheader_col, calculate_start_col, stat_start_col, is_delta_r_checked):
        """应用表格格式化"""
        try:
            # 定义边框样式
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # 定义字体
            font = Font(name='Arial', size=9)
            
            # 定义灰色背景填充
            gray_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            # 获取实际使用的行列数
            last_row = title_row + point_count
            last_col = stat_start_col + 6  # 包括环境记录列
            
            # 如果有group_steps属性，需要重新计算last_row
            if hasattr(self.data_model, 'group_steps'):
                total_steps = sum(len(steps) for steps in self.data_model.group_steps.values())
                last_row = title_row + total_steps * point_count
                
            # 如果启用了ΔR，需要增加列数
            if is_delta_r_checked:
                last_col += 4  # ΔR统计列
            
            # 定义整个表格区域
            for row in range(title_row, last_row + 1):
                for col in range(1, last_col + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.font = font
            
            # 设置表头行粗体并添加灰色背景
            for col in range(1, last_col + 1):
                cell = worksheet.cell(row=title_row, column=col)
                cell.font = Font(name='Arial', size=9, bold=True)
                cell.fill = gray_fill
            
            # 设置前几列的格式（加粗和灰色背景）
            for row in range(title_row, last_row + 1):
                # 第一列和第二列等关键列
                key_columns = [1, 2, calculateheader_col, calculateheader_col + 1]
                for col in key_columns:
                    if col <= last_col:  # 确保列索引不超过实际列数
                        cell = worksheet.cell(row=row, column=col)
                        cell.font = Font(name='Arial', size=9, bold=True)
                        cell.fill = gray_fill
            
            # 设置列宽
            for col in range(1, last_col + 1):
                column_letter = get_column_letter(col)
                if col in [1, 2, calculateheader_col, calculateheader_col+1, stat_start_col, stat_start_col+1, stat_start_col+2, stat_start_col+3]:
                    worksheet.column_dimensions[column_letter].width = 15
                else:
                    worksheet.column_dimensions[column_letter].width = 10
            
            # 自动调整行高
            for row in range(title_row, last_row + 1):
                worksheet.row_dimensions[row].height = 20
                
            logger.debug("LLCR格式化应用完成")
            
        except Exception as e:
            logger.error(f"应用LLCR格式化时出错: {e}", exc_info=True)