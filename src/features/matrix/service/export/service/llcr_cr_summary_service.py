from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from src.core.logger import logger


class LLCRCRSpecSummaryService:
    """LLCR/CR摘要生成服务 - 专门处理Excel摘要工作表的生成"""
    
    def __init__(self, test_type):
        self.test_type = test_type
        
    def generate_summary_sheet(self, file_path):
        """
        生成Summary工作表
        """
        try:
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
                PatternFill(start_color="FFE4B5", end_color="FFE4B5", fill_type="solid")  # 稍深黄
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