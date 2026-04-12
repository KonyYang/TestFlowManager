# TestFlowManager - 测试流程管理系统

> **版本**: 1.0.0  
> **最后更新**: 2026-04-07  
> **状态**: 活跃开发中

## 项目概述

TestFlowManager 是一款面向测试流程管理的桌面应用程序，运行于 Windows 平台。它通过自动化文档处理、测试矩阵管理和项目全生命周期管理，大幅提升测试团队的工作效率。

### 核心职责

- **自动化文档处理**: 通过 Windows COM 接口操控 Word/Excel/Outlook，实现报告生成、格式化与分发
- **测试矩阵管理**: 维护测试矩阵数据，支持多种格式导出（LLCRCR、FeeSheet、IRDWV、MatingUnmating 等）
- **项目全生命周期管理**: 从项目创建、文件夹结构搭建，到邮件提取、报告生成的完整工作流
- **标准文档版本追踪**: 解析测试规范文档，提取版本信息，维护标准文件路径映射

## 技术栈

| 类别 | 技术/库 | 版本要求 | 用途 |
|------|---------|---------|------|
| GUI 框架 | PyQt5 | ≥ 5.15.0 | 桌面 UI 组件、信号槽通信 |
| COM 自动化 | pywin32 | ≥ 227 | Word/Excel/Outlook 自动化 |
| Word 文档 | python-docx | ≥ 0.8.10 | .docx 文件读写（非 COM 路径） |
| Excel 文档 | openpyxl | ≥ 3.0.7 | .xlsx 文件读写（非 COM 路径） |
| 数据处理 | pandas | ≥ 1.3.0 | 表格数据处理与变换 |
| Excel 读取 | xlrd | ≥ 2.0.1 | 旧版 .xls 文件兼容读取 |
| HTTP | requests | ≥ 2.25.0 | 外部接口调用 |
| 打包工具 | PyInstaller | ≥ 4.0 | 编译为独立 .exe 可执行文件 |
| 测试框架 | pytest | ≥ 6.0 | 单元测试和集成测试 |
| 运行时 | Python | ≥ 3.12 | 应用运行时环境 |

## 整体架构

TestFlowManager 采用 **分层 MVCS 架构**（Model-View-Controller-Service），各层职责清晰分离：

```
┌─────────────────────────────────────────────────────────────┐
│                    应用入口层                                  │
│         src/app/application.py  (QApplication + main)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      视图层 (View)                             │
│          PyQt5 UI 组件 / QWidget / QDialog / QTableWidget     │
│          负责界面展示，通过信号触发 Controller 方法             │
└──────────────────────────┬──────────────────────────────────┘
                           │ 信号/槽
┌──────────────────────────▼──────────────────────────────────┐
│                    控制器层 (Controller)                        │
│          协调流程、处理用户交互、调用 Service 方法              │
│          订阅/发布 EventDispatcher 事件                        │
└──────────────────────────┬──────────────────────────────────┘
                           │ 方法调用
┌──────────────────────────▼──────────────────────────────────┐
│                     服务层 (Service)                           │
│          继承 BaseService，实现所有业务逻辑                     │
│          通过 ConfigManager 读取配置，写入日志                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ 访问
┌──────────────────────────▼──────────────────────────────────┐
│                      模型层 (Model)                            │
│          @dataclass 数据结构，无业务逻辑，仅数据承载            │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                     核心基础设施层 (Core)                       │
│   ConfigManager  │  EventDispatcher  │  StateManager          │
│   Logger         │  BaseService      │  Exceptions            │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    工具与 COM 层 (Utils)                        │
│   word_utils  │  excel_utils  │  email_utils  │  file_utils   │
│   pdf_utils   │  date_utils   │  string_utils │  template_utils│
└─────────────────────────────────────────────────────────────┘
```

### 架构特点

- **松耦合设计**: 通过 EventDispatcher 实现模块间通信，避免直接依赖
- **可测试性**: Service 层不依赖 UI，易于编写单元测试
- **可维护性**: 清晰的层次划分，代码职责单一
- **可扩展性**: 标准化模块结构，便于添加新功能

## 目录结构

```
TestFlowManager/
├── src/                              # 源代码目录
│   ├── app/                          # 应用程序入口
│   │   ├── application.py            # 应用主入口，QApplication 初始化
│   │   └── resources/                # 应用资源（图标、图片等）
│   ├── core/                         # 核心基础设施
│   │   ├── base_service.py         # 服务基类 (ABC)
│   │   ├── config_manager.py       # 全局配置管理器单例
│   │   ├── event_dispatcher.py     # 全局事件分发器单例
│   │   ├── state_manager.py        # 全局状态管理器单例
│   │   └── logger.py               # 全局日志记录器
│   ├── managers/                     # 管理器模块
│   │   ├── action_manager.py       # 操作管理器
│   │   └── window_manager.py       # 窗口管理器
│   ├── common/                       # 公共组件
│   │   ├── exceptions/             # 自定义异常类
│   │   ├── services/               # 跨模块共享服务
│   │   └── widgets/                # 通用 UI 组件
│   ├── utils/                        # 通用工具层
│   │   ├── com_base.py             # COM 基类
│   │   ├── word_utils.py           # Word COM 操作封装
│   │   ├── excel_utils.py          # Excel COM 操作封装
│   │   ├── email_utils.py          # Outlook COM 操作封装
│   │   ├── file_utils.py           # 文件系统操作
│   │   ├── date_utils.py           # 日期格式化工具
│   │   ├── string_utils.py         # 字符串处理工具
│   │   └── ...                     # 其他工具函数
│   └── features/                     # 功能模块（13个）
│       ├── main_window/            # 主窗口框架
│       ├── project_creator/        # 项目创建器
│       ├── email_extractor/        # 邮件提取器
│       ├── ltr_manager/            # LTR 管理器
│       ├── folder_manager/         # 文件夹管理器
│       ├── matrix/                 # 矩阵管理器（最大模块）
│       ├── report_wizard/          # 报告向导
│       ├── report_updater/         # 报告更新器
│       ├── content_editor/         # 内容编辑器
│       ├── document_parser/        # 文档解析器
│       ├── customer_report_generator/  # 客户报告生成器
│       ├── file_encryption/        # 文件加密
│       └── step_record_generator/  # 步骤记录生成器
│   ├── app/
│   │   └── config/                 # 开发态配置目录
│   │      ├── settings.json        # 主配置（JSON 格式）
│   │      └── paths.ini            # 路径与密码配置（INI 格式）
├── tests/                          # 单元/集成测试
├── docs/                           # 项目文档
├── logs/                           # 日志文件
├── build/                          # PyInstaller 构建中间产物
├── dist/                           # 打包输出目录
├── requirements.txt                # Python 依赖清单
├── pytest.ini                      # pytest 配置
└── TestFlowManager.spec            # PyInstaller 打包配置
```

每个功能模块内部结构统一如下：

```
feature_name/
├── __init__.py
├── model/           # @dataclass 数据模型
├── view/            # PyQt5 UI 组件
├── controller/      # 流程控制器
└── service/         # 业务逻辑服务
```

## 核心基础设施详解

### 1. ConfigManager – 配置管理器

**文件**: `src/core/config_manager.py`  
**实例**: `config_manager`（全局单例）

ConfigManager 负责在应用启动时加载所有配置，并在运行时提供统一的配置访问接口。

**配置来源**：

| 文件 | 格式 | 内容 |
|------|------|------|
| `src/app/config/settings.json` | JSON | 主配置：app 元信息、窗口参数、日志级别等 |
| `src/app/config/paths.ini` | INI | 路径映射、密码、默认值、设备数据源配置 |

**核心 API**：

```python
config_manager.get("paths.ltr_file")           # 点号分隔的嵌套键访问
config_manager.get("app.version", "1.0.0")     # 带默认值查询
config_manager.set("key", value)                # 运行时写入配置
config_manager.save_config()                    # 持久化到 JSON 文件
```

**路径解析策略**：ConfigManager 会根据运行模式自动调整路径：
- **开发模式**（`sys.frozen == False`）：以项目根目录为基准解析相对路径
- **打包模式**（`sys.frozen == True`）：优先查找生产环境路径 `D:\TestFlowManager\config\`，降级到 `.exe` 所在目录下的 `config\`

### 2. EventDispatcher – 事件分发器

**文件**: `src/core/event_dispatcher.py`  
**实例**: `event_dispatcher`（全局单例）

实现**观察者模式（Observer Pattern）**，用于模块间的松耦合异步通信。

**核心 API**：

```python
# 订阅事件
event_dispatcher.subscribe("project.created", callback_fn)

# 发布事件（支持任意参数）
event_dispatcher.dispatch("project.created", project_id=123)

# 取消订阅
event_dispatcher.unsubscribe("project.created", callback_fn)
```

**事件命名约定**：采用 `<模块>.<动作>` 的命名格式，例如 `state.changed`、`project.created`、`matrix.exported`。

### 3. StateManager – 状态管理器

**文件**: `src/core/state_manager.py`  
**实例**: `state_manager`（全局单例）

提供**响应式状态存储**，当状态发生变化时自动通过 EventDispatcher 广播事件。

**核心 API**：

```python
# 写入状态（自动广播 state.changed 事件）
state_manager.set_state("current_project", project_obj)

# 读取状态
project = state_manager.get_state("current_project")

# 针对特定 key 注册监听器
state_manager.add_listener("current_project", on_project_changed)

# 移除状态
state_manager.remove_state("current_project")
```

### 4. BaseService – 服务基类

**文件**: `src/core/base_service.py`

所有 Service 类的抽象基类，强制实现 `initialize()` 方法，并提供以下通用能力：

**日志方法**：自动加入服务名前缀

```python
self.log_info("操作完成")      # 输出: [MyService] 操作完成
self.log_debug("调试信息")
self.log_warning("警告信息")
self.log_error("错误信息")
```

**配置访问快捷方法**：

```python
self.get_config_value("app.version")           # 通用配置获取
self.get_path_config("template_dir")           # 获取路径配置
self.get_default_value("project_leader")       # 获取默认值
```

**异常工厂方法**：

```python
raise self.handle_processing_error("处理失败", operation="export")
raise self.handle_configuration_error("配置缺失", config_key="paths.template")
raise self.handle_file_operation_error("文件不存在", file_path=path)
```

**继承规范**：

```python
class MyService(BaseService):
    def __init__(self):
        super().__init__("MyService")   # 传入服务名用于日志标识

    def initialize(self) -> bool:
        # 初始化资源（加载文件、验证配置等）
        return True
```

## 功能模块详解

### 1. main_window – 主窗口

**路径**: `src/features/main_window/`  
**规模**: 23 个 Python 文件

主窗口是整个应用的 UI 框架，负责：
- 集成所有功能模块的入口标签页（Tab）
- 响应顶级菜单操作（文件、视图、工具、帮助）
- 在应用启动时初始化各子模块控制器
- 处理窗口关闭事件，触发 COM 资源清理

### 2. project_creator – 项目创建器

**路径**: `src/features/project_creator/`  
**规模**: 10 个 Python 文件

负责从头创建一个新的测试项目：
- 根据项目模板复制目录结构和初始文件
- 初始化 Excel 测试矩阵文件
- 创建项目配置文件，写入项目元数据
- 通过 EventDispatcher 广播 `project.created` 事件

### 3. email_extractor – 邮件提取器

**路径**: `src/features/email_extractor/`  
**规模**: 9 个 Python 文件

通过 Outlook COM 接口提取邮件内容：
- 读取 `.msg` 格式邮件附件
- 解析邮件正文中的测试相关数据字段
- 将提取结果写入矩阵或 Excel 文件
- 支持批量处理模式

### 4. ltr_manager – LTR 管理器

**路径**: `src/features/ltr_manager/`  
**规模**: 25 个 Python 文件

LTR（测试请求单/实验室测试报告）管理器：
- 解析 LTR 文档，提取测试项目信息
- 维护 LTR 与测试项目的关联映射
- 支持 LTR 数据的查询、更新和导出
- 提供跨模块的 LTR 数据访问接口

### 5. folder_manager – 文件夹管理器

**路径**: `src/features/folder_manager/`  
**规模**: 7 个 Python 文件

管理测试项目的文件夹结构：
- 创建/校验标准化的项目目录树
- 在文件资源管理器中打开指定目录
- 扫描已有项目文件夹，导入历史项目
- 监听 `project.created` 事件自动创建对应文件夹

### 6. matrix – 矩阵管理器（核心模块）

**路径**: `src/features/matrix/`  
**规模**: 69 个 Python 文件

测试矩阵是系统的核心数据载体，负责全生命周期管理：

**子模块结构**：

```
matrix/service/
├── base/               # 矩阵服务基类
├── defaults/           # 默认值填充策略
├── document_parsers/   # 规范文档解析器
├── export/             # 导出服务（22 个文件）
│   ├── LLCRCRExportService          # LLCRCR 格式导出
│   ├── FeeSheetExportService        # 费用表格导出
│   ├── IRDWVExportService           # IRDWV 格式导出
│   ├── MatingUnmatingExportService  # 插拔测试数据导出
│   ├── TestStatusExportService      # 测试状态汇总导出
│   └── ...                          # 其他导出格式
├── processing/         # 矩阵数据处理
├── spec/               # 测试规范版本提取
└── template/           # 矩阵模板管理
```

**核心服务**：
- `matrix_service.py`: 矩阵主服务，协调所有子服务
- `matrix_cell_service.py`: 单元格级别的读写与格式化
- `matrix_initializer.py`: 新建矩阵的初始化工作

### 7. report_wizard – 报告向导

**路径**: `src/features/report_wizard/`  
**规模**: 23 个 Python 文件

报告向导是最复杂的文档生成模块：
- 引导用户逐步完成测试报告配置
- 从 Word 测试规范文档中提取表格数据
- 自动填充测试结果、日期、设备信息等字段
- 通过 COM 操作 Word，应用复杂格式
- 生成最终的 `.docx` 测试报告文件

### 8. report_updater – 报告更新器

**路径**: `src/features/report_updater/`  
**规模**: 9 个 Python 文件

对已生成的测试报告进行增量更新：
- 比较新旧版本规范文档，识别变更内容
- 在已有报告的指定位置插入/替换测试条目
- 保留原有格式和批注，仅更新内容部分
- 支持批量更新多份报告

### 9. content_editor – 内容编辑器

**路径**: `src/features/content_editor/`  
**规模**: 9 个 Python 文件

提供报告内容的可视化编辑界面：
- 嵌入式富文本编辑组件
- 与 Word 文档双向同步
- 支持段落样式快速应用
- 保存编辑历史，支持撤销操作

### 10. document_parser – 文档解析器

**路径**: `src/features/document_parser/`  
**规模**: 8 个 Python 文件

通用文档解析服务，被多个模块复用：
- 解析 Word 文档中的表格、段落、标题
- 提取结构化数据（测试项目编号、描述、验收条件等）
- 支持规范文档版本自动识别
- 输出标准化的 Python 数据结构

### 11. customer_report_generator – 客户报告生成器

**路径**: `src/features/customer_report_generator/`  
**规模**: 11 个 Python 文件

面向对外交付场景生成客户报告：
- 从内部测试报告中提取摘要和关键结论
- 应用客户专用模板和样式
- 支持多语言输出（中英文切换）
- 生成带封面和目录的完整 Word 文档

### 12. file_encryption – 文件加密

**路径**: `src/features/file_encryption/`  
**规模**: 3 个 Python 文件

对敏感文档进行加密保护：
- 对 Word/Excel 文件设置密码保护（通过 COM 接口）
- 管理加密密码（从 `src/app/config/paths.ini [Passwords]` 读取，打包态读取生产配置）
- 支持批量加密/解密操作

### 13. step_record_generator – 步骤记录生成器

**路径**: `src/features/step_record_generator/`  
**规模**: 7 个 Python 文件

生成标准化的测试步骤记录文档：
- 从矩阵数据中读取测试执行步骤
- 按规定格式填写步骤记录表
- 自动填充测试设备、环境条件、操作人员信息
- 支持一键生成整套步骤记录包

## 核心数据流

### 1. 新建项目流程

```
用户点击"新建项目"按钮
        │
        ▼
ProjectCreatorView (PyQt5)
  └─ 触发 on_create_clicked 信号
        │
        ▼
ProjectCreatorController
  ├─ 调用 ProjectCreatorService.validate_inputs()
  │       └─ 校验项目编号格式、路径有效性
  │
  ├─ 调用 ProjectCreatorService.create_project_structure()
  │       ├─ 复制模板目录树 (file_utils)
  │       ├─ 初始化 Excel 矩阵文件 (MatrixInitializer)
  │       └─ 写入项目元数据 JSON
  │
  ├─ 调用 FolderManagerService.create_folders()
  │       └─ 创建标准化子目录结构
  │
  └─ 广播 event_dispatcher.dispatch("project.created", project_id)
          │
          ├─ StateManager.set_state("current_project", project)
          ├─ MainWindow 更新标题和状态栏
          └─ LtrManager 更新 LTR 关联
```

### 2. 报告生成流程

```
用户启动"报告向导"
        │
        ▼
ReportWizardView – 多步骤向导 UI
  步骤1: 选择项目 & 报告模板
  步骤2: 选择要包含的测试章节
  步骤3: 配置测试人员、设备信息
  步骤4: 确认生成
        │
        ▼
ReportWizardController
  ├─ 调用 DocumentParser.parse_spec_document()
  │       └─ 读取 Word 测试规范，提取所有测试表格
  │
  ├─ 调用 TestSpecTablesService.build_report_tables()
  │       ├─ 按选定章节过滤测试条目
  │       └─ 与矩阵数据关联，填入测试结果
  │
  ├─ 调用 word_utils.apply_template()
  │       └─ 打开 Word 模板，替换占位符变量
  │
  ├─ 插入处理后的测试表格 (Word COM)
  │
  └─ 调用 word_utils.save_document(output_path)
          └─ 保存为最终 .docx 报告文件
```

### 3. Matrix 导出流程

```
用户选择导出格式（如 LLCRCR）
        │
        ▼
MatrixView → MatrixController
        │
        ▼
MatrixService.export(format="LLCRCR")
  ├─ LLCRCRTableStructureService.build_structure()
  │       └─ 从矩阵数据构建表格骨架
  │
  ├─ LLCRCRSpecSummaryService.generate_summary()
  │       └─ 提取规范摘要信息
  │
  ├─ LLCRCRFormulaService.inject_formulas()
  │       └─ 写入 Excel 计算公式
  │
  ├─ LLCRCRStylingService.apply_styles()
  │       └─ 应用单元格颜色、字体、边框
  │
  ├─ ExcelFormattingService.finalize()
  │       └─ 列宽自适应、冻结窗格、页眉页脚
  │
  └─ excel_utils.save_workbook(output_path)
          └─ 保存 .xlsx 导出文件
```

## 配置系统

应用使用双文件配置体系：

### `src/app/config/settings.json` – 主配置

```json
{
    "app": {
        "name": "TestFlowManager",
        "version": "1.0.0",
        "debug": false
    },
    "window": {
        "width": 1200,
        "height": 800,
        "position_x": 100,
        "position_y": 100
    },
    "logging": {
        "level": "INFO",
        "file": "logs/testflow.log",
        "max_bytes": 10485760,
        "backup_count": 5
    },
    "paths": {
        "template_dir": "templates/",
        "output_dir": "output/"
    },
    "defaults": {
        "project_leader": "张三",
        "test_lab": "上海实验室"
    }
}
```

### `src/app/config/paths.ini` – 路径与敏感配置

```ini
[Paths]
ltr_file = D:\Projects\LTR\ltr_database.xlsx

[STANDARD_FILES]
iec_62368 = D:\Standards\IEC62368-1_2018.docx
en_55032 = D:\Standards\EN55032_2015.docx

[Passwords]
report_password = ****
matrix_password = ****

[Defaults]
project_leader = 张三
test_lab = 上海实验室

[EquipmentDataSources]
oscilloscope = D:\Equipment\osc_data.xlsx
```

### 配置读取示例

```python
# 在 Service 中（推荐）
template_dir = self.get_path_config("template_dir")
leader = self.get_default_value("project_leader")

# 在任意位置
from src.core.config_manager import config_manager
ltr_path = config_manager.get("paths.ltr_file")
password = config_manager.get("passwords.report_password")
```

## COM 自动化层

### Word COM

通过 `src/utils/word_utils.py` 封装：

- 启动/复用 Word 进程
- 打开、创建、另存为、关闭文档
- 查找并替换文本（支持正则）
- 遍历表格、读写单元格内容
- 应用段落样式
- 打印/导出为 PDF
- 设置文档密码保护

**资源管理**：应用退出时调用 `word_utils.cleanup_word_resources()` 确保 Word 进程被正确关闭。

### Excel COM

通过 `src/utils/excel_utils.py` 封装：

- 启动/复用 Excel 进程
- 读写单元格（支持范围操作）
- 写入公式
- 应用条件格式和单元格样式
- 自动调整列宽、行高
- 保护/解除保护工作表

**资源管理**：应用退出时调用 `excel_utils.release_excel_app()` 释放 COM 引用。

### Outlook COM

通过 `src/utils/email_utils.py` 封装：

- 遍历指定邮件夹
- 读取邮件主题、正文、附件
- 解析 `.msg` 格式邮件文件
- 下载附件

## 开发指南

### 环境搭建

1. **克隆项目**

```bash
git clone <repository-url>
cd TestFlowManager
```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境**

开发态直接使用 `src/app/config/settings.json` 与 `src/app/config/paths.ini`。

### 运行应用

#### 开发模式

```bash
python src/app/application.py
```

#### 生产模式（打包）

```bash
# 使用打包脚本
python build_executable.py

# 或直接调用 PyInstaller
pyinstaller TestFlowManager.spec
```

打包输出位于 `dist/` 目录，生成独立的 `.exe` 可执行文件。

### 添加新功能模块

1. **创建模块目录结构**

```bash
src/features/new_feature/
├── __init__.py
├── model/
│   ├── __init__.py
│   └── new_feature_model.py
├── view/
│   ├── __init__.py
│   └── new_feature_ui.py
├── controller/
│   ├── __init__.py
│   └── new_feature_controller.py
└── service/
    ├── __init__.py
    └── new_feature_service.py
```

2. **实现 Service 层**

```python
from src.core.base_service import BaseService

class NewFeatureService(BaseService):
    def __init__(self):
        super().__init__("NewFeatureService")

    def initialize(self) -> bool:
        self.log_info("初始化 NewFeature 服务")
        return True

    def do_something(self, data):
        try:
            # 获取配置
            config_value = self.get_config_value("some.key")
            
            # 业务逻辑
            result = self._process_data(data)
            self.log_info("数据处理完成")
            return result
        except Exception as e:
            raise self.handle_processing_error(f"处理失败: {str(e)}", "do_something")
```

3. **实现 Controller 层**

```python
from src.core.base_controller import BaseController

class NewFeatureController(BaseController):
    def __init__(self, parent=None):
        super().__init__()
        self.service = NewFeatureService()
        self.view = NewFeatureView()
        self.setup_connections()
        
    def setup_connections(self):
        self.view.some_button.clicked.connect(self.handle_some_action)
        
    def handle_some_action(self):
        try:
            data = self.view.get_input_data()
            result = self.service.do_something(data)
            self.view.show_result(result)
        except Exception as e:
            self.show_error_message("操作失败", str(e))
```

4. **集成到主窗口**

在 `src/features/main_window/controller/main_window_controller.py` 中注册新功能：

```python
from src.features.new_feature.controller.new_feature_controller import NewFeatureController

class MainWindowController:
    def __init__(self, main_window):
        super().__init__()
        self.new_feature_controller = NewFeatureController(main_window)
        self.setup_tab_integrations()
        
    def setup_tab_integrations(self):
        # 添加新功能标签页
        self.main_window.add_tab(
            self.new_feature_controller.view,
            "新功能",
            QIcon(":/icons/new_feature.png")
        )
```

### 使用 EventDispatcher 通信

**订阅事件**：

```python
from src.core.event_dispatcher import event_dispatcher

def on_project_created(event_data):
    project_id = event_data.get("project_id")
    self.log_info(f"收到项目创建事件: {project_id}")
    # 处理逻辑

# 订阅事件
event_dispatcher.subscribe("project.created", on_project_created)
```

**发布事件**：

```python
# 发布事件
event_dispatcher.dispatch("new_feature.completed", {
    "result": result_obj,
    "timestamp": datetime.now()
})
```

## 性能优化

### 已实施的优化

1. **Word COM 解析器优化**
   - 实现文档缓存机制，避免重复解析
   - 优化关键字搜索算法，减少遍历次数
   - 批量操作减少 COM 调用次数

2. **缓存机制**
   - Matrix 导出结果缓存
   - 文档解析结果缓存
   - 配置数据缓存

3. **延迟加载**
   - 控制器延迟初始化，缩短启动时间
   - 服务按需加载，减少内存占用

4. **资源管理**
   - 应用退出时清理 COM 资源
   - 自动垃圾回收优化

### 性能数据

根据性能测试文档，优化后预期性能提升：

| 优化项 | 预期性能提升 | 影响范围 |
|--------|------------|----------|
| Word 解析器优化 | 50-70% | 文档导入、测试方法提取 |
| 缓存机制 | 30-50% | 数据导出、重复操作 |
| 延迟加载 | 20-30% | 应用启动时间 |
| 并行处理 | 30-40% | 测试方法提取 |

## 测试策略

### 测试结构

```
tests/
├── unit/               # 单元测试
│   ├── test_services/
│   ├── test_utils/
│   └── test_models/
├── integration/        # 集成测试
│   ├── test_matrix_export/
│   └── test_report_generation/
└── conftest.py         # pytest 配置
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成测试报告
pytest --html=reports/test_report.html --self-contained-html
```

### 测试覆盖率目标

- **单元测试**: 覆盖率 ≥ 80%
- **集成测试**: 覆盖核心业务流程
- **手动测试**: 覆盖所有 UI 交互场景

## 打包与部署

### 生产环境部署约定

1. 将 `.exe` 文件部署到目标机器 `D:\TestFlowManager\`
2. 打包态可在 `D:\TestFlowManager\config\` 目录下放置本地化配置文件
3. 配置文件无需重新打包即可调整

### 部署目录结构

```
D:\TestFlowManager\
├── TestFlowManager.exe      # 主程序
├── config/                  # 打包态配置文件目录
│   ├── settings.json
│   └── paths.ini
├── templates/               # 模板文件
├── logs/                    # 日志文件
└── resources/               # 资源文件
```

## 设计模式

| 模式 | 应用位置 | 说明 |
|------|---------|------|
| 单例模式 (Singleton) | ConfigManager、EventDispatcher、StateManager | 全局唯一实例 |
| 观察者模式 (Observer) | EventDispatcher + StateManager | 模块间松耦合通信 |
| 工厂方法 (Factory Method) | `create_main_window()` | 主窗口创建逻辑解耦 |
| 模板方法 (Template Method) | `BaseService.initialize()` | 强制子类实现初始化 |
| 策略模式 (Strategy) | Matrix 多格式导出 | 各 ExportService 实现不同策略 |
| MVC/MVCS | 所有功能模块 | Model-View-Controller-Service 分层 |
| 混入模式 (Mixin) | `DocumentEditorMixin` | 为 Controller 注入文档编辑能力 |

