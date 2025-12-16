from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font, PatternFill
from src.core.logger import logger


class LLCRCRTableStructureService:
    """LLCR/CR表格结构服务 - 专门处理各种表格结构创建"""
    
    def __init__(self, formatting_service):
        self.formatting_service = formatting_service
        
    def insert_bulk_resistance_table(self, ws, test_type, cr_current_value):
        """插入体积电阻表格"""
        bulk_tbl_start_row = 1  # 体积电阻起始行

        logger.debug(
            f"insert_bulk_resistance_table called with test_type: {test_type}, cr_current_value: {cr_current_value}")

        # 体积电阻表头
        if test_type == "CR":
            logger.debug("Inserting CR bulk resistance table header")
            ws.cell(row=bulk_tbl_start_row, column=1).value = "unit:mV"
            ws.cell(row=bulk_tbl_start_row, column=2).value = "Voltage"
            ws.cell(row=bulk_tbl_start_row + 5, column=1).value = "Current(Unit:A)"
            ws.cell(row=bulk_tbl_start_row + 5, column=2).value = cr_current_value
            # 设置CR电流值单元格格式为一位小数
            ws.cell(row=bulk_tbl_start_row + 5, column=2).number_format = "0.0"
        else:
            logger.debug("Inserting LLCR bulk resistance table header")
            ws.cell(row=bulk_tbl_start_row, column=1).value = "unit:mΩ"
            ws.cell(row=bulk_tbl_start_row, column=2).value = "Resistance"

        # 体积电阻列
        bulk_labels = ["bulk1", "bulk2", "bulk3", "Avg"]
        for i, label in enumerate(bulk_labels):
            ws.cell(row=bulk_tbl_start_row + 1 + i, column=1).value = label
            ws.cell(row=bulk_tbl_start_row + 1 + i, column=2).value = 0 if i < 3 else None

        if test_type == "CR":
            logger.debug("Setting CR number format")
            
            # 设置数据范围的数字格式为三位小数
            for row in range(bulk_tbl_start_row + 1, bulk_tbl_start_row + 5):
                ws.cell(row=row, column=2).number_format = "0.000"
        else:
            logger.debug("Setting LLCR number format")
            # 设置数据范围的数字格式为一位小数
            for row in range(bulk_tbl_start_row + 1, bulk_tbl_start_row + 5):
                ws.cell(row=row, column=2).number_format = "0.0"

        # 插入统计公式
        data_range = f"B{bulk_tbl_start_row + 1}:B{bulk_tbl_start_row + 3}"
        ws.cell(row=bulk_tbl_start_row + 4, column=2).value = f"=AVERAGE({data_range})"
        logger.debug(f"Inserted formula: =AVERAGE({data_range})")

        # 设置体积电阻表格格式
        self.formatting_service.format_range(ws, bulk_tbl_start_row, 1, bulk_tbl_start_row + 5, 2)
        
        # 添加字体和背景色设置
        # 设置字体为Arial，大小为9
        font = Font(name='Arial', size=9)

        # 应用字体和背景色到整个表格区域
        for row in range(bulk_tbl_start_row, bulk_tbl_start_row + 6):
            for col in range(1, 3):
                cell = ws.cell(row=row, column=col)
                cell.font = font

        # 根据附图要求，设置首行和首列的特殊样式
        # 设置首行（表头行）为粗体字并添加灰色背景色
        header_font = Font(name='Arial', size=9, bold=True)
        header_fill = PatternFill(start_color="DCDCDC", end_color="DCDCDC", fill_type="solid")
        
        # 设置首行样式
        for col in range(1, 3):
            cell = ws.cell(row=bulk_tbl_start_row, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # 设置首列（A列）为粗体字并添加灰色背景色
        for row in range(bulk_tbl_start_row, bulk_tbl_start_row + 6):
            cell = ws.cell(row=row, column=1)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        logger.debug("insert_bulk_resistance_table completed")
        
    def insert_test_info_table(self, ws, target_folder_name="Default Folder"):
        """插入测试信息表格"""
        test_info_start_row = 1  # 测试信息起始行

        # 插入测试信息 - 严格按照VBA代码的逻辑
        ws.cell(row=test_info_start_row, column=4).value = "LTR"
        ws.cell(row=test_info_start_row + 1, column=4).value = "Tested By"
        ws.cell(row=test_info_start_row + 2, column=4).value = "Test Equipment ID"
        ws.cell(row=test_info_start_row + 3, column=4).value = "Test Condition"
        ws.cell(row=test_info_start_row + 4, column=4).value = "Test Requirement"
        ws.cell(row=test_info_start_row, column=6).value = target_folder_name
        ws.cell(row=test_info_start_row + 1, column=6).value = "Even Yang"
        ws.cell(row=test_info_start_row + 2, column=6).value = "DG-Q-0639/0640"
        ws.cell(row=test_info_start_row + 3, column=6).value = "20mV,100mA Max"

        # 注意：VBA代码中还有一行调用 AssignLLCRorCRRequirementFromConfirmSpec 来获取 Test Requirement
        # 这里暂时留空，因为该函数需要额外实现
        ws.cell(row=test_info_start_row + 4, column=6).value = ""  # Test Requirement 暂时留空

        # 合并单元格
        for i in range(0, 5):  # 从第0行（TestInfoStartRow）到第4行（TestInfoStartRow + 4）
            # 合并第4列和第5列
            start_cell = ws.cell(row=test_info_start_row + i, column=4)
            end_cell = ws.cell(row=test_info_start_row + i, column=5)
            ws.merge_cells(start_row=start_cell.row, start_column=start_cell.column,
                           end_row=end_cell.row, end_column=end_cell.column)

            # 合并第6列和第9列
            start_cell = ws.cell(row=test_info_start_row + i, column=6)
            end_cell = ws.cell(row=test_info_start_row + i, column=9)
            ws.merge_cells(start_row=start_cell.row, start_column=start_cell.column,
                           end_row=end_cell.row, end_column=end_cell.column)

        # 设置测试信息表格格式
        self.formatting_service.format_range(ws, test_info_start_row, 4, test_info_start_row + 4, 9)

        # 设置单元格格式
        for row in range(test_info_start_row, test_info_start_row + 5):
            for col in range(4, 10):
                cell = ws.cell(row=row, column=col)
                # 保持Arial字体，只修改对齐方式
                if cell.font:
                    cell.font = Font(name='Arial', bold=cell.font.bold, size=9)
                else:
                    cell.font = Font(name='Arial', size=9)
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

        # 设置日期环境记录背景格式
        self._set_environment_column_format(ws, test_info_start_row, 4, test_info_start_row + 4, 9)
        
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