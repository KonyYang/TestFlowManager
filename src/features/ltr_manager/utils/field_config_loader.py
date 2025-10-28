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
        pass

    def _get_config_file_path(self) -> str:
        """
        获取用户配置文件路径

        Returns:
            用户配置文件路径
        """
        # 根据运行环境确定配置文件路径
        if getattr(sys, 'frozen', False):
            # 在可执行文件环境中
            config_file_path = os.path.join(os.path.dirname(sys.executable), "config", "ltr_fields.json")
        else:
            # 在开发环境中
            config_file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                "app", "config", "ltr_fields.json"
            )
            
        logger.debug(f"配置文件路径: {config_file_path}")
        return config_file_path

    def _get_default_config_path(self) -> str:
        """
        获取项目内置的默认配置文件路径

        Returns:
            默认配置文件路径
        """
        return self._get_config_file_path()

    def load_application_field_mapping(self) -> List[Dict[str, Any]]:
        """
        从配置文件加载应用字段映射关系

        Returns:
            字段映射关系列表
        """
        try:
            # 获取配置文件路径
            config_file_path = self._get_config_file_path()
            
            if not os.path.exists(config_file_path):
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
            # 获取配置文件路径
            config_file_path = self._get_config_file_path()
            
            logger.debug(f"尝试加载编辑器字段配置: {config_file_path}")
            
            if not os.path.exists(config_file_path):
                logger.error(f"LTR字段配置文件未找到: {config_file_path}")
                return []

            # 读取并解析JSON配置文件
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            field_mapping = config.get('editor_field_mapping', [])
            
            logger.debug(f"加载到 {len(field_mapping)} 个编辑器字段配置")

            logger.info(f"成功从 {config_file_path} 加载 {len(field_mapping)} 个编辑器字段配置")
            return field_mapping

        except json.JSONDecodeError as e:
            logger.error(f"LTR字段配置文件格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载LTR编辑器字段配置时发生错误: {e}")
            return []