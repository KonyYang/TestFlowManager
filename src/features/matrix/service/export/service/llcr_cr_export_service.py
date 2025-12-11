from src.features.matrix.service.export.service.base_export_service import BaseExportService
from src.features.matrix.service.export.service.excel_formatting_service import ExcelFormattingService
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
from openpyxl.utils import get_column_letter
from src.core.logger import logger
import re
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure  # 导入您的数据结构

class LLCRCRExportService(BaseExportService):
    """LLCR/CR导出服务"""

    def __init__(self, data_model):
        super().__init__(data_model)
        self.formatting_service = ExcelFormattingService()
        self.test_type = None  # 用于标识当前是LLCR还是CR导出
        self.matrix_data = None  # Matrix数据结构实例
        self.total_row_offset = 0  # 总偏移量
        self.is_first_group = True  # 是否为第一个组
        self.initial_test_rows = {}  # 存储每个组的初始测试行 {group_name: row}

    def set_matrix_data(self, matrix_data: MatrixDataStructure):
        """设置Matrix数据结构"""
        self.matrix_data = matrix_data

    def export_to_excel(self, file_path=None, sample_count=5, point_array=None, is_delta_r_checked=False,
                        test_category_dict=None, cr_current_value=""):
        """导出到Excel的抽象方法实现 - 默认处理LLCR"""
        self.test_type = "LLCR"
        return self._export_to_excel(file_path, sample_count, point_array, is_delta_r_checked, test_category_dict,
                                     cr_current_value)

    def export_llcr_to_excel(self, file_path=None, sample_count=5, point_array=None, is_delta_r_checked=False,
                             test_category_dict=None):
        """导出LLCR到Excel"""
        self.test_type = "LLCR"
        return self._export_to_excel(file_path, sample_count, point_array, is_delta_r_checked, test_category_dict, "")

    def export_cr_to_excel(self, file_path=None, sample_count=5, point_array=None, cr_current_value="",
                           test_category_dict=None):
        """导出CR到Excel"""
        self.test_type = "CR"
        return self._export_to_excel(file_path, sample_count, point_array, False, test_category_dict, cr_current_value)

    def _export_to_excel(self, file_path=None, sample_count=5, point_array=None, is_delta_r_checked=False,
                         test_category_dict=None, cr_current_value=""):
        """导出LLCR/CR到Excel"""
        logger.debug(f"开始导出{self.test_type}到 {file_path}")
        logger.debug(
            f"参数详情: sample_count={sample_count}, point_array={point_array}, is_delta_r_checked={is_delta_r_checked}, test_category_dict={test_category_dict}, cr_current_value={cr_current_value}")
        try:
            # 重置状态变量
            self.total_row_offset = 0
            self.is_first_group = True
            self.initial_test_rows = {}

            # 创建工作簿
            wb = Workbook()
            logger.debug("创建工作簿成功")

            # 如果提供了test_category_dict，按分组创建多个工作表
            if test_category_dict and isinstance(test_category_dict, dict):
                logger.debug(f"使用test_category_dict创建多个工作表: {test_category_dict}")
                # 删除默认工作表
                wb.remove(wb.active)

                # 为每个类别创建一个工作表
                for category_name, points in test_category_dict.items():
                    logger.debug(f"为类别'{category_name}'创建工作表，点位: {points}")
                    # 创建工作表并命名（限制工作表名称长度不超过31个字符）
                    safe_category_name = category_name[:31] if len(category_name) > 31 else category_name
                    ws = wb.create_sheet(safe_category_name)
                    logger.debug(f"工作表'{safe_category_name}'创建成功")

                    # 插入体积电阻表格
                    logger.debug(
                        f"调用_insert_bulk_resistance_table，参数: test_type={self.test_type}, cr_current_value={cr_current_value}")
                    self._insert_bulk_resistance_table(ws, self.test_type, cr_current_value)
                    # 插入测试信息表格
                    self._insert_test_info_table(ws)
                    # 插入记录数据表格 - 使用Matrix数据
                    if self.matrix_data:
                        for group_name in self.matrix_data.get_all_groups():
                            group_sample_size = self.matrix_data.get_group_sample_size(group_name)
                            parsed_sample_size = self._parse_sample_count(group_sample_size)
                            self._insert_record_data_table(ws, group_name, points, is_delta_r_checked, cr_current_value)
                    else:
                        # 回退到原有逻辑
                        self._insert_record_data_table(ws, sample_count, points, is_delta_r_checked, cr_current_value)
            else:
                logger.debug("使用默认逻辑创建单一工作表")
                # 如果没有提供test_category_dict，使用原有的逻辑
                # 如果没有提供测试点位数组，则从数据模型中提取
                if point_array is None:
                    point_array = self._extract_point_array()
                    logger.debug(f"从数据模型提取点位数组: {point_array}")

                # 创建工作表并填充数据
                ws = wb.active
                ws.title = self.test_type if self.test_type else ("LLCR" if not cr_current_value else "CR")
                logger.debug(f"设置工作表标题为: {ws.title}")

                # 插入记录数据表格
                if self.matrix_data:
                    for group_name in self.matrix_data.get_all_groups():
                        group_sample_size = self.matrix_data.get_group_sample_size(group_name)
                        parsed_sample_size = self._parse_sample_count(group_sample_size)
                        self._insert_record_data_table(ws, group_name, point_array, is_delta_r_checked,
                                                       cr_current_value)
                else:
                    self._insert_record_data_table(ws, sample_count, point_array, is_delta_r_checked, cr_current_value)

            # 保存文件
            logger.debug(f"准备保存工作簿到: {file_path}")
            return self._save_workbook_safely(wb, file_path)
        except Exception as e:
            logger.error(f"导出{self.test_type}失败: {e}", exc_info=True)
            return False

    def _parse_sample_count(self, sample_size: str) -> int:
        """解析样本数量"""
        try:
            if isinstance(sample_size, (int, float)):
                return int(sample_size)
            elif isinstance(sample_size, str):
                # 提取数字
                import re
                numbers = re.findall(r'\d+', sample_size)
                if numbers:
                    return int(numbers[0])
            return 1  # 默认值
        except (ValueError, TypeError):
            logger.warning(f"无法解析样本数量: {sample_size}，使用默认值1")
            return 1

    def _insert_record_data_table(self, ws, sample_count_or_group_name, point_array, is_delta_r_checked=False,
                                  cr_current_value=""):
        """插入记录数据表格 - 增强版本，支持Matrix数据结构"""
        try:
            # 判断第一个参数是sample_count还是group_name
            if isinstance(sample_count_or_group_name, str):
                # 新的Matrix数据模式
                group_name = sample_count_or_group_name
                if not self.matrix_data:
                    logger.error("Matrix数据未设置，无法插入记录数据表格")
                    return

                group_data = self.matrix_data.get_test_data_for_export(group_name)
                if not group_data:
                    logger.warning(f"组 {group_name} 没有可用的测试数据")
                    return

                step_dict = group_data["step_dict"]
                sample_count = self._parse_sample_count(group_data["sample_size"])
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
            stat_start_col = calculate_end_col + 1  # 开始统计列

            # 如果勾选了 Delta R，统计列需要延后（仅对LLCR有效）
            delta_r_start_col = None
            if is_delta_r_checked and self.test_type == "LLCR":
                delta_r_start_col = stat_start_col
                stat_start_col = delta_r_start_col + sample_count

            record_data_tbl_title_row = 9  # 记录数据表头
            total_rows = len(point_array)  # 数据行数

            # 如果是第一个group，插入记录数据表格表头
            if self.is_first_group:
                self._insert_table_headers(ws, headers_cols, record_start_col, record_end_col,
                                           calculateheader_col, calculate_start_col, calculate_end_col,
                                           stat_start_col, delta_r_start_col, sample_count, is_delta_r_checked)
                self.is_first_group = False

            # 计算当前表格的起始行
            current_row = 10 + self.total_row_offset

            # 填写步骤
            for step_key, step_description in step_dict.items():
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
                current_cr_cell = "B6" if self.test_type == "CR" and cr_current_value else None

                # 插入计算公式
                self._insert_calculation_formulas(ws, current_row, point_array, sample_count,
                                                  calculate_start_col, bulk_avg_cell, current_cr_cell)

                # 如果勾选了 Delta R，插入 Delta R 并填写公式（仅对LLCR有效）
                if is_delta_r_checked and self.test_type == "LLCR" and delta_r_start_col:
                    self._handle_delta_r(ws, current_row, point_array, sample_count,
                                         delta_r_start_col, calculate_start_col, step_description)

                # 插入统计公式
                self._insert_statistics_formulas(ws, current_row, point_array, sample_count,
                                                 calculate_start_col, calculate_end_col, stat_start_col,
                                                 delta_r_start_col, is_delta_r_checked)

                # 设置数据范围的数字格式
                self._set_number_format(ws, current_row, point_array, sample_count,
                                        record_start_col, record_end_col, calculate_start_col, stat_start_col)

                # 合并单元格
                self._merge_cells_for_step(ws, current_row, point_array, stat_start_col)

                # 更新当前行
                current_row = current_row + len(point_array) + 1

            # 填写第一列组名
            ws.cell(row=10 + self.total_row_offset, column=1).value = f"Group {group_name}"
            if len(point_array) > 0:
                ws.merge_cells(start_row=10 + self.total_row_offset, start_column=1,
                               end_row=current_row - 1, end_column=1)

            ws.cell(row=10 + self.total_row_offset, column=calculateheader_col).value = f"Group {group_name}"
            if len(point_array) > 0:
                ws.merge_cells(start_row=10 + self.total_row_offset, start_column=calculateheader_col,
                               end_row=current_row - 1, end_column=calculateheader_col)

            # 更新总偏移量
            step_count = len(step_dict)
            self.total_row_offset += step_count * (len(point_array) + 1)

            # 设置统计数据背景格式
            end_row = record_data_tbl_title_row + self.total_row_offset
            self._set_stat_column_format(ws, record_data_tbl_title_row, stat_start_col, end_row, stat_start_col + 3)

            # 设置日期环境记录背景格式（如果有环境记录列）
            env_start_col = stat_start_col + 4
            if env_start_col <= stat_start_col + 6:  # 确保不超出范围
                self._set_environment_column_format(ws, record_data_tbl_title_row, env_start_col, end_row,
                                                    env_start_col + 2)

            # 设置记录表格格式
            self._set_table_format(ws, record_data_tbl_title_row, 1, end_row, record_end_col, 2)
            self._set_table_format(ws, record_data_tbl_title_row, calculateheader_col, end_row, stat_start_col + 6, 2)

            logger.debug(f"成功插入组 {group_name} 的记录数据表格，步骤数: {step_count}")

        except Exception as e:
            logger.error(f"插入记录数据表格时出错: {e}", exc_info=True)

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
                              stat_start_col, delta_r_start_col, sample_count, is_delta_r_checked, cr_current_value=""):
        """插入表格表头"""
        record_data_tbl_title_row = 9

        # 填写原始记录组别和步骤列表头
        title_value = f"CR {cr_current_value}A" if self.test_type == "CR" and cr_current_value else self.test_type if self.test_type else "LLCR"
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
        if is_delta_r_checked and self.test_type == "LLCR" and delta_r_start_col:
            for i in range(1, sample_count + 1):
                ws.cell(row=record_data_tbl_title_row, column=delta_r_start_col + i - 1).value = f"{i}#ΔR"

        # 填写统计标题和日期环境记录
        stat_headers = ["Min", "Max", "Avg", "Stdev", "Test Date", "Amb Temp(°C)", "Rel. Hum.:%"]
        for i, header in enumerate(stat_headers):
            ws.cell(row=record_data_tbl_title_row, column=stat_start_col + i).value = header

        # 设置表头样式
        self._set_header_style(ws, record_data_tbl_title_row, stat_start_col)

    def _insert_calculation_formulas(self, ws, current_row, point_array, sample_count,
                                     calculate_start_col, bulk_avg_cell, current_cr_cell):
        """插入计算公式"""
        for j in range(len(point_array)):
            for i in range(1, sample_count + 1):
                col_idx = calculate_start_col + i - 1
                record_col_idx = i + 3  # 原始记录列索引

                if self.test_type == "CR" and current_cr_cell:
                    formula = f'=({get_column_letter(record_col_idx)}{current_row + j} - ${bulk_avg_cell})/${current_cr_cell}'
                else:
                    formula = f'={get_column_letter(record_col_idx)}{current_row + j} - ${bulk_avg_cell}'

                ws.cell(row=current_row + j, column=col_idx).value = formula

    def _handle_delta_r(self, ws, current_row, point_array, sample_count,
                        delta_r_start_col, calculate_start_col, step_description):
        """处理Delta R计算"""
        # 检查是否为初始步骤
        is_initial = "initial" in step_description.lower() and self.test_type.lower() in step_description.lower()

        # 获取组名
        group_cell_value = ws.cell(row=10 + self.total_row_offset, column=1).value
        group_name = group_cell_value.replace("Group ", "") if group_cell_value else "Unknown"

        if is_initial:
            # 初始步骤，Delta R的值等于计算值
            for j in range(len(point_array)):
                for i in range(1, sample_count + 1):
                    calc_col_idx = calculate_start_col + i - 1
                    delta_r_col_idx = delta_r_start_col + i - 1
                    formula = f'={get_column_letter(calc_col_idx)}{current_row + j}'
                    ws.cell(row=current_row + j, column=delta_r_col_idx).value = formula

            # 记录初始测试行
            group_cell_value = ws.cell(row=10 + self.total_row_offset, column=1).value
            group_name = group_cell_value.replace("Group ", "") if group_cell_value else "Unknown"
            self.initial_test_rows[group_name] = current_row

        else:
            # 非初始步骤，需要减去初始值
            group_cell_value = ws.cell(row=10 + self.total_row_offset, column=1).value
            group_name = group_cell_value.replace("Group ", "") if group_cell_value else "Unknown"
            initial_row = self.initial_test_rows.get(group_name)
            if not initial_row:
                logger.warning(f"组 {group_name} 未找到Initial {self.test_type}步骤！")
                return

            for j in range(len(point_array)):
                for i in range(1, sample_count + 1):
                    calc_col_idx = calculate_start_col + i - 1
                    delta_r_col_idx = delta_r_start_col + i - 1
                    initial_col_idx = calculate_start_col + i - 1

                    formula = f'={get_column_letter(calc_col_idx)}{current_row + j} - {get_column_letter(initial_col_idx)}{initial_row + j}'
                    ws.cell(row=current_row + j, column=delta_r_col_idx).value = formula

    def _insert_statistics_formulas(self, ws, current_row, point_array, sample_count,
                                    calculate_start_col, calculate_end_col, stat_start_col,
                                    delta_r_start_col, is_delta_r_checked):
        """插入统计公式"""
        if is_delta_r_checked and self.test_type == "LLCR" and delta_r_start_col:
            data_range = f"{get_column_letter(delta_r_start_col)}{current_row}:{get_column_letter(delta_r_start_col + sample_count - 1)}{current_row + len(point_array) - 1}"
        else:
            data_range = f"{get_column_letter(calculate_start_col)}{current_row}:{get_column_letter(calculate_end_col)}{current_row + len(point_array) - 1}"

        # 插入统计公式
        ws.cell(row=current_row, column=stat_start_col).value = f'=MIN({data_range})'  # Min
        ws.cell(row=current_row, column=stat_start_col + 1).value = f'=MAX({data_range})'  # Max
        ws.cell(row=current_row, column=stat_start_col + 2).value = f'=AVERAGE({data_range})'  # Avg
        ws.cell(row=current_row, column=stat_start_col + 3).value = f'=STDEV({data_range})'  # Stdev

    def _set_number_format(self, ws, current_row, point_array, sample_count,
                           record_start_col, record_end_col, calculate_start_col, stat_start_col):
        """设置数字格式"""
        rows_count = len(point_array)

        # 设置数字格式
        number_format = "0.000" if self.test_type == "CR" else "0.0"

        # 原始记录区域
        if record_start_col and record_end_col:
            record_range = f"{get_column_letter(record_start_col)}{current_row}:{get_column_letter(record_end_col)}{current_row + rows_count - 1}"
            for row in ws[record_range]:
                for cell in row:
                    cell.number_format = number_format

        # 计算区域
        calc_range = f"{get_column_letter(calculate_start_col)}{current_row}:{get_column_letter(stat_start_col + 3)}{current_row + rows_count - 1}"
        for row in ws[calc_range]:
            for cell in row:
                cell.number_format = number_format

    def _merge_cells_for_step(self, ws, current_row, point_array, stat_start_col):
        """合并步骤相关的单元格"""
        rows_count = len(point_array)

        # 合并统计列
        for i in range(7):  # Min到Rel. Hum.:% 共7列
            if stat_start_col + i <= stat_start_col + 6:  # 确保安全范围
                ws.merge_cells(start_row=current_row, start_column=stat_start_col + i,
                               end_row=current_row + rows_count - 1, end_column=stat_start_col + i)
                self._merge_cells_style(ws, current_row, stat_start_col + i, rows_count)

        # 合并步骤描述列
        ws.merge_cells(start_row=current_row, start_column=2,
                       end_row=current_row + rows_count - 1, end_column=2)
        self._merge_cells_style(ws, current_row, 2, rows_count)

        ws.merge_cells(start_row=current_row, start_column=5,  # calculateheader_col + 1
                       end_row=current_row + rows_count - 1, end_column=5)
        self._merge_cells_style(ws, current_row, 5, rows_count)

    # 以下辅助方法需要根据实际需求实现
    def _merge_cells_style(self, ws, start_row, start_col, row_span):
        """设置合并单元格样式"""
        pass

    def _set_header_style(self, ws, title_row, stat_start_col):
        """设置表头样式"""
        pass

    # 保留您原有的其他方法...
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

        logger.debug(
            f"_insert_bulk_resistance_table called with testType: {testType}, crCurrentValue: {crCurrentValue}")

        # 体积电阻表头
        if testType == "CR":
            logger.debug("Inserting CR bulk resistance table header")
            ws.cell(row=BulkTblStartRow, column=1).value = "unit:mV"
            ws.cell(row=BulkTblStartRow, column=2).value = "Voltage"
            ws.cell(row=BulkTblStartRow + 5, column=1).value = "Current(Unit:A)"
            ws.cell(row=BulkTblStartRow + 5, column=2).value = crCurrentValue
        else:
            logger.debug("Inserting LLCR bulk resistance table header")
            ws.cell(row=BulkTblStartRow, column=1).value = "unit:mΩ"
            ws.cell(row=BulkTblStartRow, column=2).value = "Resistance"

        # 体积电阻列
        bulk_labels = ["bulk1", "bulk2", "bulk3", "Avg"]
        for i, label in enumerate(bulk_labels):
            ws.cell(row=BulkTblStartRow + 1 + i, column=1).value = label
            ws.cell(row=BulkTblStartRow + 1 + i, column=2).value = 0 if i < 3 else None

        if testType == "CR":
            logger.debug("Setting CR number format")
            # 设置数据范围的数字格式为三位小数
            for row in range(BulkTblStartRow + 1, BulkTblStartRow + 5):
                ws.cell(row=row, column=2).number_format = "0.000"
        else:
            logger.debug("Setting LLCR number format")
            # 设置数据范围的数字格式为一位小数
            for row in range(BulkTblStartRow + 1, BulkTblStartRow + 5):
                ws.cell(row=row, column=2).number_format = "0.0"

        # 插入统计公式
        data_range = f"B{BulkTblStartRow + 1}:B{BulkTblStartRow + 3}"
        ws.cell(row=BulkTblStartRow + 4, column=2).value = f"=AVERAGE({data_range})"
        logger.debug(f"Inserted formula: =AVERAGE({data_range})")

        # 设置体积电阻表格格式
        self._set_table_format(ws, BulkTblStartRow, 1, BulkTblStartRow + 5, 2, 0)
        logger.debug("_insert_bulk_resistance_table completed")

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
                # 保持Arial字体，只修改对齐方式
                if cell.font:
                    cell.font = Font(name='Arial', bold=cell.font.bold, size=9)
                else:
                    cell.font = Font(name='Arial', size=9)
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

        # 设置日期环境记录背景格式
        self._set_environment_column_format(ws, TestInfoStartRow, 4, TestInfoStartRow + 4, 9)
        
        # 如果有Matrix数据，提取并打印LLCR组别信息
        if self.matrix_data:
            print("开始提取LLCR组别信息...")
            self.matrix_data.print_llcr_groups_info()

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
            last_row = worksheet.max_row
            last_col = stat_start_col + 6  # 包括统计列和环境记录列

            # 定义整个表格区域
            for row in range(title_row, last_row + 1):
                for col in range(1, last_col + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    # 只在没有字体设置的情况下应用默认字体
                    if not cell.font or not cell.font.name:
                        cell.font = font

            # 设置表头行粗体并添加灰色背景
            for col in range(1, last_col + 1):
                cell = worksheet.cell(row=title_row, column=col)
                cell.font = Font(name='Arial', size=9, bold=True)
                cell.fill = gray_fill

            # 设置列宽
            for col in range(1, last_col + 1):
                column_letter = get_column_letter(col)
                if col in [1, 2, calculateheader_col, calculateheader_col + 1, stat_start_col, stat_start_col + 1,
                           stat_start_col + 2, stat_start_col + 3]:
                    worksheet.column_dimensions[column_letter].width = 15
                else:
                    worksheet.column_dimensions[column_letter].width = 10

            # 自动调整行高
            for row in range(title_row, last_row + 1):
                worksheet.row_dimensions[row].height = 20

            logger.debug(f"{self.test_type}格式化应用完成")

        except Exception as e:
            logger.error(f"应用{self.test_type}格式化时出错: {e}", exc_info=True)

    def _set_table_format(self, ws, start_row, start_col, end_row, end_col, column_color_count):
        """设置表格格式 - 参考VBA SetTableFormat函数"""
        # 设置整个范围的字体为 Arial
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell = ws.cell(row=row, column=col)
                # 设置字体为 Arial
                if cell.font is None:
                    cell.font = Font(name='Arial', size=9)
                else:
                    # 创建新的字体对象而不是修改现有对象
                    cell.font = Font(name='Arial', size=9, bold=cell.font.bold, color=cell.font.color)

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
            cell.font = Font(name='Arial', bold=True, size=9)
            cell.fill = header_fill

        # 设置前几列的格式（根据column_color_count参数）
        first_col_fill = PatternFill(start_color="DCDCDC", end_color="DCDCDC", fill_type="solid")  # RGB(220,220,220)
        # 注意：这里start_col + column_color_count可能需要根据实际需求调整
        # VBA中是设置从第start_col列到第start_col + ColumnColorCount列
        for row in range(start_row, end_row + 1):
            for col in range(start_col, min(start_col + column_color_count + 1, end_col + 1)):
                cell = ws.cell(row=row, column=col)
                cell.font = Font(name='Arial', bold=True, size=9)
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
                # 保持Arial字体，只修改加粗属性
                if cell.font:
                    cell.font = Font(name='Arial', bold=True, size=9)
                else:
                    cell.font = Font(name='Arial', bold=True, size=9)
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
                    # 保持Arial字体，只修改背景色和加粗
                    if cell.font:
                        cell.font = Font(name='Arial', bold=True, size=9)
                    else:
                        cell.font = Font(name='Arial', bold=True, size=9)
        except Exception as e:
            logger.error(f"设置环境记录背景格式时出错: {e}", exc_info=True)