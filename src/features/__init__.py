"""
功能特性模块初始化文件
"""

# 不自动导入所有模块以避免循环导入
# 各模块将在需要时单独导入

__all__ = []  # 空列表，不自动导出任何内容

# 仅在需要时导入report_updater，避免循环导入
def lazy_import_report_updater():
    """懒加载report_updater模块"""
    from . import report_updater
    return report_updater
