#!/usr/bin/env python3
"""
构建可执行文件脚本
用于将TestFlow Manager打包为Windows可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_dist_structure():
    """创建发布目录结构"""
    print("创建发布目录结构...")
    
    # 获取当前目录
    current_dir = Path(__file__).parent.absolute()
    dist_dir = current_dir / "dist"
    
    # 创建必要的目录
    directories = [
        dist_dir / "config",
        dist_dir / "Template",
        dist_dir / "Projects",
        dist_dir / "Backup",
        dist_dir / "Temp",
        dist_dir / "logs"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {directory}")
    
    # 复制配置文件到dist/config目录
    config_src_dir = current_dir / "src" / "app" / "config"
    config_dst_dir = dist_dir / "config"
    
    config_files = ["settings.json", "paths.ini", "ltr_fields.json"]
    for config_file in config_files:
        src_file = config_src_dir / config_file
        dst_file = config_dst_dir / config_file
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            print(f"复制配置文件: {src_file} -> {dst_file}")
    
    # 复制README文件到dist目录
    readme_src = current_dir / "README.md"
    readme_dst = dist_dir / "README.txt"
    if readme_src.exists():
        shutil.copy2(readme_src, readme_dst)
        print(f"复制README文件: {readme_src} -> {readme_dst}")
    
    print("发布目录结构创建完成!")


def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 获取当前目录
    current_dir = Path(__file__).parent.absolute()
    spec_file = current_dir / "TestFlowManager.spec"
    
    if not spec_file.exists():
        print(f"错误: 找不到spec文件 {spec_file}")
        return False
    
    # 使用PyInstaller构建
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(spec_file),
            "--clean"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=current_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("可执行文件构建成功!")
            print(result.stdout)
            return True
        else:
            print("可执行文件构建失败!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"构建过程中发生错误: {e}")
        return False


def main():
    """主函数"""
    print("TestFlow Manager 可执行文件构建工具")
    print("=" * 50)
    
    # 检查PyInstaller是否已安装
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: 未安装PyInstaller，请先运行 'pip install pyinstaller'")
        return
    
    # 创建发布目录结构
    create_dist_structure()
    
    # 构建可执行文件
    if build_executable():
        print("\n" + "=" * 50)
        print("构建完成!")
        print(f"可执行文件位置: {Path(__file__).parent.absolute() / 'dist' / 'TestFlowManager.exe'}")
        print("您可以将dist目录中的所有文件发送到其他Windows系统上直接运行")
        print("\n注意: 已将日志级别设置为WARNING，以提高运行速度")
    else:
        print("\n" + "=" * 50)
        print("构建失败，请检查错误信息")


if __name__ == "__main__":
    main()