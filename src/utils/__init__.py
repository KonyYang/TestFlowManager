# src/utils/__init__.py
"""
工具模块包
包含各种工具函数和类

启动优化：使用 __getattr__ 懒加载，避免启动时一次性导入所有子模块
（特别是 email_utils/excel_utils/msg_file_utils/word_utils 等含 COM 库的模块）
"""

import sys

# 模块名 → 属性名映射
_LAZY_MODULES = {
    'date_utils': None,
    'email_utils': None,
    'excel_utils': None,
    'file_utils': None,
    'log_handler': None,
    'msg_file_utils': None,
    'string_utils': None,
    'word_utils': None,
}

# 类名 → (模块名, 类名) 映射
_LAZY_CLASSES = {
    'DocumentEditorMixin': ('document_editor_mixin', 'DocumentEditorMixin'),
    'LTRDataManager': ('ltr_data_manager', 'LTRDataManager'),
}


def __getattr__(name):
    """懒加载子模块或类"""
    if name in _LAZY_MODULES:
        if _LAZY_MODULES[name] is None:
            _LAZY_MODULES[name] = __import__(f'src.utils.{name}', fromlist=[name])
        return _LAZY_MODULES[name]

    if name in _LAZY_CLASSES:
        mod_name, cls_name = _LAZY_CLASSES[name]
        # 先确保模块已加载
        if mod_name not in _LAZY_MODULES or _LAZY_MODULES[mod_name] is None:
            _LAZY_MODULES[mod_name] = __import__(f'src.utils.{mod_name}', fromlist=[mod_name])
        return getattr(_LAZY_MODULES[mod_name], cls_name)

    # 别名兼容：DateUtils → date_utils 等
    _alias_map = {
        'DateUtils': 'date_utils',
        'EmailUtils': 'email_utils',
        'ExcelUtils': 'excel_utils',
        'FileUtils': 'file_utils',
        'LogHandler': 'log_handler',
        'MSGFileUtils': 'msg_file_utils',
        'StringUtils': 'string_utils',
        'WordUtils': 'word_utils',
    }
    if name in _alias_map:
        return __getattr__(_alias_map[name])

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


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
    # 类
    'LTRDataManager',
    'DocumentEditorMixin',
    # 别名（向后兼容）
    'DateUtils',
    'EmailUtils',
    'ExcelUtils',
    'FileUtils',
    'LogHandler',
    'MSGFileUtils',
    'StringUtils',
    'WordUtils',
]
