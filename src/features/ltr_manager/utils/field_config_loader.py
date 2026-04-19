"""
LTR字段配置加载器
用于从配置文件加载字段映射关系
"""

import json
import os
from typing import Any, Dict, List

from src.core.logger import logger


class LTRFieldConfigLoader:
    """LTR字段配置加载器类"""

    def __init__(self):
        """
        初始化LTR字段配置加载器
        """
        pass

    def _get_config_file_path(self) -> str:
        """
        获取LTR字段配置文件路径。

        委托给 ConfigManager.get_app_config_path() 统一处理开发/打包双模式路径解析，
        消除重复的 is_frozen / get_executable_dir 分支逻辑。

        Returns:
            配置文件的绝对路径
        """
        from src.core.config_manager import config_manager
        return config_manager.get_app_config_path("ltr_fields.json")

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径（与主路径相同）。"""
        return self._get_config_file_path()

    def _load_field_mapping(self, mapping_key: str) -> list:
        """通用的字段映射加载逻辑，消除重复代码。"""
        try:
            config_file_path = self._get_config_file_path()

            if not os.path.exists(config_file_path):
                logger.error(f"LTR字段配置文件未找到: {config_file_path}")
                return []

            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            field_mapping = config.get(mapping_key, [])
            logger.info(f"成功从 {config_file_path} 加载 {len(field_mapping)} 个{mapping_key}配置")
            return field_mapping

        except json.JSONDecodeError as e:
            logger.error(f"LTR字段配置文件格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载LTR字段配置时发生错误: {e}")
            return []

    def load_application_field_mapping(self) -> list[Dict[str, Any]]:
        """从配置文件加载应用字段映射关系。"""
        return self._load_field_mapping('application_field_mapping')

    def load_editor_field_mapping(self) -> list[Dict[str, Any]]:
        """从配置文件加载编辑器字段映射关系。"""
        return self._load_field_mapping('editor_field_mapping')
