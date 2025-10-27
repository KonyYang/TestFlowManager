"""
配置管理器模块
负责管理应用程序的配置信息
"""

import json
import os
import sys
from typing import Dict, Any, Optional


class ConfigManager:
    """
    配置管理器类
    管理应用程序的配置信息，支持从文件加载和保存配置
    """

    def __init__(self, config_file: str = "config/settings.json"):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load_main_config()
        self.load_paths_config("config/paths.ini")

    def load_main_config(self) -> None:
        """从主配置文件加载配置"""
        config_path = self._get_resource_path(self.config_file)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Failed to load config from {config_path}: {e}")
                self._config = {}
        else:
            # 如果配置文件不存在，使用默认配置
            self._config = self._get_default_config()

    def load_paths_config(self, paths_file: str = "config/paths.ini") -> None:
        """
        从INI格式的路径配置文件加载路径配置

        Args:
            paths_file: 路径配置文件路径
        """
        try:
            import configparser
            paths_path = self._get_resource_path(paths_file)
            if os.path.exists(paths_path):
                paths_config = configparser.ConfigParser()
                paths_config.read(paths_path, encoding='utf-8')

                # 将INI配置转换为内部配置格式
                if 'Paths' in paths_config:
                    for key, value in paths_config['Paths'].items():
                        # 保持原始路径格式，不做转换
                        self.set(f"paths.{key.lower()}", value)

                # 加载密码配置
                if 'Passwords' in paths_config:
                    for key, value in paths_config['Passwords'].items():
                        self.set(f"passwords.{key.lower()}", value)
                        
                # 加载默认值配置
                if 'Defaults' in paths_config:
                    for key, value in paths_config['Defaults'].items():
                        self.set(f"defaults.{key.lower()}", value)
        except Exception as e:
            print(f"Failed to load paths config from {paths_file}: {e}")

    def _get_resource_path(self, relative_path: str) -> str:
        """
        获取资源配置文件的绝对路径
        在开发模式下返回相对路径，在可执行模式下返回可执行文件目录下的路径

        Args:
            relative_path: 相对路径

        Returns:
            资源文件的绝对路径
        """
        # 检查是否为可执行文件模式
        if getattr(sys, 'frozen', False):
            # 如果是可执行文件模式，从可执行文件所在目录加载配置
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发模式，使用当前工作目录
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

    def save_config(self) -> None:
        """保存配置到文件"""
        config_path = self._get_resource_path(self.config_file)
        # 确保配置目录存在
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config to {config_path}: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app": {
                "name": "TestFlowManager",
                "version": "1.0.0",
                "debug": False
            },
            "window": {
                "width": 600,
                "height": 400,
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
        # 获取配置对象的引用
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