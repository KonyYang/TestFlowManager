"""
配置管理器模块
负责管理应用程序的配置信息
"""

import json
import logging
import os
import sys
from typing import Dict, Any, Optional

# 使用统一的路径解析工具，避免硬编码路径
from src.core.path_utils import (
    get_base_path,
    get_executable_dir,
    get_resource_path as utils_get_resource_path,
    is_frozen,
)

module_logger = logging.getLogger(__name__)


class ConfigManager:
    """
    配置管理器类
    管理应用程序的配置信息，支持从文件加载和保存配置
    """

    MAIN_CONFIG_FILENAME = "settings.json"
    PATHS_CONFIG_FILENAME = "paths.ini"
    DEFAULT_MAIN_CONFIG = MAIN_CONFIG_FILENAME
    DEFAULT_PATHS_CONFIG = PATHS_CONFIG_FILENAME

    def __init__(self, config_file: str = DEFAULT_MAIN_CONFIG):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load_main_config()
        
        # ✅ 修复：使用 resolve_config_path() 获取正确的配置文件路径
        # 开发环境: src/app/config/paths.ini
        # 打包环境: dist/config/paths.ini (优先) 或 _internal/src/app/config/paths.ini (fallback)
        paths_config_actual_path = self.resolve_config_path(self.DEFAULT_PATHS_CONFIG)
        self.load_paths_config_from_path(paths_config_actual_path)

    def load_main_config(self) -> None:
        """从主配置文件加载配置"""
        config_path = self.resolve_config_path(self.config_file)
        if os.path.exists(config_path):
            try:
                # 尝试使用 utf-8-sig 编码（处理BOM）
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    self._config = json.load(f)
            except Exception as e:
                module_logger.warning(
                    "Failed to load config from %s with utf-8-sig: %s",
                    config_path,
                    e,
                )
                try:
                    # 如果 utf-8-sig 失败，尝试使用 utf-8 编码
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
                except Exception as e2:
                    module_logger.warning(
                        "Failed to load config from %s with utf-8: %s",
                        config_path,
                        e2,
                    )
                try:
                    # 如果都失败了，尝试使用默认编码
                    with open(config_path, 'r') as f:
                        self._config = json.load(f)
                except Exception as e3:
                        module_logger.error(
                            "Failed to load config from %s with default encoding: %s",
                            config_path,
                            e3,
                        )
                        self._config = {}
        else:
            # 如果配置文件不存在，使用默认配置
            self._config = self._get_default_config()

    def load_paths_config(self, paths_file: str = PATHS_CONFIG_FILENAME) -> None:
        """
        从INI格式的路径配置文件加载路径配置（兼容性方法）

        Args:
            paths_file: 路径配置文件路径（可以是相对路径或绝对路径）
        
        Note:
            此方法保留用于向后兼容，新代码应使用 load_paths_config_from_path()
        """
        # 判断是否为绝对路径
        if os.path.isabs(paths_file):
            self.load_paths_config_from_path(paths_file)
        else:
            # 相对路径：使用 resolve_config_path 解析
            actual_path = self.resolve_config_path(paths_file)
            self.load_paths_config_from_path(actual_path)

    def load_paths_config_from_path(self, paths_path: str) -> None:
        """
        从指定路径加载路径配置文件

        Args:
            paths_path: 配置文件的绝对路径
        """
        try:
            import configparser
            
            # ✅ 添加调试日志
            module_logger.debug("Loading paths config from: %s", paths_path)
            
            if not os.path.exists(paths_path):
                module_logger.warning("Paths config file not found: %s", paths_path)
                return
            
            paths_config = configparser.ConfigParser()
            paths_config.read(paths_path, encoding='utf-8')

            # 将INI配置转换为内部配置格式
            if 'Paths' in paths_config:
                for key, value in paths_config['Paths'].items():
                    # 只加载ltr_file配置，其他路径配置从settings.json获取
                    if key.lower() == 'ltr_file':
                        self.set(f"paths.{key.lower()}", value)
                        module_logger.info("Loaded ltr_file path: %s", value)

            # 加载标准文件配置
            if 'STANDARD_FILES' in paths_config:
                for key, value in paths_config['STANDARD_FILES'].items():
                    self.set(f"standard_files.{key}", value)

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
                    module_logger.info(
                        "Loading equipment data sources from section: %s",
                        section_name,
                    )
                    for key, value in paths_config[section_name].items():
                        self.set(f"equipment_data_sources.{key.lower()}", value)
                    break  # 找到第一个匹配的节就停止
                    
            module_logger.debug("Paths config loaded successfully from: %s", paths_path)
        except Exception as e:
            module_logger.error(
                "Failed to load paths config from %s: %s",
                paths_path,
                e,
                exc_info=True,
            )

    def _get_resource_path(self, relative_path: str) -> str:
        """
        获取资源配置文件的绝对路径
        
        策略：
        - 打包环境(onedir): 优先从 exe 同级目录的 config/ 读取（用户可编辑）
        - 开发环境: 从嵌入配置目录读取
        
        Args:
            relative_path: 配置资源相对路径或文件名

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

    def get_embedded_config_path(self, filename: str) -> str:
        """获取嵌入资源中的配置文件路径。"""
        return utils_get_resource_path("src", "app", "config", filename)

    def get_external_config_path(self, filename: str) -> str:
        """获取打包环境下可编辑配置文件路径。"""
        return os.path.join(get_executable_dir(), "config", filename)

    def resolve_config_path(self, filename: str) -> str:
        """
        解析实际使用的配置文件路径。

        打包环境优先读取 exe 同级 config/ 下的用户可编辑配置，
        否则回退到嵌入资源；开发环境始终读取源码内配置。
        """
        embedded_path = self.get_embedded_config_path(filename)
        if not is_frozen():
            return embedded_path

        external_path = self.get_external_config_path(filename)
        if os.path.exists(external_path):
            return external_path
        return embedded_path

    def get_main_config_path(self) -> str:
        """获取主配置文件实际路径。"""
        return self.resolve_config_path(os.path.basename(self.config_file))

    def get_paths_config_path(self) -> str:
        """获取路径配置文件实际路径。"""
        return self.resolve_config_path(os.path.basename(self.DEFAULT_PATHS_CONFIG))

    def get_config_root_dir(self) -> str:
        """获取实际配置根目录。"""
        return os.path.dirname(self.get_main_config_path())

    def get_embedded_config_root_dir(self) -> str:
        """获取嵌入资源配置根目录。"""
        return os.path.dirname(self.get_embedded_config_path("settings.json"))

    def get_external_config_root_dir(self) -> str:
        """获取外部可编辑配置根目录。"""
        return os.path.dirname(self.get_external_config_path("settings.json"))

    def get_app_config_path(self, filename: str) -> str:
        """
        获取 app/config/ 下指定配置文件的绝对路径（公共便捷方法）。

        供 feature 层配置加载器使用，避免各模块重复构造 "src/app/config/" 路径前缀。
        内部委托 _get_resource_path() 统一处理开发/打包双模式解析。

        Args:
            filename: 配置文件名 (如 "ltr_fields.json")

        Returns:
            配置文件的绝对路径

        示例:
            >>> config_manager.get_app_config_path("ltr_fields.json")
            'd:/.../src/app/config/ltr_fields.json'
        """
        return self.resolve_config_path(filename)

    def describe_config_source(self) -> str:
        """返回当前运行模式下的配置来源描述。"""
        mode = "生产环境配置" if getattr(sys, "frozen", False) else "开发环境配置"
        return f"{mode}({self.get_paths_config_path()})"

    def describe_config_policy(self) -> str:
        """返回当前 config-root 决策说明。"""
        if not is_frozen():
            return (
                "开发环境: 直接读取嵌入配置目录 "
                f"({self.get_embedded_config_root_dir()})"
            )

        external_root = self.get_external_config_root_dir()
        embedded_root = self.get_embedded_config_root_dir()
        if os.path.exists(self.get_paths_config_path()):
            return (
                "生产环境: 优先读取 exe 同级可编辑配置 "
                f"({external_root})，缺失时回退到嵌入配置 ({embedded_root})"
            )
        return (
            "生产环境: 外部配置缺失，当前回退到嵌入配置 "
            f"({embedded_root})"
        )

    def get_log_file_path(self, default: str = "testflow.log") -> str:
        """统一解析日志文件路径，避免重复 dev/frozen base-path 逻辑。"""
        log_file_path = self.get_logging("file", default)
        if os.path.isabs(log_file_path):
            return log_file_path
        return os.path.join(get_base_path(), log_file_path)

    def save_config(self) -> None:
        """保存配置到文件"""
        config_path = self.resolve_config_path(self.config_file)
        # 确保配置目录存在
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            module_logger.error("Failed to save config to %s: %s", config_path, e)

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

    def _resolve_configured_dir(
        self,
        config_key: str,
        default_dir_name: str,
        default: Optional[str] = None,
    ) -> str:
        """
        统一解析可配置目录路径。

        优先级:
        1. 配置文件中的绝对路径
        2. 配置文件中的相对路径（打包态下锚定 exe 目录）
        3. 调用方传入 default
        4. exe 目录下的默认子目录
        """
        config_value = self.get_path(config_key, "")
        if config_value:
            if os.path.isabs(config_value):
                return config_value
            if is_frozen():
                return os.path.join(get_executable_dir(), config_value)
            return config_value

        if default is not None:
            return default
        return os.path.join(get_executable_dir(), default_dir_name)

    def get_template_dir(self, default: str = None) -> str:
        r"""
        获取模板目录路径。
        
        优先级:
        1. 配置文件中的绝对路径 (如 D:\TestFlowManager\Template)
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值 (仅当配置未定义时)
        """
        return self._resolve_configured_dir("template_dir", "Template", default)

    def get_default_project_dir(self, default: str = None) -> str:
        """
        获取默认项目目录路径。
        
        优先级:
        1. 配置文件中的绝对路径
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值
        """
        return self._resolve_configured_dir(
            "default_project_path",
            "Projects",
            default,
        )

    def get_backup_dir(self, default: str = None) -> str:
        """
        获取备份目录路径。
        
        优先级:
        1. 配置文件中的绝对路径
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值
        """
        return self._resolve_configured_dir("backup_path", "Backup", default)

    def get_temp_dir(self, default: str = None) -> str:
        """
        获取临时目录路径。
        
        优先级:
        1. 配置文件中的绝对路径
        2. 传入的 default 参数
        3. 基于 exe 目录的动态默认值
        """
        return self._resolve_configured_dir("temp_dir", "Temp", default)

    def get_output_dir(self, default: str = None) -> str:
        """
        获取全局输出目录路径（非项目态文件兜底目录）。

        优先级:
        1. settings.json 中 paths.output_dir 的绝对路径
        2. paths.ini 中 EquipmentDataSources.default_output_path（传统配置源）
        3. 传入的 default 参数
        4. 基于 exe 目录的动态默认值 (OutFile 子目录)
        """
        # 先尝试 settings.json 的 paths.output_dir
        config_value = self.get_path("output_dir", "")
        if config_value:
            if os.path.isabs(config_value):
                return config_value
            if is_frozen():
                return os.path.join(get_executable_dir(), config_value)
            return config_value

        # 兼容 paths.ini 的 EquipmentDataSources.default_output_path
        legacy_output = self.get_equipment_data_source("default_output_path", "")
        if legacy_output:
            legacy_output = legacy_output.rstrip("\\/")
            if os.path.isabs(legacy_output):
                return legacy_output
            if is_frozen():
                return os.path.join(get_executable_dir(), legacy_output)
            return legacy_output

        if default is not None:
            return default
        return os.path.join(get_executable_dir(), "OutFile")

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
