import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.matrix.model.matrix_data import MatrixData

def test_column_operations():
    print("测试MatrixData模型的列操作修改...")
    
    # 创建MatrixData实例
    matrix_data = MatrixData()
    
    print(f"初始列数: {matrix_data.column_count}")
    print(f"初始表头: {matrix_data.headers}")
    print(f"初始行数: {len(matrix_data.rows)}")
    
    # 测试添加列（不提供列名）
    print("\n1. 测试添加列（不提供列名）:")
    matrix_data.add_column()  # 应该在末尾添加一个新列，标签为I
    print(f"添加列后表头: {matrix_data.headers}")
    
    # 测试在指定位置插入列
    print("\n2. 测试在指定位置插入列:")
    matrix_data.add_column(position=2)  # 在位置2插入新列
    print(f"插入列后表头: {matrix_data.headers}")
    
    # 测试移动列
    print("\n3. 测试移动列:")
    # 移动第2列到第5列位置
    result = matrix_data.move_column(2, 5)
    print(f"移动列结果: {result}")
    print(f"移动列后表头: {matrix_data.headers}")
    
    # 测试删除列
    print("\n4. 测试删除列:")
    result = matrix_data.remove_column(5)
    print(f"删除列结果: {result}")
    print(f"删除列后表头: {matrix_data.headers}")
    
    # 测试移动前5列
    print("\n5. 测试移动前5列:")
    # 尝试移动第1列到第2列位置
    result = matrix_data.move_column(1, 2)
    print(f"移动前5列结果: {result}")
    print(f"移动前5列后表头: {matrix_data.headers}")
    
    # 测试删除前5列之一
    print("\n6. 测试删除前5列之一:")
    result = matrix_data.remove_column(0)
    print(f"删除前5列结果: {result}")
    print(f"删除前5列后表头: {matrix_data.headers}")
    
    print(f"最终表头: {matrix_data.headers}")
    
    # 额外测试：添加多列
    print("\n7. 测试添加多列:")
    matrix_data.add_column()
    matrix_data.add_column()
    print(f"添加多列后表头: {matrix_data.headers}")

if __name__ == "__main__":
    test_column_operations()