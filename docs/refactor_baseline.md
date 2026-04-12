# TestFlowManager 重构基线文档

> 更新时间：2026-04-09  
> 目的：基于当前代码真实状态建立重构基线，作为后续分阶段重构、回归验证和任务拆分的统一参考。

---

## 1. 当前系统基线

### 1.1 项目定位

TestFlowManager 是一个运行在 Windows 平台上的 PyQt5 桌面应用，围绕测试项目全生命周期提供以下能力：

- 项目创建与目录初始化
- LTR 申请单处理与编号生成
- Matrix 编辑、导入、导出
- 报告生成、更新、客户版转换
- 邮件与 Word/Excel/Outlook COM 自动化处理

### 1.2 技术基线

- GUI：PyQt5
- 平台依赖：Windows + pywin32 + Office COM
- 文档处理：`python-docx`、`openpyxl`、`pandas`
- 打包：PyInstaller
- 测试：pytest

### 1.3 真实入口与运行链路

应用入口：

- [application.py](D:/PythonProject/TestFlowManager/src/app/application.py)

启动链路：

1. 创建 `QApplication`
2. 初始化日志与运行环境
3. 创建主窗口 `MainWindow`
4. 在主窗口内初始化 controller、导航、Matrix 组件和页面
5. 退出时清理 Word/Excel COM 资源

---

## 2. 真实架构视图

### 2.1 目录级结构

源码主体位于 `src/`：

- `app`：应用入口、资源、实际运行配置
- `core`：全局基础设施
- `common`：公共异常、通用组件、跨模块服务
- `features`：业务功能模块
- `utils`：COM 和文件处理工具
- `managers`：少量管理器类型

### 2.2 主要模块规模

按 Python 文件数量粗略统计：

- `matrix`：69
- `ltr_manager`：25
- `main_window`：23
- `report_wizard`：23
- `customer_report_generator`：11
- `project_creator`：10
- `email_extractor`：9
- `report_updater`：9
- `content_editor`：9
- `document_parser`：8
- `folder_manager`：7
- `test_record_generator`：7
- `file_encryption`：3

结论：

- `matrix` 是复杂度中心
- `main_window` 是集成与耦合中心
- `ltr_manager`、`project_creator` 是业务流程入口中心

### 2.3 名义架构与真实架构差异

文档中描述的是 MVCS，但当前代码真实状态更接近：

`PyQt View + Controller + 全局单例 + 跨模块直连 + 部分 UI 内嵌业务逻辑`

主要偏差：

- View 不只负责展示，直接持有并驱动多个 controller/service/manager
- `main_window` 不只是壳层，还直接集成 Matrix 的具体 UI 和行为
- 跨模块通信同时依赖事件总线和全局状态
- `MatrixService` 以单例形式共享状态
- 配置解析路径与文档描述不一致

---

## 3. 模块依赖图

### 3.1 高层依赖图

```text
application.py
  -> MainWindow
    -> MainWindowController
      -> MainWindowService
      -> LTRViewerController / LTREditorController
      -> ProjectCreatorController
      -> MatrixProjectController
      -> ReportWizardController
      -> ReportUpdaterController
      -> CustomerReportController
      -> DocumentParserController

core singletons
  -> ConfigManager
  -> Logger
  -> EventDispatcher
  -> StateManager

MatrixProjectController
  -> MatrixController
    -> MatrixService (singleton)
      -> export/*
      -> spec/*
      -> processing/*
      -> template/*
      -> base/*

ProjectCreatorController
  -> EmailExtractorController
  -> ProjectCreatorService
  -> LTRProjectIntegrationService
  -> MatrixProjectController

LTRApplicationService
  -> validator / extractor / number generator
  -> EventDispatcher

report_updater / test_record_generator / matrix export services
  -> StateManager.current_project
```

### 3.2 基础设施依赖图

```text
ConfigManager
  -> 读取 src/app/config/settings.json
  -> 读取 src/app/config/paths.ini

Logger
  -> 依赖 ConfigManager.logging

StateManager
  -> 写入状态时 dispatch "state.changed"

EventDispatcher
  -> 多个 controller / service 订阅与发布
```

### 3.3 关键模块的真实依赖方向

#### 主窗口

- [main_window_ui.py](D:/PythonProject/TestFlowManager/src/features/main_window/view/main_window_ui.py)
  - 直接依赖多个 feature controller
  - 直接依赖 Matrix 的 view managers / handlers / toolbar / context menu

- [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
  - 依赖 `state_manager`
  - 订阅多个 `event_dispatcher` 事件
  - 驱动项目打开、Matrix 自动导入、页面切换、标题更新

#### Matrix

- [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)
  - 持有 `MatrixService`
  - 持有导出控制器
  - 直接访问 `state_manager.current_project`
  - 直接弹 `QFileDialog`、`QMessageBox`

- [matrix_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_service.py)
  - 使用模块级单例
  - 聚合多个子服务
  - 同时承担数据、导入、导出、格式化、规范书处理等多类职责

#### 项目创建

- [project_creator_controller.py](D:/PythonProject/TestFlowManager/src/features/project_creator/controller/project_creator_controller.py)
  - 组织邮箱提取、附件选择、Word 解析、LTR 集成、Matrix 集成
  - 直接订阅事件
  - 直接写入 `state_manager.current_project`

---

## 4. 耦合热点

### 4.1 热点一：`main_window` 与 `matrix` 交叉过深

表现：

- 主窗口 View 直接创建和持有 Matrix 相关组件
- Matrix 的 table manager、data sync manager、event handlers、context menus 直接挂在主窗口上
- 主窗口负责 Matrix 初始化、表格刷新、导入、状态切换

影响：

- 主窗口难以维护
- Matrix 无法独立演化
- UI 层与业务层边界模糊
- 后续做页面替换、拆包、自动化测试都很困难

### 4.2 热点二：跨模块通信机制重复

表现：

- 同时存在 `event_dispatcher` 与 `state_manager`
- `StateManager.set_state()` 内部又会分发事件
- 模块既订阅事件又主动读取全局状态

影响：

- 状态来源不单一
- 依赖链隐式化
- 排查行为触发路径成本高

### 4.3 热点三：`MatrixService` 单例导致共享状态过重

表现：

- `MatrixService` 使用模块级单例
- UI、导出、项目切换共用同一个数据模型实例

影响：

- 生命周期边界不清晰
- 多窗口、多项目、测试隔离都不友好
- 容易产生脏状态和隐式副作用

### 4.4 热点四：Controller 同时处理编排、持久化、对话框、状态同步

典型文件：

- [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
- [project_creator_controller.py](D:/PythonProject/TestFlowManager/src/features/project_creator/controller/project_creator_controller.py)
- [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)

影响：

- controller 过胖
- 难以单元测试
- 难以复用

### 4.5 热点五：配置与路径策略不一致

表现：

- 文档中写根目录 `config/`
- 实际运行读取的是 `src/app/config/`
- 配置中硬编码大量绝对 Windows 路径

影响：

- 部署与开发环境切换脆弱
- 文档误导
- 测试环境难构造

### 4.6 热点六：导出/生成输出目录语义长期混用

表现：

- `Submitted Material`、`Test results`、项目子目录、`D:\OutFile` 的职责没有统一文档
- 历史功能常直接硬编码 `D:\OutFile`
- 新增导出功能容易各自猜测保存目录

影响：

- 用户难以预测文件落点
- 同一项目的交付物、测试结果、费用表容易分散
- 后续扩展功能容易继续复制路径判断逻辑

### 4.7 热点七：测试组织不统一

表现：

- `tests/unit`、`tests/integration` 存在
- 但大量测试仍散落在 `tests/` 根目录
- 还有明显偏手工/脚本性质的测试文件

影响：

- 自动化回归边界不清晰
- 无法作为重构安全网稳定使用

---

## 5. 结构性问题总结

当前系统的主要结构问题不是“没有分层”，而是“分层存在但边界失效”。

具体表现为：

- View 层侵入业务编排
- Controller 层承担过多流程和副作用
- Service 层职责聚合过大
- 全局单例过多，隐藏依赖普遍存在
- 模块名义独立，真实上通过主窗口和状态对象强耦合

这意味着重构策略不能从“重写某个模块”开始，而应该优先做边界收口和依赖显式化。

---

## 6. 分阶段拆分方案

原则：

- 先收边界，再拆职责
- 先建立回归保护，再做大迁移
- 先处理壳层和状态流，再拆 Matrix 内部

### 阶段 0：基线固化

目标：

- 把“当前真实架构”文档化
- 标记关键耦合点
- 形成后续任务拆分基准

输出：

- 本文档
- 后续补充依赖清单、模块责任清单、迁移验收清单

### 阶段 1：收口应用壳层

目标：

- 把 `main_window` 从“超级集成器”收缩为“页面壳层 + 导航编排层”

动作：

- 把 Matrix 页面装配逻辑从 `main_window_ui.py` 抽成独立页面对象
- 主窗口只关心页面注册、导航切换、顶层菜单
- 让 feature 自带页面入口对象，而不是由主窗口拼接其内部组件

完成标志：

- 主窗口不再直接管理 Matrix table widget 及其 managers
- `main_window_ui.py` 的 Matrix 专用方法显著减少

### 阶段 2：统一状态与事件边界

目标：

- 建立明确的模块通信约定

动作：

- 定义哪些信息属于“全局状态”，哪些属于“领域事件”
- 禁止同一行为同时靠事件和全局状态驱动
- 给关键事件建立命名和载荷规范

建议约束：

- `StateManager` 只存当前项目、当前用户上下文、UI 全局状态
- `EventDispatcher` 只表达一次性业务事件，如 `project.opened`

完成标志：

- 任一关键业务动作只有一个主触发通道
- 页面更新逻辑不再同时读状态和监听同一事件

### 阶段 3：拆 Matrix 外壳与领域逻辑

目标：

- 将 Matrix 从“共享单例 + UI 深绑定”改造为“可独立维护的功能模块”

动作：

- 拆出 `MatrixWorkspace` 或 `MatrixPage`
- 拆出 `MatrixApplicationService` 负责编排
- 细分 `MatrixDomainService`、`MatrixImportService`、`MatrixExportService`
- 逐步去掉 `MatrixService` 单例

完成标志：

- Matrix 页面能在不依赖主窗口私有属性的情况下工作
- Matrix 数据模型生命周期可控

### 阶段 4：瘦身 Controller

目标：

- 让 controller 回到“协调者”角色

动作：

- 把文件选择、项目解析、JSON 初始化、LTR 关联等编排逻辑拆给 application service
- UI 对话框与业务执行分离
- controller 只处理输入输出和调用顺序

完成标志：

- `main_window_controller.py`、`project_creator_controller.py` 明显缩短
- controller 中可单测的纯逻辑减少，服务层纯逻辑增加

当前结果：

- 已完成 Matrix 主线 UI 收口：`MainWindow + MatrixPage` 成为唯一 Matrix UI 主实现
- 已删除 `matrix_integration.py` 与 `matrix_dialog.py`
- 已完成 `ProjectContext` 驱动的 Matrix 会话更新，移除了 `matrix_controller.project_data_file_path` / `matrix_service.project_data_file_path` 主线属性通道
- 已完成 Matrix 工作区命名收敛：主线入口统一为 `activate_matrix_workspace()` / `open_matrix_workspace()`
- 已完成项目会话统一写入口：`ProjectSessionService`
- 已完成项目会话副作用编排层：`ProjectSessionCoordinator`
- 已完成文档生成输入准备层：`ProjectDocumentContext`
- 已完成打开已有项目流程下沉：`ProjectOpenService`
- 已完成新建项目完成后项目会话恢复流程下沉：`ProjectCreationApplicationService`
- 已完成 `report_updater` / `report_wizard` / `customer_report` / `test_record` / `matrix export` 主线对 `ProjectContext` 的接入
- 阶段 4 已完成
- 已完成一轮输出目录盘点：
  - `Submitted Material`：报告、Test Record
  - `Test results`：LLCR、CR
  - 项目工作目录：费用表
  - 原目录另存：客户版报告
  - `D:\OutFile`：无项目态兜底

### 阶段 5：配置与环境解耦

目标：

- 修复配置位置、路径策略和文档不一致问题

动作：

- 明确配置根目录
- 去掉散落的绝对路径假设
- 增加环境解析与默认值策略
- 明确输出目录规则并沉淀到上下文能力层

当前已明确的输出目录基线：

- `Submitted Material`
  - 用于报告、Test Record、提交材料型输出
- `Test results`
  - 用于 LLCR、CR 及后续测试结果类导出
- 项目工作目录 / 项目子目录
  - 用于费用表等与项目目录结构强绑定的输出
- `D:\OutFile`
  - 仅作为无项目态或目录解析失败时的全局兜底目录

当前已落地的配置访问收口：

- `ConfigManager` 已提供显式配置访问接口：
  - `get_path()`
  - `get_default()`
  - `get_password()`
  - `get_standard_file()`
  - `get_equipment_data_source()`
- 主线与高频模块已不再直接拼写 `paths.* / defaults.* / passwords.* / standard_files.* / equipment_data_sources.*` 字符串前缀

当前已完成的配置项盘点：

- 已新增 [config_inventory.md](D:/PythonProject/TestFlowManager/docs/config_inventory.md)
- 已明确：
  - 哪些配置项属于部署变量
  - 哪些配置项属于业务默认值
  - 哪些配置项仍带有历史硬编码兜底语义
- 已完成第一项配置来源去重：
  - `ltr_file` 已只保留在 `paths.ini [Paths]`
- 已完成第二项配置来源去重：
  - `ltr_password` 已只保留在 `paths.ini [Passwords]`
- 已完成模板目录语义定性：
  - `paths.template_dir` 视为外部部署模板目录
  - `ltr.fields_config` 视为应用内部资源路径
- 已完成 `report_updater` 历史路径语义收口：
  - `EquipmentDataSources.source_doc_path`
  - `EquipmentDataSources.default_output_path`
  - 两者均仅保留无项目态兜底语义
- 已明确日志配置归属：
  - `logging.level / logging.file` 继续保留在 `settings.json`

完成标志：

- 配置路径规则有唯一来源
- 文档与代码一致
- 已有项目态导出链不再优先落到 `D:\OutFile`

### 阶段 6：测试基线重建

目标：

- 为重构建立可靠回归网

动作：

- 统一测试目录结构
- 区分 unit / integration / manual
- 优先覆盖配置加载、项目打开、Matrix 导入导出、LTR 编号流程

完成标志：

- 核心流程至少有可自动执行的冒烟测试
- GUI 手工测试脚本从自动化测试目录中分离

当前结果：

- 已补第一批纯逻辑自动化测试：
  - [test_project_contexts.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_contexts.py)
  - [test_project_open_service.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_open_service.py)
  - [test_config_manager.py](D:/PythonProject/TestFlowManager/tests/unit/test_config_manager.py)
  - [test_project_session_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_session_flow.py)
  - [test_project_creation_application_service.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_creation_application_service.py)
  - [test_main_window_open_project_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_main_window_open_project_flow.py)
  - [test_output_path_decisions.py](D:/PythonProject/TestFlowManager/tests/unit/test_output_path_decisions.py)
  - [test_project_creator_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_creator_flow.py)
- 已覆盖：
  - `ProjectContext`
  - `ProjectDocumentContext`
  - `OutputPathResolver`
  - `ProjectOpenService`
  - `ConfigManager`
  - `ProjectSessionService`
  - `ProjectSessionCoordinator`
  - `Matrix 自动导入` 的非 GUI 编排边界
  - `ProjectCreationApplicationService`
  - `MainWindowController.handle_open_project()`
  - `MainWindowController._on_project_opened()`
  - 导出/生成链默认目录规则
  - `MainWindowController.handle_new_file()`
  - `ProjectCreatorController.handle_create_new_project()`
  - `ProjectCreatorController` 创建后项目会话接入
- 已验证：
  - `python -m pytest tests/unit/test_project_contexts.py tests/unit/test_project_open_service.py -q`
  - `python -m pytest tests/unit/test_config_manager.py tests/unit/test_project_session_flow.py -q`
  - `python -m pytest tests/unit/test_project_creation_application_service.py -q`
  - `python -m pytest tests/unit/test_main_window_open_project_flow.py -q`
  - `python -m pytest tests/unit/test_output_path_decisions.py -q`
  - `python -m pytest tests/unit/test_project_creator_flow.py -q`
  - `python -m pytest tests/unit/test_project_contexts.py tests/unit/test_project_open_service.py tests/unit/test_config_manager.py tests/unit/test_project_session_flow.py tests/unit/test_project_creation_application_service.py tests/unit/test_main_window_open_project_flow.py tests/unit/test_output_path_decisions.py tests/unit/test_project_creator_flow.py -q`
- 这意味着阶段 6 已从“只有手工回归清单”进入“已有可执行自动化基线”的状态
- 当前可以将阶段 6 标记为“首轮完成”：
  - 已覆盖“打开项目 / 新建项目 / 项目会话副作用 / Matrix 自动导入 / 输出目录规则”这五条主线
  - 后续补测将转入增量增强，而不再是从零建立安全网

---

## 7. 第一批可落地改造点

以下改造点优先级高、收益明显、风险相对可控，适合作为第一轮实施任务。

### 7.1 提取 `MatrixPage`

目标：

- 把 `main_window_ui.py` 中 Matrix 页面的 UI 组装和事件绑定整体迁出

当前来源：

- [main_window_ui.py](D:/PythonProject/TestFlowManager/src/features/main_window/view/main_window_ui.py)

预期结果：

- 主窗口只注册一个 `MatrixPage`
- Matrix page 自己管理 toolbar/table/context menu/handlers

### 7.2 定义项目上下文对象

目标：

- 用显式对象替代到处散落的 `current_project`、`dl_number`

建议新增：

- `ProjectContext`
  - `project_path`
  - `dl_number`
  - `application_data_path`
  - `matrix_file_path`

收益：

- 降低字符串 key 状态共享
- 提高可读性与可测试性

### 7.3 统一“打开项目”流程入口

目标：

- 把项目打开后触发的一系列副作用集中到单一编排点

当前问题：

- 打开项目会同时更新状态、派发事件、切页面、更新标题、自动导入 Matrix

建议：

- 新建 `ProjectOpenOrchestrator` 或 `ProjectSessionService`

### 7.4 为 `MatrixService` 去单例做准备

短期动作：

- 先把单例访问点集中化
- 禁止新代码继续隐式依赖共享实例

当前结果：

- `matrix_service_provider.py` 已删除（Phase-11），不再作为共享实例入口
- 共享语义只保留在 `MatrixService.shared()`，且直接 import/use 受 guard 限制，仅允许在 `MatrixSessionRegistry` 内部路由
- 主消费方已开始从直接 `MatrixService()` / `MatrixService.shared()` 改为统一走 session 装配入口：
  - [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)
  - [test_spec_tables_service.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/service/test_spec_tables_service.py)
  - `MatrixController` 已支持显式注入 `matrix_service / application_service`
  - `MatrixProjectController` 已支持显式注入 `matrix_controller`
- `MatrixSessionFactory` 已建立为最小 session 级装配点：
  - [matrix_session_factory.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_session_factory.py)
  - 当前支持两种装配模式：
    - `shared`
    - `isolated`
  - 默认行为仍保持 `shared`
  - 会话切换约束与残留依赖盘点已记录于：
    [matrix_session_switching_inventory.md](D:/PythonProject/TestFlowManager/docs/matrix_session_switching_inventory.md)
- `MatrixPage / matrix_event_handlers / main_window_ui / main_window event_handlers` 中直接穿透
  `matrix_controller.service` 的第一批入口已收成 `MatrixController` 级接口
- `report_wizard / test_record` 的页面和控制器入口已切到 `MatrixController` 优先通道：
  - [report_wizard_controller.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/controller/report_wizard_controller.py)
  - [report_wizard_dialog.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/view/report_wizard_dialog.py)
  - [test_spec_tables_page.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/view/test_spec_tables_page.py)
  - [test_record_controller.py](D:/PythonProject/TestFlowManager/src/features/test_record_generator/controller/test_record_controller.py)
- `report_wizard/test_spec_tables` 已继续去 provider 化：
  - [test_spec_tables_service.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/service/test_spec_tables_service.py)
    不再直接读取 `MatrixServiceProvider`
  - 改为显式消费 `matrix_headers / matrix_rows` 快照
  - `test_spec_tables_page.py` / worker 已优先使用
    `matrix_controller.get_project_context()` 与
    `matrix_controller.get_matrix_headers()/get_matrix_rows()`
  - `test_spec_tables_page.py` / worker 中对全局 `get_current_project_context()` 的直接回退已移除
- `test_record_controller.py` / `record_data_table_export_controller.py` /
  `fee_sheet_export_service.py` 中对全局项目态的直接回退已继续收紧：
  - 当前统一优先消费显式 `ProjectContext`
  - 无显式上下文时返回 `None`，交由 `ProjectDocumentContext` / 输出路径策略兜底
  - `test_record_controller.py` 在存在 `matrix_controller` 时已忽略 `matrix_service`，
    `matrix_service` 进一步降为 legacy 兼容入口
- `report_updater_controller.py` / `report_updater_service.py` 初始化时已不再主动抓取全局
  `current_project_context`，改为等待显式项目会话注入
- `matrix_controller.py` / `import_export_manager.py` 也已移除对全局项目态的直接回退：
  - 当前只认显式 `project_context`
  - 无显式上下文时返回 `None`
- `MatrixService` 已增加显式 `create_isolated()`：
  - `MatrixSessionFactory` 不再直接 `object.__new__(MatrixService)`
  - `isolated` 会话创建已收敛到 `MatrixService` 类接口
  - 共享实例管理也已从模块级全局变量迁到 `MatrixService` 类属性
- `MatrixService()` 已回归普通实例语义，当前共享语义只保留在
    `MatrixService.shared()`
- 共享/隔离服务路由已收敛到 `MatrixSessionRegistry`（并由 `MatrixSessionFactory` 负责装配串联）
- `MatrixSessionRegistry` 已引入（小而克制）：
  - [matrix_session_registry.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_session_registry.py)
  - 只负责管理“当前 shared/isolated provider 选择”
  - 已移除 `install()/uninstall()`（不再提供全局 provider 切换入口），shared/isolated 语义仅在 registry 内部路由
- `get_matrix_service()` 的外部消费已清零，当前仅保留为 `MatrixController` 内部兼容出口
- `matrix_project_controller.py` 中最后一处 `matrix_controller.service` 直接穿透已收口到
  `MatrixController.set_ltr_data()`
- `MatrixImportService` 已拆出第一块导入职责：
  - [matrix_import_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_import_service.py)
  - 项目态 `matrix.xlsx` 自动导入逻辑已从
    [import_export_manager.py](D:/PythonProject/TestFlowManager/src/features/matrix/view/managers/import_export_manager.py)
    下沉到服务层
  - `spec` 导入链也已收口到 `MatrixImportService`，`MatrixService` 改为委托该服务执行导入
- `MatrixApplicationService` 已作为应用层编排切入点落地：
  - [matrix_application_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_application_service.py)
  - 当前已承接导入相关编排，以及 `standardize_and_fill` 这条初始化/提取/更新标准版本的主流程
  - `spec` 导入成功后的后置处理策略也已下沉到应用层，当前明确保持 `refresh_only`，不升级为
    `refresh + initialize`
  - `initialize_with_ltr_data()` 也已下沉到应用层，`MatrixController` 改为委托
  - `set_project_context()` / `set_ltr_data()` 的导出上下文同步也已下沉到应用层
  - `MatrixController` 与 `ImportExportManager` 已改为通过它协调导入流程
- `MatrixExportService` 已开始承接基础导出职责：
  - [matrix_export_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_export_service.py)
  - 当前先收 `matrix.xlsx` 显式导出与关闭时自动导出链
  - `handle_export_matrix_to_excel()` 中除文件对话框和消息提示外的默认路径、执行导出、
    失败分类逻辑已下沉到导出服务 / 应用层
  - `handle_export_matrix_to_excel()` 现已改为返回结构化结果，消息提示已回到 UI 层
  - `LLCR/CR` 的“同步模型 + 更新导出控制器 + 执行导出”应用编排也已下沉到
    `MatrixApplicationService / MatrixExportService`
  - `MatrixController` 中重复持有的 `export_controller` 已删除，导出上下文同步统一回到
    `MatrixService.export_controller`
- 这一步暂不改变运行时行为，只是为后续显式注入和工厂化做准备

中期动作：

- 支持显式传入 `MatrixData`
- 支持按项目创建 Matrix 会话实例

### 7.5 修正配置根目录策略

目标：

- 明确配置文件真实位置并统一文档

当前文件：

- [config_manager.py](D:/PythonProject/TestFlowManager/src/core/config_manager.py)
- [settings.json](D:/PythonProject/TestFlowManager/src/app/config/settings.json)
- [paths.ini](D:/PythonProject/TestFlowManager/src/app/config/paths.ini)

建议：

- 明确 `src/app/config/` 为开发态配置目录
- 如需根目录 `config/`，则统一迁移，不保留双重叙述

### 7.6 建立测试分层目录

建议结构：

```text
tests/
  unit/
  integration/
  gui_manual/
  fixtures/
```

先搬迁：

- 手工/脚本测试移到 `gui_manual/`
- 保留自动化测试在 `unit/` 和 `integration/`

### 7.7 统一输出目录策略

目标：

- 为所有导出/生成链建立统一的落盘规则

规则：

- `Submitted Material`：提交材料型输出
- `Test results`：测试结果类导出
- 项目工作目录：费用表等项目结构强绑定输出
- `D:\OutFile`：仅无项目态兜底

建议：

- 统一经由 `ProjectDocumentContext` 解析目录
- 禁止新功能在已有项目态直接硬编码 `D:\OutFile`

---

## 8. 推荐的第一阶段实施顺序

建议按以下顺序推进：

1. 抽 `MatrixPage`
2. 抽 `ProjectContext`
3. 收口项目打开流程
4. 整理状态与事件职责
5. 压缩主窗口 controller/view 职责
6. 再拆 Matrix service 单例

原因：

- 这是对现有功能影响最小、收益最大的路径
- 可以尽早降低主窗口耦合
- 可以在不大改业务逻辑的情况下先理顺边界

---

## 9. 风险与约束

### 9.1 平台风险

系统深度依赖 Windows COM：

- Word
- Excel
- Outlook

因此任何重构都需要避免破坏：

- Office 进程生命周期管理
- 文件句柄释放
- UI 关闭时的资源清理

### 9.2 回归风险

高风险流程：

- 打开项目
- 自动导入 `matrix.xlsx`
- LTR 申请单处理
- Matrix 导出
- 报告更新与客户版转换

这些流程在重构初期必须保留冒烟验证。

### 9.3 工作区噪音

当前仓库存在大量：

- `__pycache__`
- `logs/`
- `dist/`
- `build/`
- 未跟踪文档和产物

这会干扰代码审查和变更跟踪，建议在正式重构前同步清理忽略规则。

---

## 10. 建议形成的后续文档

为了让重构可执行，建议继续补齐三份文档：

1. 模块责任清单
   - 每个 feature 的边界、输入、输出、拥有的数据

2. 迁移任务看板
   - 每阶段拆成具体任务、风险、验收标准

3. 回归测试清单
   - 每次重构后必须手测/自动化验证的关键流程

---

## 11. 结论

这个项目不是“没有架构”，而是“架构意图存在，但随着功能增长，边界逐渐失效”。

重构重点不应该放在表面上的目录调整，而应该放在四件事上：

- 收缩主窗口职责
- 解耦 Matrix
- 统一状态流
- 让配置与测试成为稳定基础设施

只要先把这四件事做对，后续对 LTR、报告链路、项目创建流程的细化重构都会容易很多。
## Phase 7 Incremental Update (2026-04-10)

- `MatrixSessionFactory` now accepts explicit `registry` and `provider` injection.
- When a `registry` is injected, session mode selection (`shared` / `isolated`) is routed through the registry.
- Default behavior remains unchanged: without injection, `shared` resolves via registry-owned shared factory and keeps shared semantics stable.
- This keeps runtime behavior stable while opening a clean extension point for future multi-session orchestration.
- Registry instance ownership is still in transition:
  - current runtime: `MainWindow` (view layer) constructs the default registry/session stack
  - target: move assembly ownership to app composition (`src/app/...`) and inject into the UI/controller layer
- `TestRecordController` page/controller boundary was further tightened:
  - removed legacy `matrix_service` argument and fallback path
  - kept only `matrix_controller` snapshot + `ProjectContext` flow
- `MatrixController.get_matrix_service()` legacy compatibility outlet has been removed.
- `MatrixSessionRegistry` / `MatrixSessionFactory` now include optional `session_id` routing
  capability for future multi-session orchestration, without changing the current default shared path.
- Isolated pilot entry lifecycle is now explicit:
  - fixed pilot `session_id` is passed from main window new-project entry
  - isolated pilot session is released during project-creator cleanup
- Session lifecycle management now has a lightweight wrapper:
  - `MatrixSessionScope` (`MatrixSessionRegistry.open_scope`) for open/close style handling
  - controller cleanup uses scope-first, with release fallback for compatibility
- `MainWindowController` now has a prewired secondary non-default isolated entry API
  (preview-style open/close by `session_id`) to validate concurrent scope behavior
  without changing default shared workflows.
- Hidden debug shortcut entry is available only when `TFM_ENABLE_DEBUG_COMMANDS` is enabled,
  for manual smoke of isolated preview session lifecycle without exposing default UI paths.

## 15. Phase 15 Report Export Boundary Cleanup（2026-04-12）

- Phase 14 Guard Lockdown 之后，Phase 15 将 `ReportWizard`/`ReportUpdater` 的项目上下文与输出路径逻辑全部交给 `ReportExportCoordinator`，controller 只负责 UI 输入/反馈、显式注入 `ProjectContext`+`MatrixController`，彻底淘汰 `ProjectContext.from_project_path` 的隐式 fallback。
- `ReportWizardDialog` 只通过 controller 注入的 coordinator 回调创建报告；`ReportUpdaterController`/`ReportUpdaterData` 只接受 `ProjectContext`，`ReportUpdaterService` 也只在明确的 context 下运行。此阶段还需要在 `docs/tasks/phase15_report_export.md` 中维护 QA 验证脚本，方便团队复核。
- Phase 15 仍然依赖 `tools/run_phase14_guard_regression.ps1`（GitHub workflow `phase14-guard-lockdown.yml`）跑通 Phase 11/12 + Phase 14 guard tests，最近一次（2026-04-12）执行 143 条测试全部通过，说明新的 coordinator 和 guard 协作已经稳定。
