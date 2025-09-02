"""
配置管理器模块
负责管理应用程序的配置信息
"""

import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """
    配置管理器类
    管理应用程序的配置信息，支持从文件加载和保存配置
    """

    def __init__(self, config_file: str = "config/settings.ini"):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """从配置文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Failed to load config from {self.config_file}: {e}")
                self._config = {}
        else:
            # 如果配置文件不存在，使用默认配置
            self._config = self._get_default_config()

    def save_config(self) -> None:
        """保存配置到文件"""
        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config to {self.config_file}: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app": {
                "name": "TestFlowManager",
                "version": "1.0.0",
                "debug": False
            },
            "window": {
                "width": 1200,
                "height": 800,
                "position_x": 100,
                "position_y": 100
            },
            "logging": {
                "level": "INFO",
                "file": "logs/testflow.log"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项的值

        Args:
            key: 配置项键名（支持点号分隔的嵌套键名，如 "app.name"）
            default: 默认值

        Returns:
            配置项的值或默认值
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项的值

        Args:
            key: 配置项键名（支持点号分隔的嵌套键名，如 "app.name"）
            value: 配置项的值
        """
        keys = key.split('.')
        config = self._config

        # 导航到倒数第二层
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置最后一层的值
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置

        Returns:
            包含所有配置的字典
        """
        return self._config.copy()


# 全局配置管理器实例
config_manager = ConfigManager()
