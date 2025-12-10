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
    
    def export_to_excel(self, file_path, sample_count=5, point_array=None, is_delta_r_checked=False):
        """导出LLCR到Excel"""
        logger.debug(f"开始导出LLCR到 {file_path}")
        try:
            # 如果没有提供测试点位数组，则从数据模型中提取
            if point_array is None:
                point_array = self._extract_point_array()
            
            # 创建工作簿
            wb = Workbook()
            
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
                    ws.cell(row=record_data_tbl_title_row, column=delta_r_start_col + i - 1).value = f"{i}#"
            
            # 填写测试点位数据
            for row_idx, point in enumerate(point_array, 1):
                # 填写测试点位列
                ws.cell(row=record_data_tbl_title_row + row_idx, column=2).value = point
                
                # 填写样品编号列
                for col_idx in range(record_start_col, record_end_col + 1):
                    # 留空，由用户填写
                    pass
                    
                # 填写计算列标题
                if row_idx == 1:  # 只在第一行填写
                    ws.cell(row=record_data_tbl_title_row + row_idx, column=calculateheader_col).value = "Max"
                    ws.cell(row=record_data_tbl_title_row + row_idx, column=calculateheader_col + 1).value = "Min"
                
                # 填写统计列标题
                ws.cell(row=record_data_tbl_title_row + row_idx, column=stat_start_col).value = "Max"
                ws.cell(row=record_data_tbl_title_row + row_idx, column=stat_start_col + 1).value = "Min"
                ws.cell(row=record_data_tbl_title_row + row_idx, column=stat_start_col + 2).value = "Average"
                ws.cell(row=record_data_tbl_title_row + row_idx, column=stat_start_col + 3).value = "Std Dev"
                
            # 应用格式化
            self._apply_formatting(ws, record_data_tbl_title_row, sample_count, len(point_array), 
                                 calculateheader_col, calculate_start_col, stat_start_col, is_delta_r_checked)
                                 
        except Exception as e:
            logger.error(f"插入记录数据表格时出错: {e}", exc_info=True)
    
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
            last_col = stat_start_col + 4  # Max, Min, Average, Std Dev
            
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