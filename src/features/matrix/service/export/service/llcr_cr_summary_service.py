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
            data_sheet_names = []  # 存储所有数据工作表名称
            for sheet_name in wb.sheetnames:
                if sheet_name != 'Summary':
                    data_sheet_names.append(sheet_name)
                    if first_sheet_name is None:
                        first_sheet_name = sheet_name
            
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

            # 提取步骤信息（从第10行开始）
            steps_data = []
            
            row_idx = 10
            while row_idx <= source_ws.max_row:
                # 获取Group和Step信息
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
            # 计算需要的列数：2（Test Step）+ 4 * 工作表数量
            total_columns = 2 + 4 * len(data_sheet_names)
            
            # 为每个工作表创建表头
            for i, sheet_name in enumerate(data_sheet_names):
                start_col = 3 + i * 4  # 从第3列开始，每组4列
                end_col = start_col + 3
                
                summary_ws.cell(row=1, column=start_col).value = sheet_name
                summary_ws.merge_cells(start_row=1, start_column=start_col, end_row=1, end_column=end_col)
                
                # 第二行填写统计标题
                for j, stat_name in enumerate(stat_headers):
                    summary_ws.cell(row=2, column=start_col + j).value = stat_name

            # 合并A1到B2区域并设置值为"Test Step"
            summary_ws.merge_cells(start_row=1, start_column=1, end_row=2, end_column=2)
            summary_ws.cell(row=1, column=1).value = "Test Step"
            
            # 设置表头格式
            header_font = Font(name='Arial', size=9, bold=True)
            header_fill = PatternFill(start_color="DCDCDC", end_color="DCDCDC", fill_type="solid")
            center_alignment = Alignment(horizontal='center', vertical='center')

            # 设置表头样式
            for col in range(1, total_columns + 1):
                for row in range(1, 3):
                    cell = summary_ws.cell(row=row, column=col)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center_alignment

            # 填充数据，只使用一种浅黄色背景色
            fill_color = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")  # 淡黄色

            # 数据行字体样式（与表头统一）
            data_font = Font(name='Arial', size=9)
            max_font = Font(name='Arial', size=9, bold=True)  # Max列使用粗体

            # 遍历每个步骤填充数据
            for idx, step_info in enumerate(steps_data):
                row_idx = idx + 3  # 从第3行开始填数据
                group = step_info['group']
                step = step_info['step']
                source_row = step_info['row']
                
                # 填写Group信息（第一列）
                group_cell = summary_ws.cell(row=row_idx, column=1)
                group_cell.value = group
                # 根据交替规则填充背景色（第一个Group不填充，第二个填充，第三个不填充，第四个填充，以此类推）
                group_cell.alignment = center_alignment
                group_cell.font = data_font  # 使用数据行字体样式

                logger.info(f"在第 {row_idx} 行填写 Group: '{group}'")

                # 填写Test Step信息（第二列）
                step_cell = summary_ws.cell(row=row_idx, column=2)
                step_cell.value = step
                step_cell.alignment = center_alignment
                step_cell.font = data_font  # 使用数据行字体样式

                # 为每个工作表填写统计数据引用公式
                for sheet_idx, sheet_name in enumerate(data_sheet_names):
                    start_col = 3 + sheet_idx * 4  # 计算该工作表统计数据的起始列
                    
                    sheet_data = all_sheet_data[sheet_name]['data']
                    
                    # 填写统计数据引用公式
                    for i, stat_name in enumerate(stat_headers):
                        col_idx = start_col + i
                        
                        # 检查该工作表是否有对应的统计数据
                        if source_row in sheet_data and stat_name in sheet_data[source_row]:
                            stat_cell_ref = sheet_data[source_row][stat_name]
                            formula = f"='{sheet_name}'!{stat_cell_ref}"
                            
                            stat_cell = summary_ws.cell(row=row_idx, column=col_idx)
                            stat_cell.value = formula
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
                            stat_cell.alignment = center_alignment
                            stat_cell.font = data_font

            # 记录最后有效行的位置
            last_valid_row = len(steps_data) + 2
            logger.info(f"最后有效行位置: {last_valid_row}")

            # 收集所有包含Group的行号
            group_rows = []
            for row_idx in range(3, last_valid_row + 1):
                group_cell = summary_ws.cell(row=row_idx, column=1)
                if group_cell.value:
                    group_rows.append((row_idx, group_cell.value))
            
            logger.info(f"找到包含Group的行: {group_rows}")

            # 根据Group在Summary表中的实际分布情况进行合并，并按交替规则填充背景色
            for i in range(len(group_rows)):
                current_row, current_group = group_rows[i]
                
                # 确定合并的结束行
                if i < len(group_rows) - 1:
                    # 如果不是最后一个Group，合并到下一个Group的前一行
                    end_row = group_rows[i + 1][0] - 1
                else:
                    # 如果是最后一个Group，合并到最后一行
                    end_row = last_valid_row
                
                # 只有当需要合并多行时才执行合并操作
                if end_row >= current_row:
                    logger.info(f"合并单元格，从第 {current_row} 行到第 {end_row} 行，Group: '{current_group}'")
                    summary_ws.merge_cells(start_row=current_row, start_column=1, 
                                         end_row=end_row, end_column=1)
                    
                    # 按交替规则填充背景色（第一个Group不填充，第二个填充，第三个不填充，第四个填充，以此类推）
                    if i % 2 == 1:  # 偶数索引（0,2,4...）不填充，奇数索引（1,3,5...）填充
                        for row in range(current_row, end_row + 1):
                            # 填充Group列（第1列）
                            group_cell = summary_ws.cell(row=row, column=1)
                            group_cell.fill = fill_color
                            
                            # 填充Test Step列（第2列）
                            step_cell = summary_ws.cell(row=row, column=2)
                            step_cell.fill = fill_color
                            
                            # 填充统计数据列（从第3列开始的所有列）
                            for col in range(3, total_columns + 1):
                                stat_cell = summary_ws.cell(row=row, column=col)
                                stat_cell.fill = fill_color

            # 自动调整列宽
            for col_idx in range(1, total_columns + 1):
                summary_ws.column_dimensions[get_column_letter(col_idx)].width = 20

            # 保存工作簿
            wb.save(file_path)
            logger.info(f"Summary工作表已成功生成并保存到: {file_path}")

        except Exception as e:
            logger.error(f"生成Summary工作表时出错: {e}", exc_info=True)