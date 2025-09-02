"""
TestFlow Manager 项目架构生成器
用于生成符合MVCS架构的Python项目结构
"""

import os
import sys


def create_project_structure(project_name=None, base_path="."):
    """
    创建项目架构
    如果未提供项目名称，则在当前目录下直接创建项目结构
    """
    if project_name:
        project_root = os.path.join(base_path, project_name)
    else:
        # 如果没有提供项目名称，则使用当前目录作为项目根目录
        project_root = os.path.abspath(base_path)

    # 创建项目根目录
    os.makedirs(project_root, exist_ok=True)

    # 定义项目结构
    structure = {
        "": [  # 根目录
            "README.md",
            "requirements.txt",
            "setup.py",
            "__init__.py"
        ],
        "config": [
            "__init__.py",
            "settings.ini"
        ],
        "src": {
            "__init__.py": None,
            "app": [
                "__init__.py",
                "application.py"
            ],
            "core": [
                "__init__.py",
                "event_dispatcher.py",
                "logger.py",
                "state_manager.py",
                "config_manager.py"
            ],
            "managers": [
                "__init__.py",
                "window_manager.py",
                "action_manager.py"
            ],
            "common": {
                "__init__.py": None,
                "widgets": [
                    "__init__.py",
                    "file_selector.py",
                    "custom_dialog.py",
                    "date_edit.py"
                ],
                "services": [
                    "__init__.py",
                    "file_service.py",
                    "notification_service.py"
                ],
                "exceptions": [
                    "__init__.py",
                    "validation_error.py"
                ]
            },
            "utils": [
                "__init__.py",
                "config_handler.py",
                "file_utils.py",
                "log_handler.py",
                "string_utils.py",
                "date_utils.py"
            ],
            "features": {
                "__init__.py": None,
                "main_window": {
                    "__init__.py": None,
                    "model": [
                        "__init__.py",
                        "main_window_data.py"
                    ],
                    "view": {
                        "__init__.py": None,
                        "components": [
                            "__init__.py"
                        ],
                        "dialogs": [
                            "__init__.py"
                        ],
                        "main_window_ui.py": None
                    },
                    "controller": [
                        "__init__.py",
                        "main_window_controller.py"
                    ],
                    "service": [
                        "__init__.py",
                        "main_window_service.py"
                    ]
                }
            }
        },
        "tests": [
            "__init__.py",
            "test_example.py"
        ],
        "docs": [
            "design.md",
            "api_reference.md"
        ]
    }

    # 创建目录结构和文件
    create_structure(project_root, structure)

    # 创建核心文件内容
    create_core_files(project_root)

    if project_name:
        print(f"TestFlow Manager 项目架构已创建: {project_root}")
    else:
        print(f"TestFlow Manager 项目架构已创建于当前目录: {project_root}")
    print("\n项目结构:")
    print_project_structure(project_root)


def create_structure(base_path, structure):
    """递归创建目录结构"""
    for key, value in structure.items():
        path = os.path.join(base_path, key) if key else base_path

        if value is None:
            # 创建文件
            if not os.path.exists(path):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("")
        elif isinstance(value, list):
            # 创建目录和其中的文件
            os.makedirs(path, exist_ok=True)
            for item in value:
                item_path = os.path.join(path, item)
                if '.' in item or item == "__init__.py":
                    # 创建文件
                    with open(item_path, 'w', encoding='utf-8') as f:
                        f.write("")
                else:
                    # 创建子目录
                    os.makedirs(item_path, exist_ok=True)
        elif isinstance(value, dict):
            # 递归创建子结构
            os.makedirs(path, exist_ok=True)
            create_structure(path, value)


def create_core_files(project_root):
    """创建核心文件内容"""

    # 创建 README.md
    readme_content = """# TestFlow Manager

TestFlow Manager 是一个用于管理测试流程的工具，专注于处理测试申请单、邮件通信和相关文档管理。

## 项目结构

本项目采用MVCS架构模式（Model-View-Controller-Service）：

- **Model**: 数据模型层
- **View**: 视图层，负责界面展示
- **Controller**: 控制层，处理业务逻辑
- **Service**: 服务层，处理具体业务操作

### 目录说明

- `src/`: 源代码目录
  - `app/`: 应用程序入口
  - `core/`: 核心组件（事件分发器、日志、状态管理等）
  - `managers/`: 各种管理器
  - `common/`: 公共组件
    - `widgets/`: 自定义控件
    - `services/`: 公共服务
    - `exceptions/`: 自定义异常
  - `utils/`: 工具类
  - `features/`: 功能模块
- `tests/`: 测试代码
- `docs/`: 文档
- `config/`: 配置文件
"""

    readme_path = os.path.join(project_root, "README.md")
    # 总是写入 README.md 内容，不管文件是否已存在
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    # 创建 requirements.txt
    requirements_content = """PyQt5>=5.15.0
requests>=2.25.0
"""

    requirements_path = os.path.join(project_root, "requirements.txt")
    # 总是写入 requirements.txt 内容，不管文件是否已存在
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write(requirements_content)

    # 创建 setup.py
    setup_content = """from setuptools import setup, find_packages

setup(
    name="testflow-manager",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyQt5>=5.15.0",
        "requests>=2.25.0",
    ],
    entry_points={
        'console_scripts': [
            'testflow-manager=app.application:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for managing test workflows",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/testflow-manager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
"""

    setup_path = os.path.join(project_root, "setup.py")
    # 总是写入 setup.py 内容，不管文件是否已存在
    with open(setup_path, 'w', encoding='utf-8') as f:
        f.write(setup_content)

    # 创建 __init__.py 文件
    init_paths = [
        os.path.join(project_root, "__init__.py"),
        os.path.join(project_root, "src", "__init__.py")
    ]

    for init_path in init_paths:
        # 只有当 __init__.py 文件不存在时才创建（避免覆盖可能存在的内容）
        if not os.path.exists(init_path):
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write("")



def print_project_structure(root_path, prefix="", is_last=True):
    """打印项目结构"""
    if not os.path.exists(root_path):
        return

    # 获取目录中的所有项目
    try:
        items = sorted(os.listdir(root_path))
    except PermissionError:
        return

    # 过滤掉隐藏文件（以.开头的文件）
    items = [item for item in items if not item.startswith('.')]

    for i, item in enumerate(items):
        item_path = os.path.join(root_path, item)
        is_last_item = (i == len(items) - 1)

        # 打印当前项目
        if is_last_item:
            print(f"{prefix}└── {item}")
            new_prefix = f"{prefix}    "
        else:
            print(f"{prefix}├── {item}")
            new_prefix = f"{prefix}│   "

        # 如果是目录，递归打印其内容
        if os.path.isdir(item_path):
            print_project_structure(item_path, new_prefix, is_last_item)


if __name__ == "__main__":
    # 如果提供了命令行参数，则使用它作为项目名称
    # 否则在当前目录下创建项目结构
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
        create_project_structure(project_name)
    else:
        # 在当前目录下创建项目结构
        create_project_structure()
