"""
配置处理工具模块
提供配置文件的读取和写入功能
"""

import json
import os
from typing import Dict, Any, Optional
from src.core.logger import logger


class ConfigHandler:
    """
    配置处理类
    提供配置文件的读取、写入和管理功能
    """

    @staticmethod
    def load_json_config(file_path: str) -> Optional[Dict[str, Any]]:
        """
        加载JSON格式的配置文件

        Args:
            file_path: 配置文件路径

        Returns:
            配置字典或None（如果加载失败）
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load JSON config from '{file_path}': {e}")
            return None

    @staticmethod
    def save_json_config(file_path: str, config: Dict[str, Any]) -> bool:
        """
        保存配置到JSON文件

        Args:
            file_path: 配置文件路径
            config: 配置字典

        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON config to '{file_path}': {e}")
            return False

    @staticmethod
    def merge_configs(default_config: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并默认配置和用户配置

        Args:
            default_config: 默认配置
            user_config: 用户配置

        Returns:
            合并后的配置
        """
        merged = default_config.copy()
        merged.update(user_config)
        return merged


# 全局配置处理器实例
config_handler = ConfigHandler()
