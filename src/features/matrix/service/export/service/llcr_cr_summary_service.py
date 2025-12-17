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
            logger.info(f"开始处理文件: {file_path}")

            # 从第一个工作表提取步骤信息
            first_sheet_name = None
            for sheet_name in wb.sheetnames:
                if sheet_name != 'Summary':
                    first_sheet_name = sheet_name
                    break
            
            if not first_sheet_name:
                logger.warning("未找到任何数据工作表")
                return
                
            source_ws = wb[first_sheet_name]
            logger.info(f"从工作表 {first_sheet_name} 提取步骤信息")

            # 查找统计数据列的位置（Min, Max, Avg, Stdev）
            stat_columns = {}
            stat_headers = ['Min', 'Max', 'Avg', 'Stdev']
            
            # 直接在第9行（标题行）从第4列开始查找统计列
            record_data_tbl_title_row = 9  # 记录数据表头
            for col_idx in range(4, source_ws.max_column + 1):  # 从第4列开始
                cell_value = source_ws.cell(row=record_data_tbl_title_row, column=col_idx).value
                if cell_value in stat_headers:
                    stat_columns[cell_value] = col_idx
            
            logger.info(f"在工作表 {first_sheet_name} 中找到统计列位置: {stat_columns}")

            # 获取合并单元格信息
            merged_cells_ranges = source_ws.merged_cells.ranges
            
            # 创建一个映射来存储行号与其所属合并区域的关系
            row_to_merged_range = {}
            for merged_range in merged_cells_ranges:
                for row in range(merged_range.min_row, merged_range.max_row + 1):
                    # 只关注第2列（步骤列）的合并情况
                    if merged_range.min_col <= 2 <= merged_range.max_col:
                        row_to_merged_range[row] = merged_range

            # 提取步骤信息（从第10行开始）
            steps_data = []
            processed_merged_ranges = set()  # 记录已处理的合并区域
            
            row_idx = 10
            while row_idx <= source_ws.max_row:
                # 检查当前行是否属于某个合并区域
                if row_idx in row_to_merged_range:
                    merged_range = row_to_merged_range[row_idx]
                    
                    # 如果这个合并区域已经处理过了，跳过
                    if merged_range in processed_merged_ranges:
                        row_idx += 1
                        continue
                    
                    # 标记这个合并区域已处理
                    processed_merged_ranges.add(merged_range)
                    
                    # 获取合并区域第一行的数据作为步骤数据
                    first_row = merged_range.min_row
                    group_cell_value = source_ws.cell(row=first_row, column=1).value
                    step_cell_value = source_ws.cell(row=first_row, column=2).value
                    
                    # 为每个统计数据列创建单元格引用（使用合并区域的第一行）
                    stat_cells = {}
                    for stat_name, col_idx in stat_columns.items():
                        cell_ref = f"{get_column_letter(col_idx)}{first_row}"
                        stat_cells[stat_name] = cell_ref
                    
                    # 只有当至少有一个统计列有数据时才处理此行
                    has_stat_data = any(stat_cells.values())
                    if has_stat_data and (group_cell_value or step_cell_value):
                        steps_data.append({
                            'row': first_row,
                            'group': group_cell_value,
                            'step': step_cell_value,
                            'stat_cells': stat_cells
                        })
                    
                    # 跳到合并区域的下一行
                    row_idx = merged_range.max_row + 1
                else:
                    # 处理未合并的行
                    group_cell_value = source_ws.cell(row=row_idx, column=1).value
                    step_cell_value = source_ws.cell(row=row_idx, column=2).value
                    
                    # 为每个统计数据列创建单元格引用
                    stat_cells = {}
                    for stat_name, col_idx in stat_columns.items():
                        cell_ref = f"{get_column_letter(col_idx)}{row_idx}"
                        stat_cells[stat_name] = cell_ref
                    
                    # 只有当至少有一个统计列有数据时才处理此行
                    has_stat_data = any(stat_cells.values())
                    if has_stat_data and (group_cell_value or step_cell_value):
                        steps_data.append({
                            'row': row_idx,
                            'group': group_cell_value,
                            'step': step_cell_value,
                            'stat_cells': stat_cells
                        })
                    
                    row_idx += 1

            logger.info(f"从工作表 {first_sheet_name} 中提取了 {len(steps_data)} 个步骤数据")

            # 收集所有工作表中的统计数据
            all_sheet_data = {}
            for sheet_name in wb.sheetnames:
                if sheet_name == 'Summary':
                    continue
                    
                sheet = wb[sheet_name]
                sheet_stat_columns = {}
                
                # 查找当前工作表的统计数据列位置
                for col_idx in range(4, sheet.max_column + 1):
                    cell_value = sheet.cell(row=9, column=col_idx).value
                    if cell_value in stat_headers:
                        sheet_stat_columns[cell_value] = col_idx
                
                # 为当前工作表的每一行创建统计数据引用
                sheet_data = {}
                for row_idx in range(10, sheet.max_row + 1):
                    stat_cells = {}
                    for stat_name, col_idx in sheet_stat_columns.items():
                        cell_ref = f"{get_column_letter(col_idx)}{row_idx}"
                        stat_cells[stat_name] = cell_ref
                    sheet_data[row_idx] = stat_cells
                    
                all_sheet_data[sheet_name] = {
                    'data': sheet_data,
                    'stat_columns': sheet_stat_columns
                }

            # 创建Summary工作表
            if 'Summary' in wb.sheetnames:
                summary_ws = wb['Summary']
                # 清空现有内容
                for row in summary_ws.iter_rows():
                    for cell in row:
                        cell.value = None
            else:
                summary_ws = wb.create_sheet('Summary')

            # 创建Summary表头
            # 第一行
            summary_ws.cell(row=1, column=1).value = "Group"
            summary_ws.cell(row=1, column=2).value = "Test Step"
            summary_ws.cell(row=1, column=3).value = "Statistics"
            summary_ws.merge_cells(start_row=1, start_column=3, end_row=1, end_column=6)

            # 第二行
            summary_ws.cell(row=2, column=1).value = "Group"
            summary_ws.cell(row=2, column=2).value = "Test Step"
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

            # 数据行字体样式（与表头统一）
            data_font = Font(name='Arial', size=9)
            max_font = Font(name='Arial', size=9, bold=True)  # Max列使用粗体

            # 遍历每个步骤填充数据
            for idx, step_info in enumerate(steps_data):
                row_idx = idx + 3  # 从第3行开始填数据
                group = step_info['group']
                step = step_info['step']
                source_row = step_info['row']
                stat_cells = step_info['stat_cells']
                
                # 切换颜色
                if group != prev_group:
                    color_index = (color_index + 1) % len(group_colors)
                    prev_group = group

                fill_color = group_colors[color_index]

                # 填写Group信息（第一列）
                group_cell = summary_ws.cell(row=row_idx, column=1)
                group_cell.value = group
                group_cell.fill = fill_color
                group_cell.alignment = center_alignment
                group_cell.font = data_font  # 使用数据行字体样式

                # 填写Test Step信息（第二列）
                step_cell = summary_ws.cell(row=row_idx, column=2)
                step_cell.value = step
                step_cell.fill = fill_color
                step_cell.alignment = center_alignment
                step_cell.font = data_font  # 使用数据行字体样式

                # 填写统计数据引用公式（从对应行的每个工作表中获取数据）
                for i, stat_name in enumerate(stat_headers):
                    col_idx = 3 + i  # 从第3列开始填统计数据（C, D, E, F列）
                    
                    # 为每个工作表创建统计值
                    stat_values = []
                    for sheet_name in wb.sheetnames:
                        if sheet_name == 'Summary':
                            continue
                            
                        sheet_data = all_sheet_data[sheet_name]['data']
                        if source_row in sheet_data and stat_name in sheet_data[source_row]:
                            stat_cell_ref = sheet_data[source_row][stat_name]
                            stat_values.append(f"='{sheet_name}'!{stat_cell_ref}")
                    
                    # 如果有统计数据，填写第一个工作表的引用
                    if stat_values:
                        formula = stat_values[0]  # 使用第一个工作表的数据
                        stat_cell = summary_ws.cell(row=row_idx, column=col_idx)
                        stat_cell.value = formula
                        stat_cell.fill = fill_color
                        stat_cell.alignment = center_alignment
                        
                        # Max列使用粗体字，其他列使用普通字体
                        if stat_name == 'Max':
                            stat_cell.font = max_font
                        else:
                            stat_cell.font = data_font

                        # 设置数字格式
                        stat_cell.number_format = "0.000" if self.test_type == "CR" else "0.0"
                    else:
                        # 如果找不到统计单元格引用，填入空值
                        stat_cell = summary_ws.cell(row=row_idx, column=col_idx)
                        stat_cell.value = ""
                        stat_cell.fill = fill_color
                        stat_cell.alignment = center_alignment
                        stat_cell.font = data_font

            # 自动调整列宽
            for col_idx in range(1, 7):
                summary_ws.column_dimensions[get_column_letter(col_idx)].width = 20

            # 保存工作簿
            wb.save(file_path)
            logger.info(f"Summary工作表已成功生成并保存到: {file_path}")

        except Exception as e:
            logger.error(f"生成Summary工作表时出错: {e}", exc_info=True)