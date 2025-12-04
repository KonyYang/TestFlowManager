import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.matrix.model.matrix_data import MatrixData

def test_matrix_data():
    print("测试MatrixData模型的修改...")
    
    # 创建MatrixData实例
    matrix_data = MatrixData()
    
    print(f"列数: {matrix_data.column_count}")
    print(f"表头: {matrix_data.headers}")
    print(f"行数: {len(matrix_data.rows)}")
    
    # 检查所有表头
    print("\n所有表头:")
    for i in range(len(matrix_data.headers)):
        print(f"  列 {i}: {matrix_data.headers[i]}")
    
    # 检查所有数据行
    for i, row in enumerate(matrix_data.rows):
        print(f"\n第{i+1}行数据: {row}")
    
    # 验证特定条件
    print("\n验证:")
    print(f"是否使用字母标识: {matrix_data.headers == ['A', 'B', 'C', 'D', 'E', 'F', 'G']}")
    print(f"第一行是否包含Test Item等标题: {'Test Item' in matrix_data.rows[0]}")
    print(f"是否包含'1'列数据: {'1' in matrix_data.rows[0]}")
    print(f"是否包含'Remark'列数据: {'Remark' in matrix_data.rows[0]}")
    print(f"是否不包含'2'列数据: {'2' not in matrix_data.rows[0]}")
    print(f"行数是否为5 (包括表头): {len(matrix_data.rows) == 5}")
    print(f"是否已删除第三行空白行: {'Sample size' in matrix_data.rows[2]}")  # 现在第3行应该是Sample size而不是空白行
    
    # 检查每行的列数是否一致
    print("\n每行列数检查:")
    for i, row in enumerate(matrix_data.rows):
        print(f"  第{i+1}行有 {len(row)} 列")

if __name__ == "__main__":
    test_matrix_data()