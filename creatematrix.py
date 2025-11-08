# creatematrix.py
import os
import sys
from pathlib import Path

def create_matrix_module_structure():
    """创建matrix模块的完整文件架构"""

    # 定义项目根目录
    project_root = Path("D:/PythonProject/TestFlowManager")
    features_dir = project_root / "src" / "features"

    try:
        # 检查项目根目录是否存在
        if not project_root.exists():
            print(f"错误: 项目根目录不存在: {project_root}")
            return False

        # 创建matrix模块主目录
        matrix_dir = features_dir / "matrix"

        # 如果目录已存在，检查是否可以写入
        if matrix_dir.exists():
            try:
                # 尝试在目录中创建测试文件
                test_file = matrix_dir / ".test"
                test_file.touch()
                test_file.unlink()  # 删除测试文件
                print(f"目录已存在且可写: {matrix_dir}")
            except PermissionError:
                print(f"错误: 目录存在但无写入权限: {matrix_dir}")
                return False
        else:
            # 创建新目录
            matrix_dir.mkdir(parents=True, exist_ok=True)
            print(f"创建目录: {matrix_dir}")

        # 创建子目录和__init__.py文件
        sub_dirs = ["model", "view", "controller", "service"]
        for subdir in sub_dirs:
            dir_path = matrix_dir / subdir
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"创建目录: {dir_path}")
                except PermissionError:
                    print(f"错误: 无法创建目录: {dir_path}")
                    return False

            # 确保每个包都有__init__.py文件
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                try:
                    init_file.write_text("# __init__.py\n")
                    print(f"创建文件: {init_file}")
                except PermissionError:
                    print(f"错误: 无法写入文件: {init_file}")
                    return False

        # 创建其他空白文件
        blank_files = [
            matrix_dir / "model" / "matrix_data.py",
            matrix_dir / "view" / "matrix_dialog.py",
            matrix_dir / "controller" / "matrix_controller.py",
            matrix_dir / "service" / "matrix_service.py"
        ]

        for file_path in blank_files:
            try:
                if not file_path.exists():
                    file_path.write_text("// ... 空白文件，等待实现 ...\n")
                    print(f"创建文件: {file_path}")
                else:
                    print(f"文件已存在: {file_path}")
            except PermissionError:
                print(f"错误: 无法写入文件: {file_path}")
                return False

        print("\n✅ 矩阵模块文件架构创建完成！")
        print(f"路径: {matrix_dir}")
        print("包含以下文件:")
        for file_path in blank_files:
            print(f"  {file_path}")

        return True

    except Exception as e:
        print(f"创建过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    create_matrix_module_structure()
