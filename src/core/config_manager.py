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
        # print(f"[DEBUG] Loading main config from: {config_path}")
        if os.path.exists(config_path):
            try:
                # 尝试使用 utf-8-sig 编码（处理BOM）
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    self._config = json.load(f)
                # print(f"[DEBUG] Loaded config: {self._config}")
            except Exception as e:
                print(f"Failed to load config from {config_path} with utf-8-sig: {e}")
                try:
                    # 如果 utf-8-sig 失败，尝试使用 utf-8 编码
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
                    # print(f"[DEBUG] Loaded config with utf-8: {self._config}")
                except Exception as e2:
                    print(f"Failed to load config from {config_path} with utf-8: {e2}")
                    try:
                        # 如果都失败了，尝试使用默认编码
                        with open(config_path, 'r') as f:
                            self._config = json.load(f)
                        # print(f"[DEBUG] Loaded config with default encoding: {self._config}")
                    except Exception as e3:
                        print(f"Failed to load config from {config_path} with default encoding: {e3}")
                        self._config = {}
        else:
            # 如果配置文件不存在，使用默认配置
            # print(f"[DEBUG] Config file not found, using default config")
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
            # print(f"[DEBUG] Loading paths config from: {paths_path}")
            if os.path.exists(paths_path):
                paths_config = configparser.ConfigParser()
                paths_config.read(paths_path, encoding='utf-8')
                # print(f"[DEBUG] Loaded sections: {paths_config.sections()}")

                # 将INI配置转换为内部配置格式
                if 'Paths' in paths_config:
                    for key, value in paths_config['Paths'].items():
                        # 只加载ltr_file配置，其他路径配置从settings.json获取
                        if key.lower() == 'ltr_file':
                            self.set(f"paths.{key.lower()}", value)
                            
                # 加载标准文件配置
                if 'STANDARD_FILES' in paths_config:
                    # print(f"[DEBUG] Loading STANDARD_FILES section")
                    for key, value in paths_config['STANDARD_FILES'].items():
                        # print(f"[DEBUG] STANDARD_FILES key: '{key}', value: '{value}'")
                        self.set(f"standard_files.{key}", value)
                        # print(f"[DEBUG] Set config key: standard_files.{key}")

                # 加载密码配置
                if 'Passwords' in paths_config:
                    for key, value in paths_config['Passwords'].items():
                        self.set(f"passwords.{key.lower()}", value)
                        
                # 加载默认值配置
                if 'Defaults' in paths_config:
                    for key, value in paths_config['Defaults'].items():
                        self.set(f"defaults.{key.lower()}", value)
                        
                # 加载设备数据源配置
                if 'EquipmentDataSources' in paths_config:
                    for key, value in paths_config['EquipmentDataSources'].items():
                        self.set(f"equipment_data_sources.{key.lower()}", value)
            else:
                print(f"[DEBUG] Paths config file not found: {paths_path}")
        except Exception as e:
            print(f"Failed to load paths config from {paths_file}: {e}")
            import traceback
            traceback.print_exc()

    def _get_resource_path(self, relative_path: str) -> str:
        """
        获取资源配置文件的绝对路径
        在开发模式下返回相对路径，在可执行模式下返回可执行文件目录下的路径

        Args:
            relative_path: 相对路径

        Returns:
            资源文件的绝对路径
        """
        # 1. 首先检查是否为可执行文件模式
        if getattr(sys, 'frozen', False):
            # 如果是可执行文件模式，优先从生产环境路径加载配置
            production_config_path = os.path.join("D:", "TestFlowManager", relative_path)
            # print(f"[DEBUG] Frozen mode, checking production config path: {production_config_path}")
            if os.path.exists(production_config_path):
                # print(f"[DEBUG] Using production config path: {production_config_path}")
                return production_config_path
            
            # 如果生产环境路径不存在，则从可执行文件所在目录加载配置
            base_path = os.path.dirname(sys.executable)
            # print(f"[DEBUG] Frozen mode, using executable directory: {base_path}")
            
            # 在可执行文件模式下，检查生成环境路径
            generated_env_path = os.path.join(base_path, relative_path)
            # print(f"[DEBUG] Checking generated environment path: {generated_env_path}")
            if os.path.exists(generated_env_path):
                # print(f"[DEBUG] Using generated environment path: {generated_env_path}")
                return generated_env_path
            else:
                # 如果直接路径不存在，尝试在config子目录中查找
                config_path = os.path.join(base_path, "config", os.path.basename(relative_path))
                # print(f"[DEBUG] Checking config path: {config_path}")
                if os.path.exists(config_path):
                    # print(f"[DEBUG] Using config path: {config_path}")
                    return config_path
        else:
            # 如果是开发模式，需要检查当前工作目录来确定正确的基路径
            base_path = os.path.abspath(".")
            # print(f"[DEBUG] Development mode, using current directory: {base_path}")
            
            # 检查当前目录是否为src/app目录
            if os.path.basename(base_path) == "app" and os.path.basename(os.path.dirname(base_path)) == "src":
                # 如果当前在src/app目录下，需要向上两级到达项目根目录
                project_root = os.path.dirname(os.path.dirname(base_path))
                result_path = os.path.join(project_root, "src", "app", relative_path)
                # print(f"[DEBUG] Development mode resource path from src/app: {result_path}")
                return result_path
            else:
                # 否则假设当前在项目根目录
                result_path = os.path.join(base_path, "src", "app", relative_path)
                # print(f"[DEBUG] Development mode resource path: {result_path}")
                return result_path

        result_path = os.path.join(base_path, relative_path)
        # print(f"[DEBUG] Final resource path: {result_path}")
        return result_path

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
                "width": 800,
                "height": 600,
                "position_x": 100,
                "position_y": 100
            },
            "logging": {
                "level": "DEBUG",
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
            # 特殊处理标准文件路径和普通路径，在可执行文件模式下转换为绝对路径
            # 仅对配置中定义的路径进行处理，不处理其他配置项
            if (key.startswith("standard_files.") or key.startswith("paths.")) and isinstance(default, str):
                if getattr(sys, 'frozen', False):
                    # 在可执行文件模式下，将相对路径转换为绝对路径
                    if not os.path.isabs(default):
                        base_path = os.path.dirname(sys.executable)
                        abs_path = os.path.join(base_path, default)
                        return abs_path
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