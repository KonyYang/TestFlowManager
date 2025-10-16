## 开发指南

1. 每个功能模块遵循 MVCS 架构模式 (Model-View-Controller-Service)
2. 使用事件驱动架构进行模块间通信
3. 通过 ActionManager 协调复杂操作
4. 通用组件放在 common/ 目录，工具函数放在 utils/ 目录
"""
    
    with open(os.path.join(project_root, "README.md"), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # 创建 requirements.txt
    requirements_content = """PyQt5>=5.15.0
python-docx>=0.8.11
pywin32>=227; sys_platform == 'win32'
"""
    
    with open(os.path.join(project_root, "requirements.txt"), 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    # 创建 setup.py
    setup_content = """from setuptools import setup, find_packages

setup(
    name="TestFlowManager",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyQt5>=5.15.0",
        "python-docx>=0.8.11",
    ],
    extras_require={
        "win32": ["pywin32>=227"],
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "testflow-manager=src.main:main",
        ],
    },
)
"""
    
    with open(os.path.join(project_root, "setup.py"), 'w', encoding='utf-8') as f:
        f.write(setup_content)
    
    # 创建核心基础设施文件
    create_core_infrastructure(project_root)
    
    # 创建管理器文件
    create_manager_files(project_root)
    
    # 创建通用组件
    create_common_components(project_root)
    
    # 创建工具函数
    create_util_files(project_root)
    
    # 创建主窗口模块
    create_main_window_module(project_root)
    
    # 创建应用入口
    create_app_entry(project_root)

def create_core_infrastructure(project_root):
    """创建核心基础设施文件"""
    
    # Event Dispatcher
    event_dispatcher_content = """\"\"\"
事件分发器
负责应用程序中的事件管理和分发
\"\"\"

import logging
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

class EventDispatcher:
    \"\"\"事件分发器\"\"\"
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def add_listener(self, event_type: str, callback: Callable) -> None:
        \"\"\"添加事件监听器\"\"\"
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.debug(f"Added listener for event: {event_type}")
    
    def remove_listener(self, event_type: str, callback: Callable) -> None:
        \"\"\"移除事件监听器\"\"\"
        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
                logger.debug(f"Removed listener for event: {event_type}")
    
    def dispatch(self, event_type: str, data: Any = None) -> None:
        \"\"\"分发事件\"\"\"
        if event_type in self._listeners:
            logger.debug(f"Dispatching event: {event_type}")
            for callback in self._listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")

# 全局事件分发器实例
event_dispatcher = EventDispatcher()
"""
    
    with open(os.path.join(project_root, "src", "core", "event_dispatcher.py"), 'w', encoding='utf-8') as f:
        f.write(event_dispatcher_content)
    
    # Logger
    logger_content = """\"\"\"
日志管理器
负责应用程序的日志配置和管理
\"\"\"

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(log_level=logging.INFO, log_file="testflow.log"):
    \"\"\"设置日志记录器\"\"\"
    # 创建日志目录
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str):
    \"\"\"获取指定名称的日志记录器\"\"\"
    return logging.getLogger(name)
"""
    
    with open(os.path.join(project_root, "src", "core", "logger.py"), 'w', encoding='utf-8') as f:
        f.write(logger_content)
    
    # State Manager
    state_manager_content = """\"\"\"
状态管理器
负责管理应用程序的全局状态
\"\"\"

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class StateManager:
    \"\"\"状态管理器\"\"\"
    
    def __init__(self):
        self._state: Dict[str, Any] = {}
    
    def set_state(self, key: str, value: Any) -> None:
        \"\"\"设置状态值\"\"\"
        self._state[key] = value
        logger.debug(f"State updated: {key} = {value}")
        
        # 发送状态变更事件
        from src.core.event_dispatcher import event_dispatcher
        event_dispatcher.dispatch("state.changed", {
            "key": key,
            "value": value
        })
    
    def get_state(self, key: str, default: Any = None) -> Any:
        \"\"\"获取状态值\"\"\"
        return self._state.get(key, default)
    
    def remove_state(self, key: str) -> None:
        \"\"\"移除状态值\"\"\"
        if key in self._state:
            del self._state[key]
            logger.debug(f"State removed: {key}")
    
    def get_all_state(self) -> Dict[str, Any]:
        \"\"\"获取所有状态\"\"\"
        return self._state.copy()

# 全局状态管理器实例
state_manager = StateManager()
"""
    
    with open(os.path.join(project_root, "src", "core", "state_manager.py"), 'w', encoding='utf-8') as f:
        f.write(state_manager_content)
    
    # Config Manager
    config_manager_content = """\"\"\"
配置管理器
负责管理应用程序的配置
\"\"\"

import configparser
import os
from typing import Any, Optional

class ConfigManager:
    \"\"\"配置管理器\"\"\"
    
    def __init__(self, config_file: str = "config/settings.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_main_config()
    
    def load_main_config(self) -> None:
        \"\"\"加载配置文件\"\"\"
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            # 创建默认配置
            self.create_default_config()
            self.save_config()
    
    def create_default_config(self) -> None:
        \"\"\"创建默认配置\"\"\"
        self.config['Paths'] = {
            'temp_dir': 'data/temp',
            'output_dir': 'data/output'
        }
        
        self.config['Application'] = {
            'name': 'TestFlow Manager',
            'version': '1.0.0'
        }
    
    def save_config(self) -> None:
        \"\"\"保存配置文件\"\"\"
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        \"\"\"获取配置值\"\"\"
        return self.config.get(section, key, fallback=fallback)
    
    def set(self, section: str, key: str, value: str) -> None:
        \"\"\"设置配置值\"\"\"
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

# 全局配置管理器实例
config_manager = ConfigManager()
"""
    
    with open(os.path.join(project_root, "src", "core", "config_manager.py"), 'w', encoding='utf-8') as f:
        f.write(config_manager_content)

def create_manager_files(project_root):
    """创建管理器文件"""
    
    # Window Manager
    window_manager_content = """\"\"\"
窗口管理器
负责管理应用程序中的窗口
\"\"\"

import logging
from typing import Dict, Type, Any

logger = logging.getLogger(__name__)

class WindowManager:
    \"\"\"窗口管理器\"\"\"
    
    def __init__(self):
        self._windows: Dict[str, Any] = {}
        self._window_factories: Dict[str, Type] = {}
    
    def register_window_type(self, window_type: str, window_class: Type) -> None:
        \"\"\"注册窗口类型\"\"\"
        self._window_factories[window_type] = window_class
        logger.debug(f"Registered window type: {window_type}")
    
    def create_window(self, window_type: str, *args, **kwargs) -> Any:
        \"\"\"创建窗口实例\"\"\"
        if window_type not in self._window_factories:
            raise ValueError(f"Unknown window type: {window_type}")
        
        window_class = self._window_factories[window_type]
        window = window_class(*args, **kwargs)
        
        # 跟踪窗口
        window_id = id(window)
        self._windows[window_id] = window
        
        logger.debug(f"Created window: {window_type} with ID {window_id}")
        return window
    
    def close_window(self, window_id: int) -> None:
        \"\"\"关闭窗口\"\"\"
        if window_id in self._windows:
            del self._windows[window_id]
            logger.debug(f"Closed window with ID {window_id}")
    
    def get_window(self, window_id: int) -> Any:
        \"\"\"获取窗口实例\"\"\"
        return self._windows.get(window_id)

# 全局窗口管理器实例
window_manager = WindowManager()
"""
    
    with open(os.path.join(project_root, "src", "managers", "window_manager.py"), 'w', encoding='utf-8') as f:
        f.write(window_manager_content)
    
    # Action Manager
    action_manager_content = """\"\"\"
操作管理器
负责管理应用程序中的操作
\"\"\"

import logging
from typing import Dict, Callable, Any

logger = logging.getLogger(__name__)

class ActionManager:
    \"\"\"操作管理器\"\"\"
    
    def __init__(self):
        self._actions: Dict[str, Callable] = {}
    
    def register_action(self, action_name: str, handler: Callable) -> None:
        \"\"\"注册操作\"\"\"
        self._actions[action_name] = handler
        logger.debug(f"Registered action: {action_name}")
    
    def execute_action(self, action_name: str, data: Any = None) -> Any:
        \"\"\"执行操作\"\"\"
        if action_name not in self._actions:
            logger.warning(f"Unknown action: {action_name}")
            return None
        
        try:
            logger.debug(f"Executing action: {action_name}")
            result = self._actions[action_name](data)
            
            # 发送操作完成事件
            from src.core.event_dispatcher import event_dispatcher
            event_dispatcher.dispatch("action.completed", {
                "action": action_name,
                "data": data,
                "result": result
            })
            
            return result
        except Exception as e:
            logger.error(f"Error executing action '{action_name}': {e}")
            
            # 发送操作错误事件
            from src.core.event_dispatcher import event_dispatcher
            event_dispatcher.dispatch("action.error", {
                "action": action_name,
                "error": str(e)
            })
            
            return {"success": False, "error": str(e)}

# 全局操作管理器实例
action_manager = ActionManager()
"""
    
    with open(os.path.join(project_root, "src", "managers", "action_manager.py"), 'w', encoding='utf-8') as f:
        f.write(action_manager_content)

def create_common_components(project_root):
    """创建通用组件"""
    
    # File Selector Widget
    file_selector_content = """\"\"\"
文件选择器组件
提供文件选择功能的通用UI组件
\"\"\"

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal

class FileSelectorWidget(QWidget):
    \"\"\"文件选择器组件\"\"\"
    
    fileSelected = pyqtSignal(str)  # 文件选择信号
    
    def __init__(self, file_filter="All Files (*)", parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        self.setup_ui()
    
    def setup_ui(self):
        \"\"\"设置界面\"\"\"
        layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.browse_button = QPushButton("浏览")
        
        self.browse_button.clicked.connect(self.browse_file)
        self.path_edit.textChanged.connect(self.on_text_changed)
        
        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)
        self.setLayout(layout)
    
    def browse_file(self):
        \"\"\"浏览文件\"\"\"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", self.file_filter
        )
        if file_path:
            self.path_edit.setText(file_path)
            self.fileSelected.emit(file_path)
    
    def set_file_path(self, file_path: str):
        \"\"\"设置文件路径\"\"\"
        self.path_edit.setText(file_path)
    
    def get_file_path(self) -> str:
        \"\"\"获取文件路径\"\"\"
        return self.path_edit.text()
    
    def on_text_changed(self, text: str):
        \"\"\"文本改变时的处理\"\"\"
        self.fileSelected.emit(text)
"""
    
    with open(os.path.join(project_root, "src", "common", "widgets", "file_selector.py"), 'w', encoding='utf-8') as f:
        f.write(file_selector_content)
    
    # File Service
    file_service_content = """\"\"\"
文件服务
提供文件操作的通用服务
\"\"\"

import os
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FileService:
    \"\"\"文件服务\"\"\"
    
    @staticmethod
    def create_directory(path: str) -> bool:
        \"\"\"创建目录\"\"\"
        try:
            os.makedirs(path, exist_ok=True)
            logger.debug(f"Created directory: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    @staticmethod
    def copy_file(source: str, destination: str) -> bool:
        \"\"\"复制文件\"\"\"
        try:
            shutil.copy2(source, destination)
            logger.debug(f"Copied file from {source} to {destination}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy file from {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def move_file(source: str, destination: str) -> bool:
        \"\"\"移动文件\"\"\"
        try:
            shutil.move(source, destination)
            logger.debug(f"Moved file from {source} to {destination}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file from {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        \"\"\"删除文件\"\"\"
        try:
            os.remove(file_path)
            logger.debug(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
"""
    
    with open(os.path.join(project_root, "src", "common", "services", "file_service.py"), 'w', encoding='utf-8') as f:
        f.write(file_service_content)

def create_util_files(project_root):
    """创建工具函数文件"""
    
    # Config Handler
    config_handler_content = """\"\"\"
配置处理工具
提供配置文件处理的工具函数
\"\"\"

import configparser
import os
from typing import Any, Optional

def get_config_value(section: str, key: str, default: Any = None, config_file: str = "config/settings.ini") -> Any:
    \"\"\"获取配置值\"\"\"
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file, encoding='utf-8')
        if config.has_section(section) and config.has_option(section, key):
            return config.get(section, key)
    return default

def set_config_value(section: str, key: str, value: str, config_file: str = "config/settings.ini") -> bool:
    \"\"\"设置配置值\"\"\"
    try:
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
        
        if not config.has_section(section):
            config.add_section(section)
        
        config.set(section, key, value)
        
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        
        return True
    except Exception as e:
        print(f"Error setting config value: {e}")
        return False
"""
    
    with open(os.path.join(project_root, "src", "utils", "config_handler.py"), 'w', encoding='utf-8') as f:
        f.write(config_handler_content)
    
    # File Utils
    file_utils_content = """\"\"\"
文件工具函数
提供文件处理的工具函数
\"\"\"

import os
import re
from typing import List

def get_file_extension(file_path: str) -> str:
    \"\"\"获取文件扩展名\"\"\"
    return os.path.splitext(file_path)[1].lower()

def sanitize_filename(filename: str) -> str:
    \"\"\"清理文件名中的非法字符\"\"\"
    invalid_chars = r'[\\/:*?"<>|]'
    return re.sub(invalid_chars, "_", filename)

def get_files_in_directory(directory: str, extensions: List[str] = None) -> List[str]:
    \"\"\"获取目录中的文件\"\"\"
    files = []
    if os.path.exists(directory):
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                if extensions is None or get_file_extension(file_path) in extensions:
                    files.append(file_path)
    return files
"""
    
    with open(os.path.join(project_root, "src", "utils", "file_utils.py"), 'w', encoding='utf-8') as f:
        f.write(file_utils_content)

def create_main_window_module(project_root):
    """创建主窗口模块"""
    
    # Main Window Data
    main_window_data_content = """\"\"\"
主窗口数据模型
负责管理主窗口的数据状态
\"\"\"

from typing import Dict, Any

class MainWindowData:
    \"\"\"主窗口数据模型\"\"\"
    
    def __init__(self):
        self._data: Dict[str, Any] = {
            "current_file": None,
            "recent_files": [],
            "application_state": "ready"
        }
    
    def set_current_file(self, file_path: str) -> None:
        \"\"\"设置当前文件\"\"\"
        self._data["current_file"] = file_path
        if file_path and file_path not in self._data["recent_files"]:
            self._data["recent_files"].insert(0, file_path)
            # 保持最近文件列表不超过10个
            self._data["recent_files"] = self._data["recent_files"][:10]
    
    def get_current_file(self) -> str:
        \"\"\"获取当前文件\"\"\"
        return self._data["current_file"]
    
    def get_recent_files(self) -> list:
        \"\"\"获取最近文件列表\"\"\"
        return self._data["recent_files"].copy()
    
    def set_application_state(self, state: str) -> None:
        \"\"\"设置应用状态\"\"\"
        self._data["application_state"] = state
    
    def get_application_state(self) -> str:
        \"\"\"获取应用状态\"\"\"
        return self._data["application_state"]
"""
    
    with open(os.path.join(project_root, "src", "features", "main_window", "model", "main_window_data.py"), 'w', encoding='utf-8') as f:
        f.write(main_window_data_content)
    
    # Main Window UI
    main_window_ui_content = """\"\"\"
主窗口UI
负责主窗口的用户界面
\"\"\"

from PyQt5.QtWidgets import QMainWindow, QAction, QMenuBar, QToolBar, QStatusBar, QTextEdit
from PyQt5.QtCore import Qt

class MainWindowUI(QMainWindow):
    \"\"\"主窗口UI\"\"\"
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TestFlow Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        \"\"\"设置界面\"\"\"
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_central_widget()
    
    def setup_menu_bar(self):
        \"\"\"设置菜单栏\"\"\"
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        new_action = QAction("新建", self)
        open_action = QAction("打开", self)
        save_action = QAction("保存", self)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        # 添加编辑菜单项
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        \"\"\"设置工具栏\"\"\"
        toolbar = self.addToolBar("主工具栏")
        # 添加工具栏项
    
    def setup_status_bar(self):
        \"\"\"设置状态栏\"\"\"
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
    
    def setup_central_widget(self):
        \"\"\"设置中央组件\"\"\"
        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)
"""
    
    with open(os.path.join(project_root, "src", "features", "main_window", "view", "main_window_ui.py"), 'w', encoding='utf-8') as f:
        f.write(main_window_ui_content)
    
    # Main Window Controller
    main_window_controller_content = """\"\"\"
主窗口控制器
负责主窗口的业务逻辑
\"\"\"

import logging
from src.features.main_window.view.main_window_ui import MainWindowUI
from src.features.main_window.model.main_window_data import MainWindowData

logger = logging.getLogger(__name__)

class MainWindowController:
    \"\"\"主窗口控制器\"\"\"
    
    def __init__(self):
        self.view = MainWindowUI()
        self.model = MainWindowData()
        self.setup_connections()
    
    def setup_connections(self):
        \"\"\"设置信号连接\"\"\"
        # 连接UI事件到处理函数
        pass
    
    def show_window(self):
        \"\"\"显示窗口\"\"\"
        self.view.show()
        logger.info("Main window shown")
    
    def handle_file_open(self, file_path: str):
        \"\"\"处理文件打开\"\"\"
        self.model.set_current_file(file_path)
        self.view.statusBar.showMessage(f"已打开文件: {file_path}")
        logger.info(f"Opened file: {file_path}")
    
    def handle_exit(self):
        \"\"\"处理退出\"\"\"
        self.view.close()
        logger.info("Application exit requested")
"""
    
    with open(os.path.join(project_root, "src", "features", "main_window", "controller", "main_window_controller.py"), 'w', encoding='utf-8') as f:
        f.write(main_window_controller_content)

def create_app_entry(project_root):
    """创建应用入口文件"""
    
    # Application
    application_content = """\"\"\"
应用程序入口
负责应用程序的初始化和启动
\"\"\"

import sys
import logging
from PyQt5.QtWidgets import QApplication

from src.core.logger import setup_logger
from src.core.config_manager import config_manager
from src.features.main_window.controller.main_window_controller import MainWindowController

class Application:
    \"\"\"应用程序\"\"\"
    
    def __init__(self):
        self.app = None
        self.main_window_controller = None
    
    def initialize(self):
        \"\"\"初始化应用程序\"\"\"
        # 设置日志
        setup_logger()
        logging.info("TestFlow Manager initializing...")
        
        # 创建Qt应用
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(
            config_manager.get("Application", "name", "TestFlow Manager")
        )
        self.app.setApplicationVersion(
            config_manager.get("Application", "version", "1.0.0")
        )
        
        # 创建主窗口控制器
        self.main_window_controller = MainWindowController()
        
        logging.info("TestFlow Manager initialized")
    
    def run(self):
        \"\"\"运行应用程序\"\"\"
        if not self.app:
            self.initialize()
        
        # 显示主窗口
        self.main_window_controller.show_window()
        
        # 运行事件循环
        logging.info("TestFlow Manager started")
        return self.app.exec_()
    
    def shutdown(self):
        \"\"\"关闭应用程序\"\"\"
        logging.info("TestFlow Manager shutting down...")

def main():
    \"\"\"主函数\"\"\"
    app = Application()
    try:
        exit_code = app.run()
        sys.exit(exit_code)
    except Exception as e:
        logging.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
    
    with open(os.path.join(project_root, "src", "app", "application.py"), 'w', encoding='utf-8') as f:
        f.write(application_content)
    
    # Main entry point
    main_content = """\"\"\"
TestFlow Manager 主入口点
\"\"\"

from src.app.application import main

if __name__ == "__main__":
    main()
"""
    
    with open(os.path.join(project_root, "src", "main.py"), 'w', encoding='utf-8') as f:
        f.write(main_content)

def print_project_structure(root_path, prefix="", is_last=True):
    """打印项目结构"""
    if not os.path.exists(root_path):
        return
    
    dir_name = os.path.basename(root_path)
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{dir_name}")
    
    if os.path.isdir(root_path):
        items = sorted(os.listdir(root_path))
        for i, item in enumerate(items):
            item_path = os.path.join(root_path, item)
            is_last_item = (i == len(items) - 1)
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            if os.path.isdir(item_path):
                print_project_structure(item_path, new_prefix, is_last_item)
            else:
                file_connector = "└── " if is_last_item else "├── "
                print(f"{new_prefix}{file_connector}{item}")

if __name__ == "__main__":
    # 如果作为脚本运行，创建项目
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
        create_project_structure(project_name)
    else:
        create_project_structure("TestFlowManager")
