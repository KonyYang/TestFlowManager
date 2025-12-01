# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

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
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'win32com',
        'win32com.client',
        'win32timezone',
        'pythoncom',
        'extract_msg',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.cell._writer',
        'openpyxl.cell_writer',
        'docx',
        'pandas',
        'numpy',
        'numpy._core._multiarray_umath',
        'numpy._core.multiarray',
        'numpy._core',
        'numpy._core._dtype_ctypes',
        'numpy._core._multiarray_tests',
        'numpy.core._multiarray_tests',
        'numpy.core._multiarray_umath'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy.core._operand_flag_tests',
        'numpy.core._rational_tests',
        'numpy.core._umath_tests',
        'numpy.core.multiarray_tests',
        'numpy.core.setup_common',
        'numpy.distutils',
        'numpy.f2py',
        'numpy.random._examples'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TestFlowManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(current_dir, 'src', 'app', 'resources', 'icons', 'app_icon.ico') if os.path.exists(os.path.join(current_dir, 'src', 'app', 'resources', 'icons', 'app_icon.ico')) else None
)