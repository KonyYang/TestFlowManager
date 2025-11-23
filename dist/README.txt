# TestFlow Manager

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
    - `email_extractor/`: 邮件提取模块
    - `project_creator/`: 项目创建模块
    - `ltr_manager/`: LTR管理模块
    - `folder_manager/`: 文件夹管理模块
    - `document_parser/`: 文档解析模块
- `tests/`: 测试代码
- `docs/`: 文档
- `config/`: 配置文件

## 核心功能

1. **邮件处理**：支持从Outlook或MSG文件中提取邮件和附件
2. **文档解析**：自动解析Word格式的测试申请单
3. **项目管理**：基于申请单信息创建标准化项目结构
4. **LTR编号管理**：生成和管理LTR测试申请编号

## 开发环境搭建

1. 安装 Python 3.7 或更高版本
2. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```
3. 运行应用程序：
   ```
   python -m src.app.application
   ```

## 构建可执行文件

要构建 Windows 可执行文件，请执行以下步骤：

1. 安装 PyInstaller：
   ```
   pip install pyinstaller
   ```

2. 运行构建脚本：
   ```
   python build_executable.py
   ```

3. 构建完成后，所有必要的文件将位于 `dist/` 目录中，包括：
   - TestFlowManager.exe: 主程序文件
   - config/: 配置文件目录
   - Template/: 模板文件目录
   - Projects/: 项目文件目录
   - Temp/: 临时文件目录
   - logs/: 日志文件目录
   - start.bat: 启动脚本
   - README.txt: 使用说明

4. 将整个 `dist/` 目录复制到目标计算机即可使用，无需安装 Python 环境。

## 配置说明

配置文件位于 `config/` 目录中：

1. `paths.ini`: 路径配置文件
   - ltr_file: LTR文件路径（相对于可执行文件目录）
   - ltr_password: LTR文件密码
   - project_leader: 默认项目负责人

2. `settings.json`: 主配置文件
   - 应用程序基本配置
   - 窗口大小和位置
   - 日志配置等

在可执行文件模式下，配置文件会从可执行文件所在目录加载，确保程序在任何位置都能正确运行。

## 开发指南

详细开发指南请参考 [develope.md](develope.md) 文件，其中包含：
- 架构设计原则
- 代码规范
- 模块开发指导
- 测试策略