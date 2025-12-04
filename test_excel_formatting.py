import sys
import os
from openpyxl import Workbook

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.matrix.service.export.service.excel_formatting_service import ExcelFormattingService

def test_excel_formatting():
    """测试Excel格式化服务"""
    print("开始测试Excel格式化服务...")
    
    # 创建一个工作簿和工作表进行测试
    wb = Workbook()
    ws = wb.active
    
    # 添加一些测试数据
    test_data = [
        ["姓名", "年龄", "描述"],
        ["张三", "25", "这是一个很长的描述文本，用来测试自动换行功能是否正常工作"],
        ["李四", "30", "另一个描述文本，同样很长，用于测试格式化效果"],
        ["王五", "28", "第三个测试用例"]
    ]
    
    # 写入测试数据
    for row_idx, row_data in enumerate(test_data, 1):
        for col_idx, cell_value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=cell_value)
    
    print("原始数据已写入工作表")
    
    # 创建格式化服务实例
    formatter = ExcelFormattingService()
    
    # 应用格式化
    print("开始应用格式化...")
    formatter.format_worksheet(ws)
    
    # 保存文件
    output_path = "test_formatted_output.xlsx"
    wb.save(output_path)
    print(f"格式化后的Excel文件已保存到: {output_path}")
    print("测试完成!")

if __name__ == "__main__":
    test_excel_formatting()