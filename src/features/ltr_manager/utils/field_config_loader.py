"""
LTR字段配置加载器（兼容性重导出）。

真实实现已迁至 src/domain/project/ltr_field_config_loader.py (2026-04-19)。
本文件保留为兼容性重导出，供 features 层内部使用。

迁移原因：消除 domain → features 反向依赖。
"""

from src.domain.project.ltr_field_config_loader import LTRFieldConfigLoader

__all__ = ['LTRFieldConfigLoader']
