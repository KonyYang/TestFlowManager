# src/utils/__init__.py
"""
工具模块包
包含各种工具函数和类
"""

# 直接导入模块（对于主要包含函数的模块）
from . import date_utils
from . import email_utils
from . import excel_utils
from . import file_utils
from . import log_handler
from . import msg_file_utils
from . import string_utils
from . import word_utils

# 导入类（对于包含类定义的模块）
from .config_handler import ConfigHandler
from .ltr_data_manager import LTRDataManager
from .document_content_editor import DocumentContentEditor

# 为了向后兼容，创建别名
DateUtils = date_utils
EmailUtils = email_utils
ExcelUtils = excel_utils
FileUtils = file_utils
LogHandler = log_handler
MSGFileUtils = msg_file_utils
StringUtils = string_utils
WordUtils = word_utils

__all__ = [
    # 模块
    'date_utils',
    'email_utils',
    'excel_utils',
    'file_utils',
    'log_handler',
    'msg_file_utils',
    'string_utils',
    'word_utils',
    'ConfigHandler',
    'LTRDataManager',
    'DocumentContentEditor',
    # 别名
    'DateUtils',
    'EmailUtils',
    'ExcelUtils',
    'FileUtils',
    'LogHandler',
    'MSGFileUtils',
    'StringUtils',
    'WordUtils',
    'DocumentContentEditor'
]