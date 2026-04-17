# -*- mode: python ; coding: utf-8 -*-
"""
TestFlowManager 打包配置

启动优化说明：
- 使用 onedir 模式替代 onefile，避免每次启动解压 ~100MB 归档（节省 3-8s）
- 移除不必要的 hiddenimports（numpy/pandas 已改为懒加载）
- 扩大 excludes 范围以减小包体积
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 获取当前工作目录
current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# 定义要包含的配置文件和资源文件
datas = [
    # 包含配置文件到config目录
    (os.path.join(current_dir, 'src', 'app', 'config'), 'config'),
]

# 收集其他可能需要的数据文件
datas += collect_data_files('src')

a = Analysis(
    [os.path.join(current_dir, 'src', 'app', 'application.py')],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt5 核心模块（启动必需）
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        # COM 相关（延迟加载，但需打包进去供运行时使用）
        'win32com',
        'win32com.client',
        'win32timezone',
        'pythoncom',
        # 文档处理库（自动收集所有子模块，避免遗漏内部引用）
        *collect_submodules('openpyxl'),
        'extract_msg',
        *collect_submodules('docx'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # NumPy 测试/内部模块（大幅减小体积）
        'numpy.core._operand_flag_tests',
        'numpy.core._rational_tests',
        'numpy.core._umath_tests',
        'numpy.core.multiarray_tests',
        'numpy.core.setup_common',
        'numpy.distutils',
        'numpy.f2py',
        'numpy.random._examples',
        'numpy.testing',
        'numpy.tests',
        'numpy.conftest',
        'numpy._pytesttester',
        # Pandas 测试模块
        'pandas.tests',
        'pandas._testing',
        # Matplotlib（如果被间接引入）
        'matplotlib',
        'matplotlib.pyplot',
        'mpl_toolkits',
        # 其他不常用的科学计算
        'scipy',
        'sklearn',
        'IPython',
        'jupyter',
        'notebook',
        # Tkinter（Qt 应用不需要）
        'tkinter',
        '_tkinter',
        'tcl',
        'tk',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# =========================================================================
# 使用 onedir 模式（目录模式），避免每次启动解压整个归档文件
# 预期效果：启动速度提升 3-8 秒
# =========================================================================
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,  # ← 关键：二进制和数据文件单独放置
    name='TestFlowManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.join(current_dir, 'src', 'app', 'resources', 'icons', 'app_icon.ico') if os.path.exists(os.path.join(current_dir, 'src', 'app', 'resources', 'icons', 'app_icon.ico')) else None
)

# 二进制文件、数据文件等放到同目录下（而非嵌入 exe）
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TestFlowManager',
)