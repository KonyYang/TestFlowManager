"""
配置管理器模块
负责管理应用程序的配置信息
"""

import json
import os
import sys
from typing import Dict, Any, Optional

# 使用统一的路径解析工具，避免硬编码路径
from src.core.path_utils import get_resource_path as utils_get_resource_path, get_executable_dir, is_frozen


class ConfigManager:
    """
    配置管理器类
    管理应用程序的配置信息，支持从文件加载和保存配置
    """

    DEFAULT_MAIN_CONFIG = "src/app/config/settings.json"
    DEFAULT_PATHS_CONFIG = "src/app/config/paths.ini"

    def __init__(self, config_file: str = DEFAULT_MAIN_CONFIG):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load_main_config()
        self.load_paths_config(self.DEFAULT_PATHS_CONFIG)

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

    def load_paths_config(self, paths_file: str = "src/app/config/paths.ini") -> None:
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
                        
                # 加载设备数据源配置（兼容大小写）
                equipment_sections = ['EquipmentDataSources', 'EQUIPMENT_DATA_SOURCES', 'equipmentdatasources']
                for section_name in equipment_sections:
                    if section_name in paths_config:
                        print(f"[INFO] Loading equipment data sources from section: {section_name}")
                        for key, value in paths_config[section_name].items():
                            self.set(f"equipment_data_sources.{key.lower()}", value)
                        break  # 找到第一个匹配的节就停止
            else:
                print(f"[DEBUG] Paths config file not found: {paths_path}")
        except Exception as e:
            print(f"Failed to load paths config from {paths_file}: {e}")
            import traceback
            traceback.print_exc()

    def _get_resource_path(self, relative_path: str) -> str:
        """
        获取资源配置文件的绝对路径
        
        策略：
        - 打包环境(onedir): 优先从 exe 同级目录的 config/ 读取（用户可编辑）
        - 开发环境: 从 src/app/config/ 读取
        
        Args:
            relative_path: 相对路径 (如 "src/app/config/settings.json")

        Returns:
            资源文件的绝对路径
        """
        # ✅ 打包环境：从 exe 同级目录的 config/ 读取
        if is_frozen():
            # 提取文件名，忽略原始路径结构
            filename = os.path.basename(relative_path)
            exe_dir = get_executable_dir()
            external_config_path = os.path.join(exe_dir, "config", filename)
            
            # 如果外部配置文件存在，优先使用（用户可编辑）
            if os.path.exists(external_config_path):
                return external_config_path
            
            # 否则 fallback 到 _internal/config/ （打包时嵌入的资源）
            return utils_get_resource_path(relative_path)
        
        # ✅ 开发环境：从源码目录读取
        return utils_get_resource_path(relative_path)

    def get_main_config_path(self) -> str:
        """获取主配置文件实际路径。"""
        return self._get_resource_path(self.config_file)

    def get_paths_config_path(self) -> str:
        """获取路径配置文件实际路径。"""
        return self._get_resource_path(self.DEFAULT_PATHS_CONFIG)

    def get_config_root_dir(self) -> str:
        """获取实际配置根目录。"""
        return os.path.dirname(self.get_main_config_path())

    def describe_config_source(self) -> str:
        """返回当前运行模式下的配置来源描述。"""
        mode = "生产环境配置" if getattr(sys, "frozen", False) else "开发环境配置"
        return f"{mode}({self.get_paths_config_path()})"

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

    def get_path(self, key: str, default: str = "") -> str:
        return self.get(f"paths.{key}", default)

    def get_template_dir(self, default: str = None) -> str:
        r"""
        获取模板目录路径。
        
        优先级:
        1. 配置文件中的绝对路径 (如 D:\TestFlowManager\Template)
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值 (仅当配置未定义时)
        """
        # 首先尝试从配置文件读取
        config_value = self.get_path("template_dir", "")
        
        # 如果配置文件中定义了路径(无论是绝对还是相对),优先使用
        if config_value:
            # 如果是绝对路径,直接返回
            if os.path.isabs(config_value):
                return config_value
            # 如果是相对路径,在打包环境下转换为绝对路径
            if is_frozen():
                return os.path.join(get_executable_dir(), config_value)
            return config_value
        
        # 配置文件中未定义,使用默认值
        if default is None:
            default = os.path.join(get_executable_dir(), "Template")
        return default

    def get_default_project_dir(self, default: str = None) -> str:
        """
        获取默认项目目录路径。
        
        优先级:
        1. 配置文件中的绝对路径
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值
        """
        config_value = self.get_path("default_project_path", "")
        
        if config_value:
            if os.path.isabs(config_value):
                return config_value
            if is_frozen():
                return os.path.join(get_executable_dir(), config_value)
            return config_value
        
        if default is None:
            default = os.path.join(get_executable_dir(), "Projects")
        return default

    def get_backup_dir(self, default: str = None) -> str:
        """
        获取备份目录路径。
        
        优先级:
        1. 配置文件中的绝对路径
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值
        """
        config_value = self.get_path("backup_path", "")
        
        if config_value:
            if os.path.isabs(config_value):
                return config_value
            if is_frozen():
                return os.path.join(get_executable_dir(), config_value)
            return config_value
        
        if default is None:
            default = os.path.join(get_executable_dir(), "Backup")
        return default

    def get_temp_dir(self, default: str = None) -> str:
        """
        获取临时目录路径。
        
        优先级:
        1. 配置文件中的绝对路径
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值
        """
        config_value = self.get_path("temp_dir", "")
        
        if config_value:
            if os.path.isabs(config_value):
                return config_value
            if is_frozen():
                return os.path.join(get_executable_dir(), config_value)
            return config_value
        
        if default is None:
            default = os.path.join(get_executable_dir(), "Temp")
        return default

    def get_default(self, key: str, default: Any = "") -> Any:
        return self.get(f"defaults.{key}", default)

    def get_password(self, key: str, default: str = "") -> str:
        return self.get(f"passwords.{key}", default)

    def get_logging(self, key: str, default: Any = None) -> Any:
        return self.get(f"logging.{key}", default)

    def get_standard_file(self, key: str, default: Any = "") -> Any:
        return self.get(f"standard_files.{key}", default)

    def get_equipment_data_source(self, key: str, default: Any = "") -> Any:
        return self.get(f"equipment_data_sources.{key}", default)

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
