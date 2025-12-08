#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本，用于将TestFlowManager项目打包成Windows可执行文件
支持在其他Windows系统上独立运行
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_dist_structure():
    """创建dist目录结构并复制必要文件"""
    project_root = Path.cwd()
    dist_dir = project_root / "dist"
    
    # 创建必要的目录
    dirs_to_create = [
        dist_dir / "config",
        dist_dir / "Template",
        dist_dir / "Projects",
        dist_dir / "Temp",
        dist_dir / "Backup",
        dist_dir / "logs"
    ]
    
    for directory in dirs_to_create:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {directory}")


def copy_required_files():
    """复制必需的配置和资源文件到dist目录"""
    project_root = Path.cwd()
    dist_dir = project_root / "dist"
    
    # 复制配置文件
    config_src = project_root / "src" / "app" / "config"
    if config_src.exists():
        # 复制到 dist/config
        shutil.copytree(config_src, dist_dir / "config", dirs_exist_ok=True)
        print("复制配置文件到 dist/config")
    
    # 复制模板文件夹
    # 首先尝试从D:\Template复制
    external_template_src = Path("D:/Template")
    dist_template_dir = dist_dir / "Template"
    
    if external_template_src.exists():
        # 从D:\Template复制
        shutil.copytree(external_template_src, dist_template_dir, dirs_exist_ok=True)
        print(f"从 {external_template_src} 复制模板文件到 {dist_template_dir}")
    else:
        # 如果D:\Template不存在，则尝试从项目中的Template目录复制
        project_template_src = project_root / "Template"
        if project_template_src.exists():
            shutil.copytree(project_template_src, dist_template_dir, dirs_exist_ok=True)
            print(f"从项目 {project_template_src} 复制模板文件到 {dist_template_dir}")
        else:
            print("未找到模板文件目录，创建空的Template目录")
            dist_template_dir.mkdir(exist_ok=True)
    
    # 创建README.txt文件
    version = get_version()
    readme_content = f'''TestFlowManager 使用说明
========================

这是一个独立的Windows应用程序，可以直接运行而无需安装Python。

目录结构说明:
- TestFlowManager.exe: 主程序文件
- config/: 配置文件目录
- Template/: 模板文件目录
- Projects/: 项目文件目录
- Temp/: 临时文件目录
- Backup/: 备份文件目录
- logs/: 日志文件目录

使用方法:
1. 首先，将整个目录结构移动到 D:\\TestFlowManager 路径下
2. 根据实际环境修改 D:\\TestFlowManager\\config\\paths.ini 文件中的配置项：
   - 修改实际路径配置（如ltr_file等）
   - 更新密码配置（如ltr_password）
   - 根据使用者不同调整默认值配置（如project_leader）
3. 双击 TestFlowManager.exe 即可运行程序

注意事项:
1. 请勿删除或移动此目录中的任何文件，否则可能导致程序无法正常运行。
2. 程序会在logs目录中生成日志文件，可用于问题排查。
3. 如需重新配置，请修改config目录中的配置文件。
4. 如果遇到路径相关的问题，请检查paths.ini文件中的配置是否正确。
5. 确保程序运行时有足够的权限访问所有需要的目录和文件。

版本信息:
- 当前版本: {version}
- 发布日期: 2025-12-03

技术支持:
如有任何问题，请联系技术支持团队：Even.Yang@fci.com
'''

    readme_path = dist_dir / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("创建 README.txt 文件")
    
    # 创建启动批处理文件
    bat_content = """@echo off
cd /d %~dp0
TestFlowManager.exe
pause
"""
    
    bat_path = dist_dir / "start.bat"
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print("创建启动批处理文件 start.bat")


def build_executable():
    """使用PyInstaller构建可执行文件"""
    print("开始构建可执行文件...")
    
    try:
        # 使用PyInstaller构建
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "TestFlowManager.spec"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("可执行文件构建成功!")
            print(result.stdout)
            # 重命名生成的exe文件以包含版本号
            version = get_version()
            dist_dir = Path.cwd() / "dist"
            old_exe = dist_dir / "TestFlowManager.exe"
            new_exe = dist_dir / f"TestFlowManager_v{version}.exe"
            
            if old_exe.exists():
                # 如果新文件已存在，先删除它
                if new_exe.exists():
                    new_exe.unlink()
                    print(f"已删除已存在的文件: {new_exe.name}")
                
                old_exe.rename(new_exe)
                print(f"已将可执行文件重命名为: TestFlowManager_v{version}.exe")
            
            return True
        else:
            print("构建过程中出现错误:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"构建可执行文件时发生异常: {e}")
        return False


# 从version.txt文件读取版本号
def get_version():
    """
    从version.txt文件读取版本号
    """
    version_file = Path.cwd() / "version.txt"
    if version_file.exists():
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "1.0.0"  # 默认版本号


def main():
    """主函数"""
    print("TestFlowManager 可执行文件构建工具")
    print("=" * 50)
    
    # 检查当前目录
    project_root = Path.cwd()
    print(f"项目根目录: {project_root}")
    
    # 检查必要的文件是否存在
    required_files = ["TestFlowManager.spec", "src/app/application.py"]
    missing_files = [f for f in required_files if not (project_root / f).exists()]
    
    if missing_files:
        print(f"错误: 缺少必要的文件: {missing_files}")
        return False
    
    # 检查图标文件是否存在
    icon_path = project_root / "src" / "app" / "resources" / "icons" / "app_icon.ico"
    if not icon_path.exists():
        print(f"警告: 图标文件不存在: {icon_path}")
    else:
        print(f"找到图标文件: {icon_path}")
    
    # 创建dist目录结构
    create_dist_structure()
    
    # 复制必需文件
    copy_required_files()
    
    # 构建可执行文件
    if not build_executable():
        print("构建失败!")
        return False
    
    print("\n构建完成!")
    print("可执行文件及相关文件已生成到 dist 目录中")
    print("您可以将整个 dist 目录复制到其他Windows系统上直接运行")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

