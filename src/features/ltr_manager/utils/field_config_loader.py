"""
LTR字段配置加载器
用于从配置文件加载字段映射关系
"""

import os
import sys
import json
from typing import List, Dict, Any
from src.core.logger import logger
from src.core.config_manager import config_manager


class LTRFieldConfigLoader:
    """LTR字段配置加载器类"""

    def __init__(self):
        """
        初始化LTR字段配置加载器
        """
        # 获取用户配置文件路径
        self.config_file_path = self._get_config_file_path()

    def _get_config_file_path(self) -> str:
        """
        获取用户配置文件路径

        Returns:
            用户配置文件路径
        """
        # 从配置管理器获取配置文件相对路径
        config_file_relative_path = config_manager.get("ltr.fields_config", "app/config/ltr_fields.json")

        # 根据运行环境确定基础路径
        if getattr(sys, 'frozen', False):
            # 在可执行文件环境中，使用可执行文件所在目录作为基础路径
            base_path = os.path.dirname(sys.executable)
        else:
            # 在开发环境中，使
            # 用项目根目录作为基础路径
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        # 组合完整路径
        config_file_path = os.path.join(base_path, config_file_relative_path)
        return config_file_path

    def _get_default_config_path(self) -> str:
        """
        获取项目内置的默认配置文件路径

        Returns:
            默认配置文件路径
        """
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "app", "config", "ltr_fields.json"
        )

    def load_application_field_mapping(self) -> List[Dict[str, Any]]:
        """
        从配置文件加载应用字段映射关系

        Returns:
            字段映射关系列表
        """
        try:
            import os
            from pathlib import Path

            # 获取当前模块的路径
            current_dir = Path(__file__).parent

            # 尝试从项目根目录查找
            config_file_path = current_dir / ".." / ".." / ".." / "app" / "config" / "ltr_fields.json"

            if not config_file_path.exists():
                # 如果上述路径不存在，尝试从标准位置查找
                config_file_path = Path("src/app/config/ltr_fields.json")

            if not config_file_path.exists():
                logger.error(f"LTR字段配置文件未找到: {config_file_path}")
                return []

            # 读取并解析JSON配置文件
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            field_mapping = config.get('application_field_mapping', [])

            logger.info(f"成功从 {config_file_path} 加载 {len(field_mapping)} 个应用字段配置")
            return field_mapping

        except json.JSONDecodeError as e:
            logger.error(f"LTR字段配置文件格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载LTR应用字段配置时发生错误: {e}")
            return []


    def load_editor_field_mapping(self) -> List[Dict[str, Any]]:
        """
        从配置文件加载编辑器字段映射关系

        Returns:
            字段映射关系列表
        """
        try:
            # 确定要加载的配置文件路径
            if os.path.exists(self.config_file_path):
                # 使用用户自定义配置文件
                config_file_path = self.config_file_path
                logger.info(f"使用用户配置文件: {config_file_path}")
            else:
                # 使用项目内置默认配置文件
                config_file_path = self._get_default_config_path()
                logger.info(f"用户配置文件不存在，使用默认配置文件: {config_file_path}")

            # 读取并解析JSON配置文件
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            field_mapping = config.get('editor_field_mapping', [])

            logger.info(f"成功从 {config_file_path} 加载 {len(field_mapping)} 个编辑器字段配置")
            return field_mapping

        except json.JSONDecodeError as e:
            logger.error(f"LTR字段配置文件格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载LTR编辑器字段配置时发生错误: {e}")
            return []
