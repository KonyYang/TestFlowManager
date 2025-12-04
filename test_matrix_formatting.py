import sys
import os
from openpyxl import Workbook

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.matrix.service.export.service.excel_formatting_service import ExcelFormattingService

def test_matrix_formatting():
    """测试Matrix个性化格式化服务"""
    print("开始测试Matrix个性化格式化服务...")
    
    # 创建一个工作簿和工作表进行测试
    wb = Workbook()
    ws = wb.active
    
    # 添加一些测试数据（模拟Matrix表格）
    test_data = [
        ["Test Item", "PARA", "Test Method", "Condition", "Requirement", "1", "Notes"],
        ["Visual Examination", "", "EIA-364-18B", "10x min magnification", "No detrimental condition", "1", ""],
        ["Sample size", "", "", "", "", "5", ""],
        ["Time", "", "", "", "", "", ""],
        ["Fee", "", "", "", "", "", ""]
    ]
    
    # 写入测试数据
    for row_idx, row_data in enumerate(test_data, 1):
        for col_idx, cell_value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=cell_value)
    
    print("原始数据已写入工作表")
    
    # 创建格式化服务实例
    formatter = ExcelFormattingService()
    
    # 应用Matrix个性化格式化
    print("开始应用Matrix个性化格式化...")
    # 定义Matrix表格的列宽设置
    matrix_column_widths = {
        1: 20,  # 第1列（Test Item）要宽些
        2: 10,  # 第2列（PARA）要窄些
        4: 20,  # 第4列（Condition）要宽些
        5: 20   # 第5列（Requirement）要宽些
    }
    
    # 使用自定义列宽格式化工作表
    formatter.format_worksheet_with_custom_widths(ws, matrix_column_widths)
    
    # 为首行和首列应用灰色背景
    formatter.apply_background_fill(ws, rows=[1], cols=[1])
    
    # 保存文件
    output_path = "test_matrix_formatted_output.xlsx"
    wb.save(output_path)
    print(f"格式化后的Matrix Excel文件已保存到: {output_path}")
    print("测试完成!")

if __name__ == "__main__":
    test_matrix_formatting()