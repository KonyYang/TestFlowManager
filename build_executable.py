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
    else:
        print("警告: 配置文件目录不存在: ", config_src)
    
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
    
    # 复制资源文件夹（图标等）
    resources_src = project_root / "src" / "app" / "resources"
    dist_resources_dir = dist_dir / "resources"
    if resources_src.exists():
        shutil.copytree(resources_src, dist_resources_dir, dirs_exist_ok=True)
        print(f"复制资源文件到 {dist_resources_dir}")
    else:
        print("警告: 资源文件目录不存在: ", resources_src)
    
    # 复制字体和样式文件（如果有）
    fonts_dirs = [project_root / "fonts", project_root / "styles"]
    for font_dir in fonts_dirs:
        if font_dir.exists():
            dist_font_dir = dist_dir / font_dir.name
            shutil.copytree(font_dir, dist_font_dir, dirs_exist_ok=True)
            print(f"复制{font_dir.name}文件到 {dist_font_dir}")
        else:
            print(f"信息: {font_dir.name}目录不存在，跳过")
    
    # 创建README.txt文件
    version = get_version()
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    readme_content = f'''TestFlowManager 使用说明
========================

这是一个独立的Windows应用程序，可以直接运行而无需安装Python。

目录结构说明:
- TestFlowManager_v{{version}}_{{timestamp}}.exe: 主程序文件（带版本号和时闰戳）
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
3. 双击 TestFlowManager_v*.exe 即可运行程序

注意事项:
1. 请勿删除或移动此目录中的任何文件，否则可能导致程序无法正常运行。
2. 程序会在logs目录中生成日志文件，可用于问题排查。
3. 如需重新配置，请修改config目录中的配置文件。
4. 如果遇到路径相关的问题，请检查paths.ini文件中的配置是否正确。
5. 确保程序运行时有足够的权限访问所有需要的目录和文件。

版本信息:
- 当前版本: {version}
- 发布日期: {current_date}

技术支持:
如有任何问题，请联系技术支持团队：Even.Yang@fci.com
'''

    readme_path = dist_dir / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("创建 README.txt 文件")
    
    # 创建启动批处理文件（自动查找最新的 EXE 文件）
    bat_content = """@echo off
cd /d %~dp0

REM 自动查找最新的 TestFlowManager EXE 文件
for /f "delims=" %%i in ('dir TestFlowManager_v*.exe /b /o-d 2^>nul') do (
    set "EXE_FILE=%%i"
    goto :run
)

REM 如果没有找到带版本号的 EXE，尝试默认的
if not defined EXE_FILE (
    if exist TestFlowManager.exe (
        set "EXE_FILE=TestFlowManager.exe"
    ) else (
        echo 错误: 找不到 TestFlowManager EXE 文件!
        pause
        exit /b 1
    )
)

:run
echo 启动 %EXE_FILE% ...
start "" "%EXE_FILE%"
"""
    
    bat_path = dist_dir / "start.bat"
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print("创建启动批处理文件 start.bat")


def build_executable():
    """使用PyInstaller构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 清理 dist 目录中的旧构建文件（保留 config, Template 等用户数据）
    dist_dir = Path.cwd() / "dist"
    if dist_dir.exists():
        print("清理旧的构建文件...")
        # 只删除 PyInstaller 生成的文件和目录
        items_to_remove = [
            dist_dir / "_internal",
            dist_dir / "TestFlowManager.exe",
            dist_dir / "base_library.zip",
        ]
        for item in items_to_remove:
            if item.exists():
                if item.is_file():
                    item.unlink()
                    print(f"  删除: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"  删除目录: {item.name}")
    
    try:
        # 使用PyInstaller构建（不使用 --clean，避免清理整个 dist 目录）
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",  # ← 移除 --clean，避免权限问题
            "TestFlowManager.spec"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        # 修复编码问题：使用 utf-8 编码读取输出
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',  # 强制使用 UTF-8 编码
            errors='replace'   # 遇到无法解码的字符用 ? 替换
        )
        
        if result.returncode == 0:
            print("✅ 可执行文件构建成功!")
            if result.stdout:
                print(result.stdout)
            
            # 获取版本号和时闰戳
            version = get_version()
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # PyInstaller onedir 模式生成 dist/TestFlowManager/ 目录
            # 我们需要将所有文件移动到 dist/ 根目录
            build_dir = dist_dir / "TestFlowManager"
            
            if build_dir.exists():
                print(f"\n📦 整理文件结构...")
                print(f"   将 {build_dir}/ 下的文件移动到 {dist_dir}/")
                
                # 移动所有文件和子目录到 dist/ 根目录
                for item in build_dir.iterdir():
                    dest = dist_dir / item.name
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    shutil.move(str(item), str(dist_dir))
                    print(f"   ✅ 移动: {item.name}")
                
                # 删除空的 TestFlowManager 目录
                build_dir.rmdir()
                print(f"   ✅ 删除空目录: TestFlowManager/")
                
                # 重命名 EXE 文件
                old_exe = dist_dir / "TestFlowManager.exe"
                new_exe_name = f"TestFlowManager_v{version}_{timestamp}.exe"
                new_exe = dist_dir / new_exe_name
                
                if old_exe.exists():
                    if new_exe.exists():
                        new_exe.unlink()
                    old_exe.rename(new_exe)
                    print(f"\n✅ 已将可执行文件重命名为: {new_exe_name}")
                else:
                    print(f"\n⚠️  警告: 未找到 {old_exe}")
            else:
                print(f"❌ 错误: 未找到构建目录 {build_dir}")
                return False
            
            return True
        else:
            print("❌ 构建过程中出现错误:")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建可执行文件时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# 从src/__init__.py读取版本号
def get_version():
    """
    从src/__init__.py读取版本号
    """
    try:
        import sys
        project_root = Path.cwd()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        import src
        return src.__version__
    except Exception as e:
        print(f"警告: 无法从src/__init__.py读取版本号: {e}")
        return "1.0.0"  # 默认版本号


def main():
    """主函数"""
    print("TestFlowManager 可执行文件构建工具")
    print("=" * 50)
    
    # 检查当前目录
    project_root = Path.cwd()
    print(f"项目根目录: {project_root}")
    
    # 检查必要的文件是否存在
    required_files = ["TestFlowManager.spec", "src/app/application.py", "src/__init__.py"]
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

