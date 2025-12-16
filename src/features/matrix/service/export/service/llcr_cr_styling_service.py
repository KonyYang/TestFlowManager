from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
from openpyxl.utils import get_column_letter
from src.core.logger import logger


class LLCRCRStylingService:
    """LLCR/CR样式服务 - 专门处理Excel样式和格式化"""
    
    def __init__(self):
        pass
        
    def merge_cells_style(self, ws, start_row, start_col, row_span):
        """设置合并单元格样式"""
        # 实现合并单元格的样式设置
        for row in range(start_row, start_row + row_span):
            cell = ws.cell(row=row, column=start_col)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    def set_header_style(self, ws, title_row, stat_start_col):
        """设置表头样式"""
        # 设置表头样式
        header_font = Font(name='Arial', size=9, bold=True)
        header_fill = PatternFill(start_color="DCDCDC", end_color="DCDCDC", fill_type="solid")
        
        # 设置表头行的字体和背景色
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=title_row, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
    def set_table_format(self, ws, start_row, start_col, end_row, end_col, column_color_count):
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
        
    def set_stat_column_format(self, worksheet, title_row, start_col, end_row, end_col):
        """设置统计数据背景格式"""
        try:
            # 预先创建样式对象，避免在循环中重复创建
            blue_fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")
            bold_font = Font(name='Arial', bold=True, size=9)
            normal_font = Font(name='Arial', size=9)
            
            # 为第一列到第四列(Min, Max, Avg, Stdev)设置浅蓝色背景
            for col_offset in range(4):  # 0, 1, 2, 3 (第一列到第四列)
                col_letter = get_column_letter(start_col + col_offset)
                col_range = f"{col_letter}{title_row+1}:{col_letter}{end_row}"
                for row in worksheet[col_range]:
                    for cell in row:
                        cell.fill = blue_fill

            # 为第二列(Max)设置字体加粗
            max_col_letter = get_column_letter(start_col + 1)
            max_range = f"{max_col_letter}{title_row+1}:{max_col_letter}{end_row}"
            for row in worksheet[max_range]:
                for cell in row:
                    cell.font = bold_font
        except Exception as e:
            logger.error(f"设置统计数据背景格式时出错: {e}", exc_info=True)

    def set_environment_column_format(self, worksheet, title_row, start_col, end_row, end_col):
        """设置日期环境记录格式"""
        try:
            # 预先创建样式对象
            yellow_fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
            bold_font = Font(name='Arial', bold=True, size=9)
            
            # 构建范围字符串
            start_col_letter = get_column_letter(start_col)
            end_col_letter = get_column_letter(end_col)
            range_str = f"{start_col_letter}{title_row+1}:{end_col_letter}{end_row}"
            
            # 为整个范围应用样式
            for row in worksheet[range_str]:
                for cell in row:
                    cell.fill = yellow_fill
                    cell.font = bold_font
        except Exception as e:
            logger.error(f"设置环境记录背景格式时出错: {e}", exc_info=True)
            
    def set_number_format(self, ws, current_row, point_array, sample_count,
                           record_start_col, record_end_col, calculate_start_col, stat_start_col, test_type):
        """设置数字格式"""
        rows_count = len(point_array)

        # 设置数字格式
        number_format = "0.000" if test_type == "CR" else "0.0"

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