from src.features.matrix.model.matrix_data import MatrixData
from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
from src.core.logger import logger
from src.features.matrix.service.export.service.excel_formatting_service import ExcelFormattingService
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
from openpyxl.utils import get_column_letter


class TestStatusTableExportService:
    """Test Status表导出服务 - 生成特定格式的Test Status表"""

    def __init__(self, data_model, ltr_data: LTRApplicationData = None):
        self.data_model = data_model
        self.ltr_data = ltr_data
        # 创建格式化服务实例
        self.formatting_service = ExcelFormattingService()
        # 移除LTR数据的详细日志输出

    def export_test_status_to_excel(self, file_path):
        """将Matrix数据导出为Test Status表格式"""
        logger.debug(f"开始导出Test Status表到 {file_path}")
        try:
            # 创建工作簿
            wb = Workbook()
            ws = wb.active

            # 确定截止行（找到第一列包含"Sample"的行）
            cutoff_row_index = self._find_sample_row_index()
            # 获取处理后的数据（移除指定列）
            processed_headers, processed_rows = self._process_matrix_data(cutoff_row_index)
            
            # 直接写入数据行，不写入表头
            for row_idx, row_data in enumerate(processed_rows):
                for col_idx, cell_value in enumerate(row_data):
                    ws.cell(row=row_idx + 1, column=col_idx + 1, value=cell_value)
            
            # 添加"Estimated completion date in Clarizen"行
            est_date_row = len(processed_rows) + 1
            ws.cell(row=est_date_row, column=1, value="Estimated completion date in Clarizen")
            # 合并该行除第一列外的所有列
            if len(processed_headers) > 1:
                ws.merge_cells(start_row=est_date_row, start_column=2, 
                               end_row=est_date_row, end_column=len(processed_headers))
                if self.ltr_data and self.ltr_data.estimated_completion_date:
                    ws.cell(row=est_date_row, column=2, value=self.ltr_data.estimated_completion_date)
            
            # 添加Status行（在Estimated completion date行之后）
            status_row = est_date_row + 1
            ws.cell(row=status_row, column=1, value="Status")
            
            # 应用格式化
            self._apply_formatting(ws, status_row, len(processed_headers))
            
            # 保存文件
            wb.save(file_path)
            logger.debug(f"Test Status表已成功导出到: {file_path}")
            return True
        except PermissionError:
            # 文件被其他程序占用（如Excel）
            logger.error(f"导出Test Status表失败: 文件被占用，可能已在Excel中打开")
            return False
        except Exception as e:
            logger.error(f"导出Test Status表失败: {e}", exc_info=True)
            return False

    def _find_sample_row_index(self):
        """找到第一列包含'Sample'的行索引"""
        rows = self.data_model.get_rows()
        for row_idx, row_data in enumerate(rows):
            if row_data and len(row_data) > 0 and "Sample" in str(row_data[0]):
                logger.debug(f"在第{row_idx}行找到Sample")
                return row_idx + 1  # 返回Sample行索引+1，包含该行
        # 如果没找到，返回所有行
        logger.debug("未找到Sample行，返回所有行")
        return len(rows)

    def _process_matrix_data(self, cutoff_row_index):
        """处理矩阵数据，移除指定列并将Status列转换为最后一行"""
        # 原始表头
        original_headers = self.data_model.get_headers()[:]
        
        # 处理空表头的情况
        if not original_headers:
            logger.debug("表头为空，返回空结果")
            return [], []
        
        # 确定要移除的列索引 (2,3,4,5列对应索引1,2,3,4，以及最后一列Notes)
        columns_to_remove = {1, 2, 3, 4}
        # 只有当有足够的列时才移除最后一列
        if len(original_headers) > 1:
            columns_to_remove.add(len(original_headers) - 1)
        
        # 处理表头 - 移除指定列
        processed_headers = []
        for idx, header in enumerate(original_headers):
            if idx not in columns_to_remove:
                processed_headers.append(header)
        
        # 处理数据行
        processed_rows = []
        rows = self.data_model.get_rows()
        
        # 直接处理所有行，从第一行开始（索引0）
        start_row_index = 0
        for row_idx, row_data in enumerate(rows[start_row_index:cutoff_row_index], start=start_row_index):
            processed_row = []
            # 确保row_data不为空
            if row_data:
                for col_idx, cell_value in enumerate(row_data):
                    if col_idx not in columns_to_remove:
                        processed_row.append(cell_value)
            processed_rows.append(processed_row)
            
        logger.debug(f"处理完成，最终数据行数: {len(processed_rows)}")
        return processed_headers, processed_rows

    def _apply_formatting(self, worksheet, data_rows, data_cols):
        """应用表格格式化，参照VBA代码实现"""
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
            gray_fill = PatternFill(start_color="C8C8C8", end_color="C8C8C8", fill_type="solid")
            
            # 定义蓝色背景填充
            blue_fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
            
            # 获取实际使用的行列数
            last_row = worksheet.max_row
            last_col = worksheet.max_column
            
            # 定义整个表格区域
            for row in range(1, last_row + 1):
                for col in range(1, last_col + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.font = font
            
            # 设置第一行粗体并添加灰色背景
            for col in range(1, last_col + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = Font(name='Arial', size=9, bold=True)
                cell.fill = gray_fill
            
            # 设置列宽为固定值15
            for col in range(1, last_col + 1):
                column_letter = get_column_letter(col)
                worksheet.column_dimensions[column_letter].width = 15
            
            # 自动调整行高
            for row in range(1, last_row):
                worksheet.row_dimensions[row].height = None  # 让Excel自动调整行高
            
            # 设置最后一行的行高为固定值60
            worksheet.row_dimensions[last_row].height = 60
            
            # 在最后一行的每列（除了第一列）添加"No Start"
            for col in range(2, last_col + 1):
                cell = worksheet.cell(row=last_row, column=col)
                cell.value = "No Start"
            
            # 查找并为包含"SAMPLE"的行及其后续行添加蓝色背景
            for row in range(1, last_row + 1):  # 从第1行开始查找
                cell_value = worksheet.cell(row=row, column=1).value
                if cell_value and "SAMPLE" in str(cell_value).upper():
                    # 为该行及后续所有行添加蓝色背景
                    for bg_row in range(row, last_row + 1):
                        for bg_col in range(1, last_col + 1):
                            worksheet.cell(row=bg_row, column=bg_col).fill = blue_fill
                    break
            
            logger.debug("格式化应用完成")
            
        except Exception as e:
            logger.error(f"应用格式化时出错: {e}", exc_info=True)