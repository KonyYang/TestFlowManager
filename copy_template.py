"""
独立的模板文件复制脚本
将指定的Word模板文件复制到目标位置
"""

import os
import shutil


def copy_template_file():
    """
    复制模板文件到指定的目标位置
    """
    # 源模板文件路径
    source_path = r"D:\Template\FDQF-E-036 Test Record Template_241104.docx"
    
    # 目标文件路径
    target_path = r"D:\outfile\testrecord0.docx"
    
    # 确保目标目录存在
    target_dir = os.path.dirname(target_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"已创建目标目录: {target_dir}")
    
    try:
        # 复制文件
        shutil.copy2(source_path, target_path)
        print(f"成功复制模板文件:")
        print(f"  源文件: {source_path}")
        print(f"  目标文件: {target_path}")
        return True
    except FileNotFoundError:
        print(f"错误: 找不到源文件 {source_path}")
        return False
    except PermissionError:
        print(f"错误: 没有权限访问源文件或目标位置")
        return False
    except Exception as e:
        print(f"复制文件时发生错误: {e}")
        return False


if __name__ == "__main__":
    print("开始复制模板文件...")
    success = copy_template_file()
    if success:
        print("模板文件复制完成!")
    else:
        print("模板文件复制失败!")