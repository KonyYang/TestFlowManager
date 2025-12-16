from src.features.matrix.service.export.service.base_export_service import BaseExportService
from src.features.matrix.service.export.service.excel_formatting_service import ExcelFormattingService
from src.features.matrix.service.export.service.llcr_cr_table_structure_service import LLCRCRTableStructureService
from src.features.matrix.service.export.service.llcr_cr_formula_service import LLCRCRFormulaService
from src.features.matrix.service.export.service.llcr_cr_styling_service import LLCRCRStylingService
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
from openpyxl.utils import get_column_letter
from src.core.logger import logger
import re


class LLCRCRExportService(BaseExportService):
    """LLCR/CR导出服务"""

    def __init__(self, data_model):
        super().__init__(data_model)
        self.formatting_service = ExcelFormattingService()
        self.table_structure_service = LLCRCRTableStructureService(self.formatting_service)
        self.formula_service = LLCRCRFormulaService()
        self.styling_service = LLCRCRStylingService()
        self.test_type = None  # 用于标识当前是LLCR还是CR导出
        self.matrix_data = None  # Matrix数据结构实例
        self.total_row_offset = 0  # 总偏移量
        self.is_first_group = True  # 是否为第一个组
        self.initial_test_rows = {}  # 存储每个组的初始测试行 {group_name: row}

    def set_matrix_data(self, matrix_data):
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
                    # 重置状态变量（针对每个工作表）
                    self.total_row_offset = 0
                    self.is_first_group = True
                    self.initial_test_rows = {}
                    
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
                        # 输出一次Matrix数据信息
                        logger.debug(f"Matrix数据信息: test_type={self.test_type}")
                        logger.debug(f"Matrix数据存在，所有组别={self.matrix_data.get_all_groups()}")
                        
                        # 遍历所有组别，输出每个组别的信息
                        for group_name in self.matrix_data.get_all_groups():
                            steps = self.matrix_data.get_group_steps(group_name)
                            sample_size = self.matrix_data.get_group_sample_size(group_name)
                            logger.debug(f"组别 {group_name} - 步骤数: {len(steps)}, 样本数: {sample_size}")
                        
                        # 使用MatrixDataStructure对象
                        for group_name in self.matrix_data.get_all_groups():
                            group_sample_size = self.matrix_data.get_group_sample_size(group_name)
                            parsed_sample_size = self._parse_sample_count(group_sample_size)
                            # 传递sample_count而不是parsed_sample_size
                            self._insert_record_data_table(ws, group_name, points, sample_count, is_delta_r_checked, cr_current_value)
                    else:
                        # 回退到原有逻辑
                        self._insert_record_data_table(ws, sample_count, point_array, sample_count, is_delta_r_checked, cr_current_value)
            else:
                logger.debug("使用默认逻辑创建单一工作表")
                # 重置状态变量
                self.total_row_offset = 0
                self.is_first_group = True
                self.initial_test_rows = {}
                
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
                    # 输出一次Matrix数据信息
                    logger.debug(f"Matrix数据信息: test_type={self.test_type}")
                    logger.debug(f"Matrix数据存在，所有组别={self.matrix_data.get_all_groups()}")
                    
                    # 遍历所有组别，输出每个组别的信息
                    for group_name in self.matrix_data.get_all_groups():
                        steps = self.matrix_data.get_group_steps(group_name)
                        sample_size = self.matrix_data.get_group_sample_size(group_name)
                        logger.debug(f"组别 {group_name} - 步骤数: {len(steps)}, 样本数: {sample_size}")
                    
                    # 使用MatrixDataStructure对象
                    for group_name in self.matrix_data.get_all_groups():
                        group_sample_size = self.matrix_data.get_group_sample_size(group_name)
                        parsed_sample_size = self._parse_sample_count(group_sample_size)
                        # 传递sample_count而不是parsed_sample_size
                        self._insert_record_data_table(ws, group_name, point_array, sample_count, is_delta_r_checked,
                                                     cr_current_value)
                else:
                    # 回退到原有逻辑
                    self._insert_record_data_table(ws, sample_count, point_array, sample_count, is_delta_r_checked, cr_current_value)

            # 保存文件
            logger.debug(f"准备保存工作簿到: {file_path}")
            save_result = self._save_workbook_safely(wb, file_path)
            
            # 如果保存成功，则生成Summary工作表
            if save_result:
                self._generate_summary_sheet_internal(file_path)
            
            return save_result
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

    def _insert_record_data_table(self, ws, sample_count_or_group_name, point_array, sample_count, is_delta_r_checked=False,
                                  cr_current_value=""):
        """插入记录数据表格 - 增强版本，支持Matrix数据结构"""
        try:
            logger.debug(f"开始处理工作表 {ws.title} 的记录数据表格")
            group_name = None
            
            # 判断第一个参数是sample_count还是group_name
            if isinstance(sample_count_or_group_name, str):
                # 新的Matrix数据模式
                group_name = sample_count_or_group_name
                logger.debug(f"处理组: {group_name}, is_first_group: {self.is_first_group}")
                if not self.matrix_data:
                    logger.error("Matrix数据未设置，无法插入记录数据表格")
                    return

                # 定义过滤函数
                def test_type_filter(step):
                    # 如果没有指定测试类型，则包含所有步骤
                    if not self.test_type or self.test_type not in ["LLCR", "CR"]:
                        return True
                    # 只包含与当前测试类型匹配的步骤
                    return step.get("Test", "").upper() == self.test_type.upper()

                # 根据测试类型过滤获取相应的测试数据
                group_data = self.matrix_data.get_test_data_for_export(group_name, test_type_filter)
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
            if self.is_first_group:
                stat_start_col = calculate_end_col + 1  # 第一个组使用相对位置
                self.total_column_offset = 0  # 初始化列偏移量
                # 保存第一个组的统计列起始位置，供后续组使用
                self.first_group_stat_start_col = stat_start_col
                logger.debug(f"[{group_name}] 是第一个组，stat_start_col设置为: {stat_start_col}")
            else:
                # 后续组使用第一个组的统计列起始位置，确保统计列位置一致
                stat_start_col = self.first_group_stat_start_col
                logger.debug(f"[{group_name}] 不是第一个组，stat_start_col复用: {stat_start_col}")

            # 如果勾选了 Delta R，统计列需要延后（仅对LLCR有效）
            delta_r_start_col = None
            if is_delta_r_checked and self.test_type == "LLCR":
                delta_r_start_col = stat_start_col
                stat_start_col = delta_r_start_col + sample_count
                logger.debug(f"[{group_name}] Delta R已勾选，delta_r_start_col: {delta_r_start_col}, 新stat_start_col: {stat_start_col}")

            record_data_tbl_title_row = 9  # 记录数据表头
            total_rows = len(point_array)  # 数据行数

            # 如果是第一个group，插入记录数据表格表头
            if self.is_first_group:
                # logger.debug(f"[{group_name}] 插入表头前 calculateheader_col: {calculateheader_col}")
                self._insert_table_headers(ws, headers_cols, record_start_col, record_end_col,
                                       calculateheader_col, calculate_start_col, calculate_end_col,
                                       stat_start_col, delta_r_start_col, sample_count, is_delta_r_checked)
                self.is_first_group = False
                logger.debug(f"[{group_name}] 已插入表头，设置is_first_group为False")

            # 计算当前表格的起始行
            current_row = 10 + self.total_row_offset
            logger.debug(f"[{group_name}] 当前工作表起始行: {current_row}, 总行偏移量: {self.total_row_offset}")
            logger.debug(f"[{group_name}] 当前工作表起始行: {current_row}, 总行偏移量: {self.total_row_offset}")

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
                self._merge_cells_for_step(ws, current_row, point_array, stat_start_col, calculateheader_col)

                # 更新当前行
                current_row = current_row + len(point_array)

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

            # 保存当前组的行偏移量，用于后续计算
            current_total_row_offset = self.total_row_offset
            self.total_row_offset += step_count * len(point_array)
            logger.debug(f"[{group_name}] 更新总行偏移量: {self.total_row_offset}, 步骤数: {step_count}, 点位数: {len(point_array)}")

            # 更新总列偏移量
            self.total_column_offset += (calculate_end_col - record_start_col + 1)

            # 只有在最后一个组处理完后才设置统计数据背景格式和环境记录格式
            # 获取所有组的数量
            all_groups = []
            if self.matrix_data:
                all_groups = self.matrix_data.get_all_groups()
        
            # 当处理到最后一个组时，设置统计列和环境列的格式
            is_last_group = (group_name == all_groups[-1] if all_groups else True)
        
            end_row = record_data_tbl_title_row + self.total_row_offset


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
        logger.debug(f"插入表头到工作表 {ws.title}, record_data_tbl_title_row={record_data_tbl_title_row}")

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
        # 只在第一个组时插入Delta R表头
        if self.is_first_group and is_delta_r_checked and self.test_type == "LLCR" and delta_r_start_col:
            for i in range(1, sample_count + 1):
                ws.cell(row=record_data_tbl_title_row, column=delta_r_start_col + i - 1).value = f"{i}#ΔR"

        # 填写统计标题和日期环境记录
        # 只在第一个组时插入统计标题和环境记录
        if self.is_first_group:
            stat_headers = ["Min", "Max", "Avg", "Stdev", "Test Date", "Amb Temp(°C)", "Rel. Hum.:%"]
            for i, header in enumerate(stat_headers):
                ws.cell(row=record_data_tbl_title_row, column=stat_start_col + i).value = header

        # 设置表头样式
        self._set_header_style(ws, record_data_tbl_title_row, stat_start_col)
        logger.debug(f"完成表头插入到工作表 {ws.title}")

    def _insert_calculation_formulas(self, ws, current_row, point_array, sample_count,
                                     calculate_start_col, bulk_avg_cell, current_cr_cell):
        """插入计算公式"""
        self.formula_service.insert_calculation_formulas(
            ws, current_row, point_array, sample_count,
            calculate_start_col, bulk_avg_cell, current_cr_cell, self.test_type
        )

    def _handle_delta_r(self, ws, current_row, point_array, sample_count,
                        delta_r_start_col, calculate_start_col, step_description):
        """处理Delta R计算"""
        self.formula_service.handle_delta_r(
            ws, current_row, point_array, sample_count,
            delta_r_start_col, calculate_start_col, step_description,
            self.test_type, self.initial_test_rows, self.total_row_offset
        )

    def _insert_statistics_formulas(self, ws, current_row, point_array, sample_count,
                                    calculate_start_col, calculate_end_col, stat_start_col,
                                    delta_r_start_col, is_delta_r_checked):
        """插入统计公式"""
        self.formula_service.insert_statistics_formulas(
            ws, current_row, point_array, sample_count,
            calculate_start_col, calculate_end_col, stat_start_col,
            delta_r_start_col, is_delta_r_checked, self.test_type
        )

    def _set_number_format(self, ws, current_row, point_array, sample_count,
                           record_start_col, record_end_col, calculate_start_col, stat_start_col):
        """设置数字格式"""
        self.styling_service.set_number_format(
            ws, current_row, point_array, sample_count,
            record_start_col, record_end_col, calculate_start_col, stat_start_col, self.test_type
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
        self.styling_service.set_environment_column_format(worksheet, title_row, start_col, end_row, end_col)
        
    def _set_number_format(self, ws, current_row, point_array, sample_count,
                           record_start_col, record_end_col, calculate_start_col, stat_start_col):
        """设置数字格式"""
        self.styling_service.set_number_format(
            ws, current_row, point_array, sample_count,
            record_start_col, record_end_col, calculate_start_col, stat_start_col, self.test_type
        )

    # 以下辅助方法需要根据实际需求实现
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
        self.table_structure_service.insert_bulk_resistance_table(ws, testType, crCurrentValue)

    def _insert_test_info_table(self, ws, test_info=None):
        """插入测试信息表格 - 使用默认值"""
        # 使用固定的默认值
        targetFolderName = "Default Folder"  # 可以根据需要修改这个默认值
        self.table_structure_service.insert_test_info_table(ws, targetFolderName)

    def _generate_summary_sheet_internal(self, file_path):
        """
        内部方法：在导出Excel文件后自动生成Summary工作表
        """
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
            import os
            
            # 加载工作簿
            wb = load_workbook(file_path)
            
            # 获取第一个工作表（Sheet1）
            if '1' in wb.sheetnames:
                source_ws = wb['1']
            else:
                source_ws = wb.active
            
            # 创建Summary工作表
            if 'Summary' in wb.sheetnames:
                summary_ws = wb['Summary']
            else:
                summary_ws = wb.create_sheet('Summary')
            
            # 解析合并单元格信息
            merged_cells_ranges = source_ws.merged_cells.ranges
            
            # 创建一个映射来存储单元格与其所属合并区域的关系
            cell_to_merged_range = {}
            for merged_range in merged_cells_ranges:
                for row in range(merged_range.min_row, merged_range.max_row + 1):
                    for col in range(merged_range.min_col, merged_range.max_col + 1):
                        cell_to_merged_range[(row, col)] = merged_range
            
            # 查找统计数据列的位置（Min, Max, Avg, Stdev）
            stat_columns = {}
            stat_headers = ['Min', 'Max', 'Avg', 'Stdev']
            
            # 在前5行中查找统计标题
            for row_idx in range(1, 6):
                for col_idx in range(1, source_ws.max_column + 1):
                    cell_value = source_ws.cell(row=row_idx, column=col_idx).value
                    if cell_value in stat_headers:
                        stat_columns[cell_value] = col_idx
            
            # 检查是否找到了所有统计列
            if not all(header in stat_columns for header in stat_headers):
                logger.warning("未能找到所有统计列 (Min, Max, Avg, Stdev)")
                # 尝试另一种方式查找
                for col_idx in range(1, source_ws.max_column + 1):
                    for row_idx in range(1, 6):
                        cell_value = str(source_ws.cell(row=row_idx, column=col_idx).value or '').strip()
                        for header in stat_headers:
                            if header.lower() in cell_value.lower():
                                stat_columns[header] = col_idx
                                break
            
            # 提取Group和Step信息
            groups_and_steps = []
            current_group = None
            
            # 遍历数据行查找Group和Step
            for row_idx in range(10, source_ws.max_row + 1):  # 从第10行开始通常是数据行
                # 检查是否有Group信息（第1列）
                group_cell_value = source_ws.cell(row=row_idx, column=1).value
                if group_cell_value and str(group_cell_value).startswith('Group'):
                    current_group = group_cell_value
                
                # 检查是否有Step信息（第2列）
                step_cell_value = source_ws.cell(row=row_idx, column=2).value
                if step_cell_value and current_group:
                    # 检查这行是否有统计数据（通过检查是否有Min值）
                    min_col = stat_columns.get('Min')
                    if min_col:
                        stat_value = source_ws.cell(row=row_idx, column=min_col).value
                        # 如果这一行有统计数据，则认为这是一个有效的Step行
                        if stat_value is not None:
                            groups_and_steps.append({
                                'group': current_group,
                                'step': step_cell_value,
                                'row': row_idx
                            })
            
            # 去重，保留每个group-step组合的一个实例
            unique_groups_and_steps = []
            seen_combinations = set()
            for item in groups_and_steps:
                combination = (item['group'], item['step'])
                if combination not in seen_combinations:
                    unique_groups_and_steps.append(item)
                    seen_combinations.add(combination)
            
            # 创建Summary表头
            # 第一行
            summary_ws.cell(row=1, column=1).value = "Test Step"
            summary_ws.cell(row=1, column=3).value = "Statistics"
            summary_ws.merge_cells(start_row=1, start_column=3, end_row=1, end_column=6)
            
            # 第二行
            summary_ws.cell(row=2, column=1).value = "Test Step"
            summary_ws.cell(row=2, column=2).value = ""
            summary_ws.cell(row=2, column=3).value = "Min"
            summary_ws.cell(row=2, column=4).value = "Max"
            summary_ws.cell(row=2, column=5).value = "Avg"
            summary_ws.cell(row=2, column=6).value = "Stdev"
            
            # 设置表头格式
            header_font = Font(name='Arial', size=9, bold=True)
            header_fill = PatternFill(start_color="DCDCDC", end_color="DCDCDC", fill_type="solid")
            center_alignment = Alignment(horizontal='center', vertical='center')
            
            # 设置表头样式
            for col in range(1, 7):
                for row in range(1, 3):
                    if row == 1 and col == 2:
                        continue  # 跳过(1,2)位置
                    
                    cell = summary_ws.cell(row=row, column=col)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center_alignment
            
            # 填充数据
            group_colors = [
                PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid"),  # 淡黄色
                PatternFill(start_color="FFE4B5", end_color="FFE4B5", fill_type="solid")   # 稍深黄
            ]
            
            prev_group = None
            color_index = 0
            
            for idx, item in enumerate(unique_groups_and_steps):
                row_idx = idx + 3  # 从第3行开始填数据
                group = item['group']
                step = item['step']
                source_row = item['row']
                
                # 切换颜色
                if group != prev_group:
                    color_index = (color_index + 1) % len(group_colors)
                    prev_group = group
                
                fill_color = group_colors[color_index]
                
                # 填写Step名称
                step_cell = summary_ws.cell(row=row_idx, column=1)
                step_cell.value = step
                step_cell.fill = fill_color
                step_cell.alignment = center_alignment
                
                # 填写统计数据引用公式
                for i, stat_name in enumerate(stat_headers):
                    col_idx = 3 + i  # C, D, E, F列
                    stat_col = stat_columns.get(stat_name)
                    
                    if stat_col:
                        # 创建引用公式
                        formula = f"='1'!{get_column_letter(stat_col)}{source_row}"
                        stat_cell = summary_ws.cell(row=row_idx, column=col_idx)
                        stat_cell.value = formula
                        stat_cell.fill = fill_color
                        stat_cell.alignment = center_alignment
                        
                        # 设置数字格式
                        stat_cell.number_format = "0.000" if self.test_type == "CR" else "0.0"
                    else:
                        # 如果找不到统计列，填入空值
                        stat_cell = summary_ws.cell(row=row_idx, column=col_idx)
                        stat_cell.value = ""
                        stat_cell.fill = fill_color
                        stat_cell.alignment = center_alignment
                
                # 设置空的B列
                empty_cell = summary_ws.cell(row=row_idx, column=2)
                empty_cell.value = ""
                empty_cell.fill = fill_color
            
            # 自动调整列宽
            for col_idx in range(1, 7):
                summary_ws.column_dimensions[get_column_letter(col_idx)].width = 20
            
            # 保存工作簿
            wb.save(file_path)
            logger.info(f"Summary工作表已成功生成并保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"生成Summary工作表时出错: {e}", exc_info=True)
