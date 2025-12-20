from src.core.logger import logger
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font, PatternFill


class TestRecordTableStructureService:
    """Test Record表格结构服务 - 专门处理Test Record的各种表格结构创建"""

    def __init__(self, formatting_service, formula_service, styling_service):
        self.formatting_service = formatting_service
        self.formula_service = formula_service
        self.styling_service = styling_service

    def insert_record_data_table(self, ws, sample_count_or_group_name, point_array, sample_count, 
                                is_delta_r_checked=False, cr_current_value="", test_type=None, 
                                matrix_data=None, is_first_group=True, total_row_offset=0,
                                initial_test_rows=None, first_group_stat_start_col=None):
        """插入记录数据表格 - 增强版本，支持Matrix数据结构"""
        try:
            logger.debug(f"开始处理工作表 {ws.title} 的记录数据表格")
            group_name = None
            
            # 判断第一个参数是sample_count还是group_name
            if isinstance(sample_count_or_group_name, str):
                # 新的Matrix数据模式
                group_name = sample_count_or_group_name
                logger.debug(f"处理组: {group_name}, is_first_group: {is_first_group}")
                if not matrix_data:
                    logger.error("Matrix数据未设置，无法插入记录数据表格")
                    return

                # 定义过滤函数
                def test_type_filter(step):
                    # 如果没有指定测试类型，则包含所有步骤
                    if not test_type or test_type not in ["LLCR", "CR"]:
                        return True
                    # 只包含与当前测试类型匹配的步骤
                    return step.get("Test", "").upper() == test_type.upper()

                # 根据测试类型过滤获取相应的测试数据
                group_data = matrix_data.get_test_data_for_export(group_name, test_type_filter)
                if not group_data:
                    logger.warning(f"组 {group_name} 没有可用的测试数据")
                    return

                step_dict = group_data["step_dict"]
                # sample_count已经在函数参数中传入，我们直接使用它
                group_col_index = group_data["column_index"]
            else:
                # 原有的sample_count模式（向后兼容）
                sample_count = sample_count_or_group_name
                step_dict = {"1": "Test Step"}  # 默认步骤
                group_name = "Default"
                group_col_index = -1

            # 验证输入参数
            if not self._validate_inputs(point_array, step_dict):
                return

            # 初始化变量
            headers_cols = 3
            record_start_col = headers_cols + 1  # 原始记录开始列，头三列是测试组别和测试点位名称
            record_end_col = headers_cols + sample_count
            calculateheader_col = record_end_col + 2 + 1  # 中间空格两列
            calculate_start_col = calculateheader_col + headers_cols  # 开始计算扣除体积电阻的值
            calculate_end_col = calculate_start_col + sample_count - 1
            # 打印calculateheader_col的初始值和样本数量
            logger.debug(f"[{group_name}] 样本数量: {sample_count}, calculateheader_col初始值: {calculateheader_col}")

            # 计算统计列起始位置，考虑total_row_offset的影响
            # 使用全局固定的统计列起始位置，避免每个组独立计算导致偏移
            total_column_offset = 0  # 初始化列偏移量
            if is_first_group:
                stat_start_col = calculate_end_col + 1  # 第一个组使用相对位置
                # 保存第一个组的统计列起始位置，供后续组使用
                first_group_stat_start_col = stat_start_col
                logger.debug(f"[{group_name}] 是第一个组，stat_start_col设置为: {stat_start_col}")
            else:
                # 后续组使用第一个组的统计列起始位置，确保统计列位置一致
                if first_group_stat_start_col is not None:
                    stat_start_col = first_group_stat_start_col
                else:
                    # 如果没有提供first_group_stat_start_col，则使用默认计算方式
                    stat_start_col = calculate_end_col + 1
                logger.debug(f"[{group_name}] 不是第一个组，stat_start_col: {stat_start_col}")

            # 如果勾选了 Delta R，统计列需要延后（仅对LLCR有效）
            delta_r_start_col = None
            if is_delta_r_checked and test_type == "LLCR":
                delta_r_start_col = stat_start_col
                stat_start_col = delta_r_start_col + sample_count
                logger.debug(f"[{group_name}] Delta R已勾选，delta_r_start_col: {delta_r_start_col}, 新stat_start_col: {stat_start_col}")

            record_data_tbl_title_row = 9  # 记录数据表头
            total_rows = len(point_array)  # 数据行数

            # 如果是第一个group，插入记录数据表格表头
            if is_first_group:
                # logger.debug(f"[{group_name}] 插入表头前 calculateheader_col: {calculateheader_col}")
                self._insert_table_headers(ws, headers_cols, record_start_col, record_end_col,
                                          calculateheader_col, calculate_start_col, calculate_end_col,
                                          stat_start_col, delta_r_start_col, sample_count, 
                                          is_delta_r_checked, cr_current_value, test_type, is_first_group)
                is_first_group = False
                logger.debug(f"[{group_name}] 已插入表头，设置is_first_group为False")

            # 计算当前表格的起始行
            current_row = 10 + total_row_offset
            logger.debug(f"[{group_name}] 当前工作表起始行: {current_row}, 总行偏移量: {total_row_offset}")
            logger.debug(f"[{group_name}] 当前工作表起始行: {current_row}, 总行偏移量: {total_row_offset}")

            # 填写步骤
            for step_key, step_description in step_dict.items():
                # 打印当前步骤的calculateheader_col值
                logger.debug(f"[{group_name}] 步骤 {step_key} 处理中, calculateheader_col: {calculateheader_col}, stat_start_col: {stat_start_col}")
                
                # 填写步骤描述
                ws.cell(row=current_row, column=2).value = step_description.strip()
                ws.cell(row=current_row, column=calculateheader_col + 1).value = step_description.strip()

                # 填写测试点位
                for j, point in enumerate(point_array):
                    row_idx = current_row + j
                    ws.cell(row=row_idx, column=3).value = point
                    ws.cell(row=row_idx, column=calculateheader_col + 2).value = point

                # 获取体积电阻平均值的单元格地址（B5）
                bulk_avg_cell = "B5"
                # 获取CR电流值的单元格地址（如果需要）
                current_cr_cell = "B6" if test_type == "CR" and cr_current_value else None

                # 插入计算公式
                self._insert_calculation_formulas(ws, current_row, point_array, sample_count,
                                                  calculate_start_col, bulk_avg_cell, current_cr_cell, test_type)

                # 如果勾选了 Delta R，插入 Delta R 并填写公式（仅对LLCR有效）
                if is_delta_r_checked and test_type == "LLCR" and delta_r_start_col:
                    self._handle_delta_r(ws, current_row, point_array, sample_count,
                                         delta_r_start_col, calculate_start_col, step_description, test_type,
                                         initial_test_rows, total_row_offset)

                # 插入统计公式
                self._insert_statistics_formulas(ws, current_row, point_array, sample_count,
                                                 calculate_start_col, calculate_end_col, stat_start_col,
                                                 delta_r_start_col, is_delta_r_checked, test_type)

                # 设置数据范围的数字格式
                self._set_number_format(ws, current_row, point_array, sample_count,
                                        record_start_col, record_end_col, calculate_start_col, stat_start_col, test_type)

                # 合并单元格
                self._merge_cells_for_step(ws, current_row, point_array, stat_start_col, calculateheader_col)

                # 更新当前行
                current_row = current_row + len(point_array)

            # 填写第一列组名
            ws.cell(row=10 + total_row_offset, column=1).value = f"Group {group_name}"
            if len(point_array) > 0:
                ws.merge_cells(start_row=10 + total_row_offset, start_column=1,
                               end_row=current_row - 1, end_column=1)

            ws.cell(row=10 + total_row_offset, column=calculateheader_col).value = f"Group {group_name}"
            if len(point_array) > 0:
                ws.merge_cells(start_row=10 + total_row_offset, start_column=calculateheader_col,
                               end_row=current_row - 1, end_column=calculateheader_col)

            # 更新总偏移量
            step_count = len(step_dict)

            # 保存当前组的行偏移量，用于后续计算
            current_total_row_offset = total_row_offset
            total_row_offset += step_count * len(point_array)
            logger.debug(f"[{group_name}] 更新总行偏移量: {total_row_offset}, 步骤数: {step_count}, 点位数: {len(point_array)}")

            # 更新总列偏移量
            total_column_offset += (calculate_end_col - record_start_col + 1)

            # 只有在最后一个组处理完后才设置统计数据背景格式和环境记录格式
            # 获取所有组的数量
            all_groups = []
            if matrix_data:
                all_groups = matrix_data.get_all_groups()
        
            # 当处理到最后一个组时，设置统计列和环境列的格式
            is_last_group = (group_name == all_groups[-1] if all_groups else True)
        
            end_row = record_data_tbl_title_row + total_row_offset

            # 设置统计数据背景格式
            self._set_stat_column_format(ws, record_data_tbl_title_row, stat_start_col, end_row, stat_start_col + 3)
            # 设置日期环境记录背景格式
            env_start_col = stat_start_col + 4
            self._set_environment_column_format(ws, record_data_tbl_title_row, env_start_col, end_row,
                                                env_start_col + 2)
            # 设置记录表格格式
            logger.debug(f"设置记录表格格式，范围1: ({record_data_tbl_title_row}, 1) 到 ({end_row}, {record_end_col})")
            self._set_table_format(ws, record_data_tbl_title_row, 1, end_row, record_end_col, 2)
            logger.debug(f"设置记录表格格式，范围2: ({record_data_tbl_title_row}, {calculateheader_col}) 到 ({end_row}, {stat_start_col + 6})")
            self._set_table_format(ws, record_data_tbl_title_row, calculateheader_col, end_row, stat_start_col + 6, 2)

            logger.debug(f"成功插入组 {group_name} 的记录数据表格，步骤数: {step_count}")
            
            # 返回更新后的状态变量
            return {
                "total_row_offset": total_row_offset,
                "is_first_group": is_first_group,
                "total_column_offset": total_column_offset,
                "first_group_stat_start_col": first_group_stat_start_col
            }

        except Exception as e:
            logger.error(f"插入记录数据表格时出错: {e}", exc_info=True)
            return None

    def _validate_inputs(self, point_array, step_dict):
        """验证输入参数"""
        if not isinstance(point_array, list) or len(point_array) == 0:
            logger.error("测试点位数组为空或未正确初始化！")
            return False

        if not step_dict or len(step_dict) == 0:
            logger.error("步骤字典为空或未正确初始化！")
            return False

        return True

    def _insert_table_headers(self, ws, headers_cols, record_start_col, record_end_col,
                              calculateheader_col, calculate_start_col, calculate_end_col,
                              stat_start_col, delta_r_start_col, sample_count, is_delta_r_checked, 
                              cr_current_value, test_type, is_first_group=True):
        """插入表格表头"""
        record_data_tbl_title_row = 9
        logger.debug(f"插入表头到工作表 {ws.title}, record_data_tbl_title_row={record_data_tbl_title_row}")

        # 填写原始记录组别和步骤列表头
        title_value = f"CR {cr_current_value}A" if test_type == "CR" and cr_current_value else test_type if test_type else "LLCR"
        ws.cell(row=record_data_tbl_title_row, column=1).value = title_value
        ws.merge_cells(start_row=record_data_tbl_title_row, start_column=1,
                       end_row=record_data_tbl_title_row, end_column=2)

        # 合并单元格样式
        self._merge_cells_style(ws, record_data_tbl_title_row, 1, 2)

        ws.cell(row=record_data_tbl_title_row, column=3).value = "S/N"

        # 填写统计记录组别和步骤列表头
        ws.cell(row=record_data_tbl_title_row, column=calculateheader_col).value = "unit:mΩ"
        ws.merge_cells(start_row=record_data_tbl_title_row, start_column=calculateheader_col,
                       end_row=record_data_tbl_title_row, end_column=calculateheader_col + 1)
        self._merge_cells_style(ws, record_data_tbl_title_row, calculateheader_col, calculateheader_col + 1)

        ws.cell(row=record_data_tbl_title_row, column=calculateheader_col + 2).value = "S/N"

        # 填写原始记录样品编号表头
        for i in range(1, sample_count + 1):
            ws.cell(row=record_data_tbl_title_row, column=i + headers_cols).value = f"{i}#"

        # 填写统计记录样品编号表头
        for i in range(1, sample_count + 1):
            ws.cell(row=record_data_tbl_title_row, column=calculate_start_col + i - 1).value = f"{i}#"

        # 如果勾选了 Delta R，插入 Delta R 表格 (仅对LLCR有效)
        # 只在第一个组时插入Delta R表头
        if is_first_group and is_delta_r_checked and test_type == "LLCR" and delta_r_start_col:
            for i in range(1, sample_count + 1):
                ws.cell(row=record_data_tbl_title_row, column=delta_r_start_col + i - 1).value = f"{i}#ΔR"

        # 填写统计标题和日期环境记录
        # 只在第一个组时插入统计标题和环境记录
        if is_first_group:
            stat_headers = ["Min", "Max", "Avg", "Stdev", "Test Date", "Amb Temp(°C)", "Rel. Hum.:%"]
            for i, header in enumerate(stat_headers):
                ws.cell(row=record_data_tbl_title_row, column=stat_start_col + i).value = header

        # 设置表头样式
        self._set_header_style(ws, record_data_tbl_title_row, stat_start_col)
        logger.debug(f"完成表头插入到工作表 {ws.title}")

    def _insert_calculation_formulas(self, ws, current_row, point_array, sample_count,
                                     calculate_start_col, bulk_avg_cell, current_cr_cell, test_type):
        """插入计算公式"""
        self.formula_service.insert_calculation_formulas(
            ws, current_row, point_array, sample_count,
            calculate_start_col, bulk_avg_cell, current_cr_cell, test_type
        )

    def _handle_delta_r(self, ws, current_row, point_array, sample_count,
                        delta_r_start_col, calculate_start_col, step_description, test_type,
                        initial_test_rows, total_row_offset):
        """处理Delta R计算"""
        self.formula_service.handle_delta_r(
            ws, current_row, point_array, sample_count,
            delta_r_start_col, calculate_start_col, step_description,
            test_type, initial_test_rows, total_row_offset
        )

    def _insert_statistics_formulas(self, ws, current_row, point_array, sample_count,
                                    calculate_start_col, calculate_end_col, stat_start_col,
                                    delta_r_start_col, is_delta_r_checked, test_type):
        """插入统计公式"""
        self.formula_service.insert_statistics_formulas(
            ws, current_row, point_array, sample_count,
            calculate_start_col, calculate_end_col, stat_start_col,
            delta_r_start_col, is_delta_r_checked, test_type
        )

    def _set_number_format(self, ws, current_row, point_array, sample_count,
                           record_start_col, record_end_col, calculate_start_col, stat_start_col, test_type):
        """设置数字格式"""
        self.styling_service.set_number_format(
            ws, current_row, point_array, sample_count,
            record_start_col, record_end_col, calculate_start_col, stat_start_col, test_type
        )

    def _merge_cells_for_step(self, ws, current_row, point_array, stat_start_col, calculateheader_col):
        """合并步骤相关的单元格"""
        rows_count = len(point_array)
        logger.debug(f"合并单元格，起始行: {current_row}, 行数: {rows_count}, stat_start_col: {stat_start_col}, calculateheader_col: {calculateheader_col}")

        # 合并统计列
        for i in range(7):  # Min到Rel. Hum.:% 共7列
            if stat_start_col + i <= stat_start_col + 6: # 确保安全范围
                start_row = current_row
                end_row = current_row + rows_count - 1
                col = stat_start_col + i
                logger.debug(f"合并统计列单元格: ({start_row}, {col}) 到 ({end_row}, {col})")
                ws.merge_cells(start_row=start_row, start_column=col,
                               end_row=end_row, end_column=col)
                self._merge_cells_style(ws, start_row, col, rows_count)

        # 合并步骤描述列
        logger.debug(f"合并步骤描述列单元格: ({current_row}, 2) 到 ({current_row + rows_count - 1}, 2)")
        ws.merge_cells(start_row=current_row, start_column=2,
                       end_row=current_row + rows_count - 1, end_column=2)
        self._merge_cells_style(ws, current_row, 2, rows_count)

        # 合并计算区域的步骤描述列（对应统计列的步骤描述）
        logger.debug(f"合并计算区域步骤描述列单元格: ({current_row}, {calculateheader_col+1}) 到 ({current_row + rows_count - 1}, {calculateheader_col+1})")
        ws.merge_cells(start_row=current_row, start_column=calculateheader_col + 1,
                       end_row=current_row + rows_count - 1, end_column=calculateheader_col + 1)
        self._merge_cells_style(ws, current_row, 5, rows_count)

    def _merge_cells_style(self, ws, start_row, start_col, row_span):
        """设置合并单元格样式"""
        self.formatting_service.format_merge_cells_style(ws, start_row, start_col, row_span)

    def _set_header_style(self, ws, title_row, stat_start_col):
        """设置表头样式"""
        self.formatting_service.format_range_bold_header(ws, title_row, stat_start_col)
        
    def _set_table_format(self, ws, start_row, start_col, end_row, end_col, column_color_count):
        """设置表格格式 - 参考VBA SetTableFormat函数"""
        self.styling_service.set_table_format(ws, start_row, start_col, end_row, end_col, column_color_count)
        
    def _set_stat_column_format(self, worksheet, title_row, start_col, end_row, end_col):
        """设置统计数据背景格式"""
        self.styling_service.set_stat_column_format(worksheet, title_row, start_col, end_row, end_col)
        
    def _set_environment_column_format(self, worksheet, title_row, start_col, end_row, end_col):
        """设置日期环境记录格式"""
        try:
            # 预先创建样式对象
            yellow_fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
            bold_font = Font(name='Arial', bold=True, size=9)
            
            # 构建范围字符串
            start_col_letter = get_column_letter(start_col)
            end_col_letter = get_column_letter(end_col)
            range_str = f"{start_col_letter}{title_row}:{end_col_letter}{end_row}"
            
            # 为整个范围应用样式
            for row in worksheet[range_str]:
                for cell in row:
                    cell.fill = yellow_fill
                    cell.font = bold_font
        except Exception as e:
            logger.error(f"设置环境记录背景格式时出错: {e}", exc_info=True)