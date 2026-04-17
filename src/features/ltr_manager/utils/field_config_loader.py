"""
LTR字段配置加载器
用于从配置文件加载字段映射关系
"""

import json
import os
from typing import Any, Dict, List

from src.core.logger import logger
from src.core.path_utils import get_executable_dir


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

        使用统一的路径解析，兼容开发模式和打包模式。
        - 打包模式: <_internal>/config/ltr_fields.json（PyInstaller 数据目录）
        - 开发模式: <项目根>/src/app/config/ltr_fields.json（源码实际位置）

        Returns:
            配置文件的绝对路径
        """
        from src.core.path_utils import get_resource_path, is_frozen

        if is_frozen():
            # 打包模式：datas 在 _internal/config/ 下（见 TestFlowManager.spec）
            return get_resource_path("config", "ltr_fields.json")
        else:
            # 开发模式：源码实际位于 src/app/config/
            return get_resource_path("src", "app", "config", "ltr_fields.json")

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
