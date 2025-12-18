from src.features.matrix.service.export.service.base_export_service import BaseExportService
from src.features.matrix.service.export.service.excel_formatting_service import ExcelFormattingService
from src.features.matrix.service.export.service.llcr_cr_table_structure_service import LLCRCRTableStructureService
from src.features.matrix.service.export.service.llcr_cr_formula_service import LLCRCRFormulaService
from src.features.matrix.service.export.service.llcr_cr_styling_service import LLCRCRStylingService
from src.features.matrix.service.export.service.llcr_cr_summary_service import LLCRCRSpecSummaryService
from openpyxl import Workbook
from src.core.logger import logger

class LLCRCRExportService(BaseExportService):
    """LLCR/CR导出服务"""

    def __init__(self, data_model):
        super().__init__(data_model)
        self.formatting_service = ExcelFormattingService()
        self.table_structure_service = LLCRCRTableStructureService(self.formatting_service)
        self.table_structure_service.export_service = self  # 添加反向引用
        self.formula_service = LLCRCRFormulaService()
        self.styling_service = LLCRCRStylingService()
        self.summary_service = None  # 摘要服务将在导出时初始化
        self.test_type = None  # 用于标识当前是LLCR还是CR导出
        self.matrix_data = None  # Matrix数据结构实例
        self.total_row_offset = 0  # 总偏移量
        self.is_first_group = True  # 是否为第一个组
        self.dl_number = None  # 添加DL编号属性

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
            # 初始化摘要服务
            self.summary_service = LLCRCRSpecSummaryService(self.test_type)

            # 创建工作簿
            wb = Workbook()
            logger.debug("创建工作簿成功")

            # 统一处理逻辑：无论单个工作表还是多个工作表，都使用统一的处理流程
            # 如果没有提供test_category_dict，则构建一个统一格式的test_category_dict
            if not test_category_dict or not isinstance(test_category_dict, dict):
                # 如果没有提供测试点位数组，则从数据模型中提取
                if point_array is None:
                    point_array = self._extract_point_array()
                    logger.debug(f"从数据模型提取点位数组: {point_array}")
                
                # 构建统一的test_category_dict格式，即使是简单的单点位情况也变成字典形式
                test_category_dict = {"Sheet1": point_array}
                logger.debug(f"构建默认test_category_dict: {test_category_dict}")

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
                    # for group_name in self.matrix_data.get_all_groups():
                        # steps = self.matrix_data.get_group_steps(group_name)
                        # sample_size = self.matrix_data.get_group_sample_size(group_name)
                        # logger.debug(f"组别 {group_name} - 步骤数: {len(steps)}, 样本数: {sample_size}")

                    # 使用MatrixDataStructure对象
                    for group_name in self.matrix_data.get_all_groups():
                        # group_sample_size = self.matrix_data.get_group_sample_size(group_name)
                        # 传递sample_count而不是parsed_sample_size
                        self._insert_record_data_table(ws, group_name, points, sample_count, is_delta_r_checked,
                                                       cr_current_value)
                else:
                    # 回退到原有逻辑
                    self._insert_record_data_table(ws, sample_count, point_array, sample_count, is_delta_r_checked,
                                                   cr_current_value)

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

    def _insert_record_data_table(self, ws, sample_count_or_group_name, point_array, sample_count,
                                  is_delta_r_checked=False,
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
            else:
                # 原有的sample_count模式（向后兼容）
                sample_count = sample_count_or_group_name
                step_dict = {"1": "Test Step"}  # 默认步骤
                group_name = "Default"

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
                logger.debug(
                    f"[{group_name}] Delta R已勾选，delta_r_start_col: {delta_r_start_col}, 新stat_start_col: {stat_start_col}")

            record_data_tbl_title_row = 9  # 记录数据表头

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
                # logger.debug(
                #     f"[{group_name}] 步骤 {step_key} 处理中, calculateheader_col: {calculateheader_col}, stat_start_col: {stat_start_col}")

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
            logger.debug(
                f"[{group_name}] 更新总行偏移量: {self.total_row_offset}, 步骤数: {step_count}, 点位数: {len(point_array)}")

            # 更新总列偏移量
            self.total_column_offset += (calculate_end_col - record_start_col + 1)

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
            logger.debug(
                f"设置记录表格格式，范围2: ({record_data_tbl_title_row}, {calculateheader_col}) 到 ({end_row}, {stat_start_col + 6})")
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
        # 调用表结构服务中的新方法
        self.table_structure_service.insert_table_headers(
            ws, headers_cols, record_start_col, record_end_col,
            calculateheader_col, calculate_start_col, calculate_end_col,
            stat_start_col, delta_r_start_col, sample_count,
            is_delta_r_checked, cr_current_value, self.test_type, self.is_first_group
        )

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
        self.table_structure_service.merge_cells_for_step(
            ws, current_row, point_array, stat_start_col, calculateheader_col
        )

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

    def _insert_test_info_table(self, ws):
        """插入测试信息表格"""
        # 如果有DL编号，使用DL编号作为target_folder_name，否则使用默认值
        target_folder_name = self.dl_number if self.dl_number else "Default Folder"
        self.table_structure_service.insert_test_info_table(ws, target_folder_name)

    def _generate_summary_sheet_internal(self, file_path):
        """
        内部方法：在导出Excel文件后自动生成Summary工作表
        """
        # 调用摘要服务生成Summary工作表
        self.summary_service.generate_summary_sheet(file_path)
