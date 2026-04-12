# TestFlowManager 重构任务看板

> 更新时间：2026-04-11  
> 关联文档：[refactor_baseline.md](D:/PythonProject/TestFlowManager/docs/refactor_baseline.md)

---

## 1. 使用说明

本文档用于把重构基线转成可执行任务。每个阶段包含：

- 目标
- 具体任务
- 涉及文件
- 主要风险
- 验收标准

建议执行原则：

- 一次只推进一个阶段
- 每个阶段结束后做一次最小回归
- 没有回归结论，不进入下一阶段

---

## 2. 阶段总览

| 阶段 | 名称 | 目标 | 状态 |
|------|------|------|------|
| 0 | 基线固化 | 明确真实架构、建立任务与回归基准 | 已完成 |
| 1 | 壳层收口 | 从主窗口移出 Matrix 细节装配 | 已完成 |
| 2 | 状态流收口 | 统一全局状态与事件边界 | 已完成 |
| 3 | Matrix 模块拆分 | 拆 Matrix 页面、编排层、领域服务 | 已完成 |
| 4 | Controller 瘦身 | 下沉流程逻辑到 application service | 已完成 |
| 5 | 配置与环境治理 | 统一配置目录、路径策略和文档 | 已完成 |
| 6 | 测试基线重建 | 建立可靠回归网 | 已完成 |
| 7 | Matrix 会话基础接入 | 建立 session factory/registry 注入和试点入口 | 已完成 |
| 8 | 非默认会话编排解耦 | 建立 manager/orchestrator/facade 装配链 | 已完成 |
| 9 | 正式会话化过渡 | 从 debug 试验态推进到受控业务入口 | 已完成 |
| 10 | 多会话对象管理 | 页面级多会话绑定、切换、回收与退役旧兼容 | 已完成 |

---

## 3. 阶段 0：基线固化

### 3.1 目标

- 固化当前真实结构
- 确定高风险流程
- 建立后续重构的追踪入口

### 3.2 任务清单

#### T0-1 建立重构基线文档

- 状态：已完成
- 输出：
  - [refactor_baseline.md](D:/PythonProject/TestFlowManager/docs/refactor_baseline.md)

#### T0-2 建立任务看板

- 状态：已完成
- 输出：
  - 本文档

#### T0-3 建立回归清单初稿

- 内容：
  - 打开项目
  - 新建项目
  - 自动导入 `matrix.xlsx`
  - Matrix 导出 Excel
  - LTR 申请单处理
  - 报告更新
  - 客户版报告转换

- 涉及文件：
  - [application.py](D:/PythonProject/TestFlowManager/src/app/application.py)
  - [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
  - [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)
  - [project_creator_controller.py](D:/PythonProject/TestFlowManager/src/features/project_creator/controller/project_creator_controller.py)

- 风险：
  - 没有统一回归清单会导致后续改动难以判断是否破坏行为

- 验收标准：
  - 有一份明确的冒烟流程列表
  - 每个流程有最少一条验证口径

---

## 4. 阶段 1：壳层收口

### 4.1 目标

- 将主窗口从“超级集成器”收缩为“页面壳层 + 导航容器”
- 把 Matrix 页面内部装配从主窗口迁出

### 4.2 任务清单

#### T1-1 识别主窗口中的 Matrix 专属逻辑

- 任务：
  - 标注 `main_window_ui.py` 中所有 Matrix 专属字段、初始化流程、事件处理方法
  - 整理迁移边界，区分“主窗口公共能力”和“Matrix 页面能力”

- 涉及文件：
  - [main_window_ui.py](D:/PythonProject/TestFlowManager/src/features/main_window/view/main_window_ui.py)

- 风险：
  - 混淆页面导航逻辑和 Matrix 页面内部逻辑

- 验收标准：
  - 得到一份 Matrix 相关成员与方法清单
  - 能明确哪些方法应迁出

#### T1-2 新增 `MatrixPage` 或等价页面对象

- 任务：
  - 提供独立页面类，封装 toolbar、table、context menu、handlers、managers
  - 让主窗口只负责注册页面，不直接管理页面内部细节

- 建议新增文件：
  - `src/features/matrix/view/matrix_page.py`

- 可能涉及文件：
  - [main_window_ui.py](D:/PythonProject/TestFlowManager/src/features/main_window/view/main_window_ui.py)
  - [matrix_toolbar.py](D:/PythonProject/TestFlowManager/src/features/matrix/view/components/matrix_toolbar.py)
  - [matrix_context_menus.py](D:/PythonProject/TestFlowManager/src/features/matrix/view/components/matrix_context_menus.py)
  - [table_manager.py](D:/PythonProject/TestFlowManager/src/features/matrix/view/managers/table_manager.py)
  - [data_sync_manager.py](D:/PythonProject/TestFlowManager/src/features/matrix/view/managers/data_sync_manager.py)
  - [import_export_manager.py](D:/PythonProject/TestFlowManager/src/features/matrix/view/managers/import_export_manager.py)
  - [matrix_event_handlers.py](D:/PythonProject/TestFlowManager/src/features/matrix/view/handlers/matrix_event_handlers.py)

- 风险：
  - 主窗口与 Matrix 页面之间的回调关系断裂
  - 页面切换后 Matrix 初始化时机变化

- 验收标准：
  - 主窗口中不再直接持有 Matrix 的 table manager / sync manager / handlers
  - Matrix 页面首次显示、刷新、导入行为保持一致

#### T1-3 建立主窗口页面注册机制

- 任务：
  - 为主窗口定义统一的页面注册接口
  - 每个功能页以页面对象方式挂载到导航

- 涉及文件：
  - [main_window_ui.py](D:/PythonProject/TestFlowManager/src/features/main_window/view/main_window_ui.py)
  - [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)

- 风险：
  - 破坏现有导航索引与菜单联动

- 验收标准：
  - 页面切换逻辑只依赖页面注册信息
  - 主窗口对具体页面内部实现无感知

### 4.3 阶段验收

- 主窗口代码规模下降
- Matrix 页面能独立初始化与刷新
- 用户可正常进入 Matrix 页并完成导入、编辑、导出

---

## 5. 阶段 2：状态流收口

### 5.1 目标

- 统一全局状态和业务事件职责
- 消除同一动作被双通道驱动的问题

### 5.2 任务清单

#### T2-1 列出所有事件订阅点与状态访问点

- 任务：
  - 梳理 `event_dispatcher.subscribe(...)`
  - 梳理 `state_manager.get_state/set_state(...)`
  - 建立事件表和状态表

- 重点文件：
  - [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
  - [project_creator_controller.py](D:/PythonProject/TestFlowManager/src/features/project_creator/controller/project_creator_controller.py)
  - [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)
  - `src/features/matrix/service/export/*`
  - `src/features/report_updater/*`
  - `src/features/test_record_generator/*`

- 风险：
  - 漏掉隐式依赖点

- 验收标准：
  - 每个关键状态和事件都有来源、消费方、用途说明

#### T2-2 定义全局状态白名单

- 建议状态：
  - `current_project_context`
  - `application_status`
  - `current_user_preferences`

- 任务：
  - 将仅用于一次性通知的信息从状态中移除
  - 避免只为触发刷新而写全局状态

- 涉及文件：
  - [state_manager.py](D:/PythonProject/TestFlowManager/src/core/state_manager.py)
  - [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
  - [project_creator_controller.py](D:/PythonProject/TestFlowManager/src/features/project_creator/controller/project_creator_controller.py)

- 风险：
  - 改动后页面刷新时机变化

- 验收标准：
  - 关键业务对象不再以散乱字符串状态传递

#### T2-3 定义事件命名与载荷规范

- 任务：
  - 统一事件命名为 `<domain>.<action>`
  - 统一事件 payload 结构

- 建议优先规范：
  - `project.opened`
  - `project.created`
  - `matrix.imported`
  - `ltr.application.processed`

- 涉及文件：
  - [event_dispatcher.py](D:/PythonProject/TestFlowManager/src/core/event_dispatcher.py)
  - 相关 controller / service

- 风险：
  - 旧事件消费者未同步改造

- 验收标准：
  - 同类事件结构一致
  - 关键流程只有一个主触发入口

### 5.3 阶段验收

- 打开项目流程不再既依赖状态又依赖重复事件
- 关键页面刷新路径可明确追踪
- 事件表和状态表完成

---

## 6. 阶段 3：Matrix 模块拆分

### 6.1 目标

- 把 Matrix 从主窗口附属实现改造为独立功能模块
- 把单例共享服务逐步收口

### 6.2 任务清单

#### T3-1 拆出 Matrix 页面编排层

- 任务：
  - 引入 `MatrixPageController` 或 `MatrixWorkspace`
  - 页面交互逻辑不再直接挂在主窗口对象上

- 建议新增文件：
  - `src/features/matrix/controller/matrix_page_controller.py`
  - 或 `src/features/matrix/view/matrix_workspace.py`

- 涉及文件：
  - [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)
  - [main_window_ui.py](D:/PythonProject/TestFlowManager/src/features/main_window/view/main_window_ui.py)

- 风险：
  - 旧的 `self.parent`、`self.parent_view` 访问方式失效

- 验收标准：
  - Matrix 页可以只依赖自身编排对象完成交互

#### T3-2 拆分 `MatrixService` 职责

- 当前聚合职责：
  - 数据模型持有
  - 行列操作
  - 格式化
  - 规范书导入
  - 导出
  - LTR 数据接入

- 建议拆分：
  - `MatrixDomainService`
  - `MatrixImportService`
  - `MatrixExportService`
  - `MatrixSession` 或 `MatrixWorkspaceState`

- 涉及文件：
  - [matrix_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_service.py)
  - `src/features/matrix/service/base/*`
  - `src/features/matrix/service/spec/*`
  - `src/features/matrix/service/export/*`
  - `src/features/matrix/service/processing/*`

- 风险：
  - 导入导出流程依赖当前聚合模型

- 验收标准：
  - 服务职责边界清晰
  - 导出不再隐式依赖 UI 同步方法

#### T3-3 为去单例做兼容层

- 任务：
  - 保留旧调用入口，但集中在一个工厂中创建 `MatrixService`
  - 标注所有共享实例访问点

- 涉及文件：
  - [matrix_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_service.py)
  - [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)
  - [matrix_project_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_project_controller.py)

- 风险：
  - 生命周期切换导致数据丢失或状态未同步

- 验收标准：
  - 新代码可通过显式构造拿到 Matrix 会话
  - 老代码仍可运行

#### T3-4 引入 `ProjectContext` / `MatrixContext`

- 任务：
  - 用对象替代零散的 `current_project`、`dl_number`、`project_data_file_path`

- 建议新增文件：
  - `src/core/project_context.py`
  - 或 `src/features/project_creator/model/project_context.py`

- 涉及文件：
  - [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
  - [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)
  - [project_creator_controller.py](D:/PythonProject/TestFlowManager/src/features/project_creator/controller/project_creator_controller.py)

- 风险：
  - 字符串状态和对象状态并存一段时间

- 验收标准：
  - 关键流程以 context 对象传递项目信息

### 6.3 阶段验收

- Matrix 页面不依赖主窗口私有字段
- Matrix 服务边界清晰
- 至少一个核心流程已使用显式 context 对象

---

## 7. 阶段 4：Controller 瘦身

状态：已完成

### 7.1 目标

- 让 controller 回到“协调输入输出”的角色
- 把流程型逻辑迁移到 application service

### 7.2 任务清单

#### T4-1 拆分主窗口打开项目流程

- 当前问题：
  - 文件选择
  - JSON 补建
  - Word 信息提取
  - 状态更新
  - 事件派发
  - UI 标题更新
  - Matrix 自动导入
  - 页面切换

  全都堆在 [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)

- 建议新增：
  - `ProjectOpenService`
  - `ProjectSessionService`

- 风险：
  - 项目打开链路是高风险流程

- 验收标准：
  - controller 只负责收集用户输入和处理结果展示

#### T4-2 拆分项目创建流程编排

- 当前问题：
  - 邮件选择
  - 附件过滤
  - Word 文档解析
  - LTR 申请数据对话框
  - 项目目录创建
  - 事件订阅和状态同步

  全在 [project_creator_controller.py](D:/PythonProject/TestFlowManager/src/features/project_creator/controller/project_creator_controller.py)

- 建议新增：
  - `ProjectCreationApplicationService`
  - `AttachmentSelectionService`
  - `ProjectBootstrapService`

- 风险：
  - 现有流程跨邮件、LTR、Matrix 多模块

- 验收标准：
  - controller 显著缩短
  - 核心流程可在不依赖 UI 的情况下执行

#### T4-3 拆分 Matrix 导出流程的 UI 逻辑

- 当前问题：
  - 导出 controller 同时处理 UI 对话框、状态读取、文件权限异常、业务导出

- 涉及文件：
  - [matrix_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/controller/matrix_controller.py)

- 建议：
  - UI 文件选择留在 controller
  - 导出执行、路径决策、错误分类下沉到 service

- 风险：
  - 导出路径规则当前分散在多个位置

- 验收标准：
  - 导出逻辑不再依赖 controller 内部状态分支

### 7.3 阶段验收

- `main_window_controller.py` 和 `project_creator_controller.py` 代码量明显下降
- 新增 application service 覆盖核心流程
- 关键流程可写单元测试

### 7.4 当前完成结果

- `MainWindow` 与 Matrix 的边界已恢复为 `MainWindow + MatrixPage`
- `matrix_integration.py` 已删除
- `matrix_dialog.py` 已删除
- `MatrixController` / `MatrixProjectController` 主线入口已统一为工作区语义
- `ProjectContext` 已成为项目会话与项目数据文件路径的主线来源
- `matrix_controller.project_data_file_path` 与 `matrix_service.project_data_file_path` 已从主线删除
- `ProjectSessionService` 已成为项目会话唯一写入口
- `ProjectSessionCoordinator` 已统一项目会话建立后的 UI/Matrix/Report 副作用
- `ProjectDocumentContext` 已成为文档生成/更新链路的统一输入准备层
- `ProjectOpenService` 已承接“打开已有项目”流程中的 `application_data.json` 补建与上下文准备
- `ProjectCreationApplicationService` 已承接“新建项目完成后进入项目会话”流程编排
- `report_updater` 已切换到 `ProjectContext` 主线，不再依赖分散项目路径状态

### 7.5 阶段结论

- 阶段 4 完成
- 下一阶段重点转为剩余历史兼容层清理、文档/测试同步，以及阶段性结构验收

---

## 8. 阶段 5：配置与环境治理

### 8.1 目标

- 统一配置目录策略
- 修复文档与代码不一致
- 降低绝对路径依赖
- 明确导出/生成输出目录规则

### 8.2 任务清单

#### T5-1 统一配置目录定义

- 当前真实位置：
  - [settings.json](D:/PythonProject/TestFlowManager/src/app/config/settings.json)
  - [paths.ini](D:/PythonProject/TestFlowManager/src/app/config/paths.ini)

- 任务：
  - 决定开发态和打包态配置根目录
  - 更新 `ConfigManager` 解析策略
  - 修正文档

- 涉及文件：
  - [config_manager.py](D:/PythonProject/TestFlowManager/src/core/config_manager.py)
  - [project_session_state_flow.md](D:/PythonProject/TestFlowManager/docs/project_session_state_flow.md)
  - [README.md](D:/PythonProject/TestFlowManager/README.md)

- 风险：
  - 打包运行路径与开发路径切换被破坏

- 验收标准：
  - 文档、代码、打包逻辑三者一致

#### T5-2 抽象路径配置对象

- 任务：
  - 为 `paths.*` 提供集中访问接口
  - 避免各模块自己拼接路径

- 建议新增：
  - `PathConfig` 或 `PathResolver`

- 涉及文件：
  - [config_manager.py](D:/PythonProject/TestFlowManager/src/core/config_manager.py)
  - `src/utils/*`
  - `src/features/*`

- 风险：
  - 老代码依然大量直接取字符串配置

- 验收标准：
  - 关键路径构造集中化

- 当前结果：
  - 已在 [config_manager.py](D:/PythonProject/TestFlowManager/src/core/config_manager.py) 增加显式配置访问接口
  - 主线与高频模块已切换到：
    - `get_path()`
    - `get_default()`
    - `get_password()`
    - `get_standard_file()`
    - `get_equipment_data_source()`

#### T5-3 清理绝对路径依赖

- 任务：
  - 识别配置中硬编码路径
  - 明确哪些是部署变量，哪些是默认值

- 涉及文件：
  - [settings.json](D:/PythonProject/TestFlowManager/src/app/config/settings.json)
  - [paths.ini](D:/PythonProject/TestFlowManager/src/app/config/paths.ini)

- 风险：
  - 业务用户环境依赖真实本地目录

- 验收标准：
  - 配置字段有说明
  - 缺省路径与环境覆盖机制明确

- 当前结果：
  - 已新增 [config_inventory.md](D:/PythonProject/TestFlowManager/docs/config_inventory.md)
  - 已按 `部署变量 / 默认值 / 历史兜底` 盘点 `settings.json` 与 `paths.ini`
  - 已登记当前仍存在的代码级硬编码兜底路径
  - 已完成首个重复配置来源去重：`ltr_file` 只保留在 `paths.ini [Paths]`
  - 已完成第二项重复配置来源去重：`ltr_password` 只保留在 `paths.ini [Passwords]`
  - 已明确模板目录语义：`paths.template_dir` 为部署变量，`ltr.fields_config` 为应用内部资源
  - 已完成 `report_updater` 历史路径语义收口：`source_doc_path / default_output_path` 仅保留无项目态兜底语义
  - 已明确日志配置归属：`logging.level / logging.file` 继续保留在 `settings.json`
  - 已新增 [fallback_path_decisions.md](D:/PythonProject/TestFlowManager/docs/fallback_path_decisions.md)，明确剩余代码级兜底路径的保留与后续候选

#### T5-4 建立统一输出目录策略

- 任务：
  - 明确 `Submitted Material`、`Test results`、项目子目录 / 项目工作目录、`D:\OutFile` 四类目录的职责
  - 将项目态目录解析优先收口到 `ProjectDocumentContext`
  - 禁止已有项目态导出链优先落到 `D:\OutFile`

- 当前规则：
  - `Submitted Material`
    - 报告、Test Record、提交材料型输出
  - `Test results`
    - LLCR、CR、后续测试结果类导出
  - 项目子目录 / 项目工作目录
    - 费用表等项目结构强绑定输出
  - `D:\OutFile`
    - 无项目态或目录解析失败时的全局兜底目录

- 涉及文件：
  - [project_document_context.py](D:/PythonProject/TestFlowManager/src/core/project_document_context.py)
  - `src/features/*/controller/*.py`
  - `src/features/*/service/*.py`
  - [refactor_baseline.md](D:/PythonProject/TestFlowManager/docs/refactor_baseline.md)
  - [project_session_state_flow.md](D:/PythonProject/TestFlowManager/docs/project_session_state_flow.md)

- 风险：
  - 历史功能默认目录变化后，用户需要重新建立预期
  - 不同类型输出可能再次被混放

- 验收标准：
  - 已打开项目时，LLCR/CR 默认保存到项目下 `Test results`
  - 报告/Test Record/费用表目录职责有清晰文档说明
  - 新功能可直接复用统一目录规则，不再各自猜目录

#### T5-5 盘点剩余输出链并分类兜底点

- 状态：已完成

- 输出：
  - [output_path_inventory.md](D:/PythonProject/TestFlowManager/docs/output_path_inventory.md)

- 内容：
  - 已接入统一目录规则的链路
  - 仍保留 `D:\OutFile` 兜底的模块
  - 后续路径治理优先级

### 8.3 阶段验收

- 配置来源唯一
- 路径策略明确
- 文档不再误导配置位置
- 项目态输出目录职责明确且可回归验证

---

## 9. 阶段 6：测试基线重建

### 9.1 目标

- 让测试真正成为重构安全网

### 9.2 任务清单

#### T6-1 统一测试目录结构

- 建议结构：

```text
tests/
  unit/
  integration/
  gui_manual/
  fixtures/
```

- 任务：
  - 把脚本式或手工测试迁入 `gui_manual/`
  - 把自动化测试收敛到 `unit/` 和 `integration/`

- 涉及文件：
  - [pytest.ini](D:/PythonProject/TestFlowManager/pytest.ini)
  - `tests/*`

- 风险：
  - 搬迁后测试发现路径变化

- 验收标准：
  - 自动化测试目录边界清晰

#### T6-2 建立核心冒烟测试

- 优先覆盖：
  - `ConfigManager` 加载配置
  - 打开项目流程
  - Matrix 导入导出
  - LTR 申请数据处理

- 涉及文件：
  - [test_config_manager.py](D:/PythonProject/TestFlowManager/tests/test_config_manager.py)
  - [test_matrix_module.py](D:/PythonProject/TestFlowManager/tests/test_matrix_module.py)
  - [test_matrix_integration.py](D:/PythonProject/TestFlowManager/tests/integration/test_matrix_integration.py)
  - `tests/unit/*`
  - `tests/integration/*`

- 风险：
  - COM 依赖导致测试环境脆弱

- 验收标准：
  - 至少有一组不依赖真实 Office 进程的核心自动化测试

- 当前结果：
  - 已新增：
    - [test_project_contexts.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_contexts.py)
    - [test_project_open_service.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_open_service.py)
    - [test_config_manager.py](D:/PythonProject/TestFlowManager/tests/unit/test_config_manager.py)
    - [test_project_session_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_session_flow.py)
    - [test_project_creation_application_service.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_creation_application_service.py)
    - [test_main_window_open_project_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_main_window_open_project_flow.py)
    - [test_output_path_decisions.py](D:/PythonProject/TestFlowManager/tests/unit/test_output_path_decisions.py)
    - [test_project_creator_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_creator_flow.py)
  - 已覆盖：
    - `ProjectContext` 项目数据文件解析
    - `ProjectDocumentContext` 项目数据读取与 `Submitted Material / Test results / 项目工作目录` 解析
    - `OutputPathResolver` 项目态目录优先与全局兜底路径
    - `ProjectOpenService` 已有项目与补建 `application_data.json` 两条主路径
    - `ConfigManager` 的主配置与路径配置读取
    - `ProjectSessionService` 的状态写入与 `project.opened` 派发
    - `ProjectSessionCoordinator` 的主窗口标题、DL 显示、Matrix/Report 上下文注入与自动刷新调度
    - `Matrix 自动导入` 的非 GUI 编排边界：
      - 有工作区时自动导入 + 刷新 + 激活
      - 无工作区时跳过导入但保持安全调度
      - 自动导入异常时仍继续后续刷新/激活调度
    - `ProjectCreationApplicationService` 的新建项目后项目会话建立、LTR 加载、Matrix 初始化编排
    - `MainWindowController.handle_open_project()` 的非 GUI 主编排：
      - 用户取消
      - 已有项目直接打开
      - 补建 `application_data.json` 后进入基本信息对话框再重载
      - 异常时更新状态并提示错误
    - `MainWindowController._on_project_opened()` 的会话副作用解耦：
      - 无项目路径时忽略
      - 同项目重复事件时短路
      - 仅通过 `_apply_project_context()` 进入副作用编排
      - 当前实现下优先使用 `ProjectContext.from_event_data()`，本地 `_build_project_context()` fallback 实际不可达
    - 导出/生成链默认目录规则：
      - `LLCR / CR -> Test results`
      - `Test Record -> Submitted Material`
      - `Report Wizard -> Submitted Material`
      - `Fee Sheet -> 项目工作目录 / DL 子目录识别`
    - 新建项目主入口与创建后会话收口：
      - `MainWindowController.handle_new_file()`
      - `ProjectCreatorController.handle_create_new_project()`
      - `ProjectCreatorController._open_matrix_editor_with_ltr_number()`
      - 本地兜底副作用与主窗口主控制器存在时的分流
  - 已验证命令：
    - `python -m pytest tests/unit/test_project_contexts.py tests/unit/test_project_open_service.py -q`
    - `python -m pytest tests/unit/test_config_manager.py tests/unit/test_project_session_flow.py -q`
    - `python -m pytest tests/unit/test_project_creation_application_service.py -q`
    - `python -m pytest tests/unit/test_main_window_open_project_flow.py -q`
    - `python -m pytest tests/unit/test_output_path_decisions.py -q`
    - `python -m pytest tests/unit/test_project_creator_flow.py -q`
    - `python -m pytest tests/unit/test_project_contexts.py tests/unit/test_project_open_service.py tests/unit/test_config_manager.py tests/unit/test_project_session_flow.py tests/unit/test_project_creation_application_service.py tests/unit/test_main_window_open_project_flow.py tests/unit/test_output_path_decisions.py tests/unit/test_project_creator_flow.py -q`

#### T6-3 将 COM 依赖流程分层测试

- 建议分类：
  - 纯单元测试：mock COM
  - 集成测试：使用受控测试文件
  - 手工测试：真实 Office 环境

- 风险：
  - 现有测试混合真实依赖与脚本式试验

- 验收标准：
  - 各类测试目的清晰
  - pytest 默认执行不包含手工测试

### 9.3 阶段验收

- 默认测试集可稳定执行
- GUI 手工测试不再污染自动化测试目录
- 关键流程有最小冒烟覆盖

### 9.4 当前阶段进展

- 已开始阶段 6
- 第一批非 GUI 自动化回归已落地并通过
- 阶段 6 首轮目标已完成
- 下一批优先建议：
  - `Matrix 导出默认路径` 的独立规则测试
  - `ProjectCreatorController.handle_create_new_project()` 的更完整无 GUI 编排测试
  - 继续清理 `project_creator / main_window` 包级导出耦合

---

## 10. 推荐执行顺序

建议按以下顺序实施：

1. 阶段 1：壳层收口
2. 阶段 2：状态流收口
3. 阶段 3：Matrix 模块拆分
4. 阶段 4：Controller 瘦身
5. 阶段 5：配置与环境治理
6. 阶段 6：测试基线重建

原因：

- `main_window` 和 `matrix` 是最大耦合源
- 不先收边界，后续任何精细重构都会反复返工
- 配置和测试适合在边界收口后统一治理

---

## 11. 每阶段最小回归清单

### 阶段 1 后

- 应用能启动
- 能进入 Matrix 页面
- Matrix 表格可显示

### 阶段 2 后

- 打开项目后标题、状态、页面切换正常
- Matrix 自动导入正常

### 阶段 3 后

- Matrix 导入、编辑、导出正常
- 切项目不会出现旧状态残留

### 阶段 4 后

- 新建项目流程正常
- 打开项目流程正常
- `application_data.json` 自动补建正常
- 新建项目后能自动进入正确的项目会话并切回 Matrix

### 阶段 5 后

- 开发态配置加载正常
- 打包态路径策略未退化
- 已打开项目时：
  - LLCR/CR 默认目录为 `Test results`
  - 报告/Test Record 默认目录仍符合既有项目语义
  - 无项目态时才回退 `D:\OutFile`

### 阶段 6 后

- pytest 默认集合可运行
- 核心冒烟测试通过

---

## 12. 建议的首批实施任务

如果直接开始动手，建议先开以下 5 个任务：

1. 提取 `MatrixPage`，从主窗口迁出 Matrix UI 装配。
2. 建立主窗口页面注册机制，去掉主窗口对页面内部细节的感知。
3. 梳理 `project.opened` 和 `current_project` 的双通道依赖，形成状态/事件表。
4. 引入 `ProjectContext`，替代散落的 `project_path` 和 `dl_number`。
5. 给“打开项目”和“Matrix 自动导入”补一组最小回归测试。

---

## 13. 结论

这份看板的重点不是把重构任务拆得很细，而是先把顺序和边界做对。

优先级最高的不是“全面重写”，而是：

- 先把主窗口和 Matrix 分开
- 先把状态流理顺
- 再拆服务和 controller

只要这三步推进顺序正确，后续重构会从高风险不可控，转成可逐步交付。

## 14. 阶段 7 入口

当前已进入下一阶段结构收缩的准备动作：

- `matrix_service_provider.py` 已删除（Phase-11），不再作为共享 MatrixService 入口
- `MatrixController` 已改为要求显式注入 `matrix_service`（由 `MatrixSessionFactory` 装配）
- `report_wizard` 和 `test_record` 已改为 `MatrixController` 优先通道，页面层不再继续扩散
  `get_matrix_service()` 使用
- `report_wizard/test_spec_tables_service` 已不再直接从 provider 取 Matrix 数据，改为显式消费
  `matrix_headers / matrix_rows` 快照
- `test_spec_tables_page.py` / worker 已优先使用 `matrix_controller.get_project_context()` 与
  `get_matrix_headers()/get_matrix_rows()`
- `test_spec_tables_page.py` / worker 已移除对全局 `get_current_project_context()` 的直接回退
- `report_wizard_controller.py` / `report_wizard_dialog.py` 已将 `matrix_controller` 固定为主通路，
  `matrix_service` 仅保留兼容入口
- `test_record_controller.py` / `record_data_table_export_controller.py` /
  `fee_sheet_export_service.py` 也已移除对全局项目态的直接回退
- `report_updater_controller.py` / `report_updater_service.py` 初始化时也已不再主动抓取
  全局 `current_project_context`
- `matrix_controller.py` / `import_export_manager.py` 也已移除对全局项目态的直接回退
- `MatrixService` 已增加 `create_isolated()`，`MatrixSessionFactory` 不再直接硬绕过
  `MatrixService.__new__`
- `MatrixService` 的共享实例管理已从模块级全局变量迁到类属性
- `MatrixService()` 已不再默认返回共享实例，当前共享语义只保留在
  `MatrixService.shared()`
- 已引入 `MatrixSessionRegistry`（仅管理当前 shared/isolated service 路由选择），暂不默认启用
- `get_matrix_service()` 的外部消费已清零，当前只保留兼容出口
- `matrix_project_controller` 中对 `matrix_controller.service` 的最后一处直接写入已完成收口
- `MatrixImportService` 已作为第一块可用职责拆分落地，现已同时承接项目态
  `matrix.xlsx` 自动导入和 `spec` 导入链
- `MatrixApplicationService` 已开始承接导入应用流程与 `standardize_and_fill`
  主流程，controller / view manager 已通过它协调导入
- `spec` 导入后的后置处理策略已进入 `MatrixApplicationService`，当前实现为
  `refresh_only`
- `initialize_with_ltr_data()` 已下沉到 `MatrixApplicationService`
- `set_project_context()` / `set_ltr_data()` 已继续下沉到 `MatrixApplicationService`
- 已确认默认策略保持 `refresh_only`，当前不升级为 `refresh + initialize`
- `MatrixExportService` 已开始承接 `matrix.xlsx` 导出和关闭自动导出链
- `handle_export_matrix_to_excel()` 的非 UI 逻辑已继续下沉，controller 主要保留文件对话框和提示
- `handle_export_matrix_to_excel()` 已改为返回结构化结果，消息提示已收回 UI 层
- `LLCR/CR` 的应用编排已下沉到 `MatrixApplicationService / MatrixExportService`
- `MatrixController` 中重复持有的 `export_controller` 已移除
- `MatrixController / MatrixProjectController` 已支持显式注入，开始为后续 session 级装配做准备
- `MatrixSessionRegistry` 已成为 shared/isolated service 路由锚点（默认仍为 shared）
- `MatrixSessionFactory` 已支持 `shared / isolated` 两种装配模式，默认仍为 `shared`
- `matrix_session_switching_inventory.md` 已建立，用于约束何时可切 `isolated`
- 下一步最合适的是继续：
  - 继续收 `MatrixExportService` 与 `MatrixApplicationService` 的边界
  - 为后续 `MatrixApplicationService / MatrixImportService / MatrixExportService` 拆分做依赖注入准备
  - 继续减少 `get_current_project_context()` fallback
  - 继续收 `report_wizard` 页面层保留的 `matrix_service` 兼容入口
## Phase 7 Incremental Task Note (2026-04-10)

- Integrated `MatrixSessionRegistry` into `MatrixSessionFactory` as an explicit injection path.
- Added explicit factory injection options:
  - `registry`: mode-driven service selection (`shared` / `isolated`)
- Kept default behavior unchanged to avoid runtime regression:
  - no injection => shared service via `MatrixSessionRegistry` -> `MatrixService.shared()`
- Added unit coverage for injected `registry` / `provider` and conflict guarding.
- Wired a single `MatrixSessionRegistry` instance through composition:
  - `MainWindow` owns the registry instance
  - `MainWindowController` and `ProjectCreatorController` both pass that registry to `MatrixSessionFactory`
  - shared behavior remains unchanged, but session orchestration now has a single explicit anchor point
- Added a non-default isolated pilot entry:
  - controlled entry: `MainWindowController.handle_new_file()`
  - switch: `TFM_MATRIX_SESSION_ISOLATED_PILOT`
  - when enabled, `ProjectCreatorController` is assembled with `mode="isolated"` and no shared registry injection
- Removed `report_wizard` page-level legacy `matrix_service` compatibility path:
  - `ReportWizardController` now only accepts `matrix_controller`
  - `ReportWizardDialog` / `TestSpecTablesPage` now consume only controller snapshot + `ProjectContext`
- Removed `test_record_controller` page-level legacy `matrix_service` compatibility path:
  - `TestRecordController` now accepts `matrix_controller + project_context` only
  - matrix snapshot parsing is routed only through controller APIs
- Removed `MatrixController.get_matrix_service()` legacy compatibility API from mainline.
- Added cross-entry session isolation regression coverage:
  - shared entry -> isolated pilot entry -> shared entry
  - verifies isolated pilot does not affect shared service binding.
- Added session-id preparation capability in Matrix session assembly:
  - `MatrixSessionRegistry` supports `session_id`-scoped mode/service routing
  - `MatrixSessionFactory` supports optional `session_id` forwarding
  - default shared behavior is unchanged (`session_id=None` mainline path)
- Wired non-default isolated pilot entry with explicit session lifecycle:
  - `MainWindowController.handle_new_file()` uses fixed `session_id="pilot:new-file"` when pilot is on
  - `ProjectCreatorController.cleanup()` releases that isolated session id
  - covered by unit tests for pilot argument passing and release behavior
- Introduced `MatrixSessionScope` wrapper to reduce manual release handling:
  - `MatrixSessionRegistry.open_scope(session_id, mode=...)`
  - `ProjectCreatorController` now closes scope in cleanup (fallback release retained)
- Added a second non-default sessionized entry in `MainWindowController`:
  - isolated preview entry open/close APIs with `session_id`
  - added an env-gated preview pilot opener:
    - gate: `TFM_MATRIX_SESSION_ISOLATED_PREVIEW_PILOT`
    - fixed session id: `pilot:preview`
  - added a symmetric preview pilot close entry (same gate + fixed session id)
  - verified multi-scope coexistence and independent release in unit tests
- Added hidden debug command wiring (development mode only):
  - gated by `TFM_ENABLE_DEBUG_COMMANDS`
  - shortcut-triggered isolated preview open/close
  - no default navigation/menu behavior change

## Phase 7 Incremental Task Note (2026-04-10 Addendum: Compatibility Cleanup)

- Removed `BasicInfoDialog` parent fallback channel:
  - deleted `getattr(parent, "project_data_file_path", None)` path.
  - call sites now pass `project_data_file_path` explicitly where needed.
- Renamed `LTRProjectIntegrationService` canonical JSON-path channel:
  - `project_data_file_path` -> `project_json_path`
  - added explicit `get_project_json_path()` accessor
  - updated consumer logs in project creation and matrix project controller.
- Cleared legacy `project_data_file_path` residue in `matrix_service_backup.py`.
- Default shared behavior remains unchanged:
  - no session mode default change
  - no Matrix runtime behavior change on mainline paths.

## Phase 7 Incremental Task Note (2026-04-11 Addendum: Registry Diagnostics)

- Added `MatrixSessionRegistry` diagnostics baseline APIs:
  - `snapshot()`
  - `get_session_modes()`
  - `get_active_isolated_session_ids()`
- This provides explicit observability before Phase 8 multi-session object management.
- Added unit tests to ensure diagnostics are stable and read-only (copy semantics).

## Phase 8 Preparation Note (2026-04-11 Addendum: Session Manager Pilot)

- Introduced `MatrixSessionManager` as a lifecycle coordinator abstraction for explicit matrix sessions.
- Current usage is intentionally limited to non-default preview/debug entry points in `MainWindowController`.
- This establishes a minimal object-management seam (`create/get/close/list`) without changing default
  shared runtime behavior.

## Phase 8 Preparation Note (2026-04-11 Addendum: Debug Session Visibility)

- Added debug-only session-state visibility in `MainWindowController`:
  - `debug_get_matrix_session_state()`
  - debug open/close status publishing based on manager+registry snapshots
- Purpose: complete a non-default observability loop before wider session-entry rollout.

## Phase 8 Preparation Note (2026-04-11 Addendum: Entry Policy Table)

- Introduced lightweight `MatrixSessionEntryPolicyTable` and switched non-default entries to
  policy-driven mode/session-id resolution.
- Covered entries: `new_file_pilot`, `preview`, `debug_preview`.
- Mainline default shared behavior remains unchanged.
- Added injectable override hook for entry policy table in `MainWindowController`
  to support controlled experiments and test composition.

## Phase 8 Preparation Note (2026-04-11 Addendum: Policy Assembly Ownership)

- Moved session-entry policy-table ownership to the MainWindow composition layer:
  - `MainWindow` now builds one `MatrixSessionEntryPolicyTable` instance.
  - The same instance is injected into `MainWindowController` during controller assembly.
- Controller-level default fallback is retained as compatibility guard, but mainline composition
  now has an explicit single policy anchor point.
- Added assembly guard tests (AST-based) to ensure:
  - `MainWindow.__init__` creates `matrix_session_entry_policies`
  - `MainWindow._initialize_controllers` injects that policy table into `MainWindowController`.

## Phase 8 Preparation Note (2026-04-11 Addendum: Session Manager Assembly Ownership)

- Moved `MatrixSessionManager` ownership to MainWindow composition:
- Current runtime wiring: `MainWindow` (view) creates one `MatrixSessionManager(parent_view=self, registry=self.matrix_session_registry)`.
  Target wiring: move this assembly to app composition (`src/app/...`) and inject into `MainWindow`.
  - `MainWindow._initialize_controllers` injects it into `MainWindowController`.
- `MainWindowController` now supports explicit `matrix_session_manager=...` injection.
- Compatibility is retained:
  - controller keeps fallback construction (`MatrixSessionManager(...)`) when injection is absent.
- Added AST guard tests to lock this assembly contract and fallback shape.

## Phase 8 Preparation Note (2026-04-11 Addendum: Session Manager Diagnostics)

- Added manager-side diagnostics APIs on `MatrixSessionManager`:
  - `snapshot()`
  - `stats()`
- `MainWindowController.debug_get_matrix_session_state()` now prefers manager snapshot view
  for preview-session state, then aligns it with registry snapshot view in one payload.
- Existing debug keys are preserved; manager-oriented fields are added:
  - `manager_total_sessions`
  - `manager_session_modes`
  - `manager_active_isolated_session_ids`
- Added unit tests for:
  - manager snapshot/stats correctness and copy semantics
  - controller debug state preferring manager snapshot over list-based fallback.

## Phase 8 Preparation Note (2026-04-11 Addendum: Session Lifecycle Cleanup Hooks)

- Added explicit lifecycle cleanup APIs to `MatrixSessionManager`:
  - `close_by_mode(mode)`
  - `close_all()`
- Wired shutdown cleanup into `MainWindowController.shutdown()`:
  - cleanup non-default sessions first (`isolated` mode)
  - then continue existing auto-export / state-save / COM release flow
- Compatibility fallback:
  - if manager does not provide `close_by_mode`, controller falls back to `close_all`
- Added unit coverage for:
  - manager mode-targeted close behavior
  - manager full close behavior
  - controller shutdown cleanup ordering and fallback path.

## Phase 8 Preparation Note (2026-04-11 Addendum: Entry-Named Session Metadata)

- Extended `MatrixSessionManager` managed session model with optional `entry_name`.
- `create_or_get(...)` now accepts:
  - `entry_name` (non-default entry identity such as `preview` / `debug_preview`)
- Manager diagnostics now include entry dimension:
  - `snapshot().session_entries`
  - `snapshot().entry_counts`
  - `stats()['session_entries']`
  - `stats()['entry_counts']`
- `MainWindowController` now tags managerized entries explicitly:
  - preview path -> `entry_name="preview"`
  - debug preview path -> `entry_name="debug_preview"`
- Debug state payload adds manager entry-oriented fields:
  - `manager_session_entries`
  - `manager_entry_counts`
- Added unit coverage for entry metadata propagation and debug-state visibility.

## Phase 8 Preparation Note (2026-04-11 Addendum: Session Orchestrator Pilot)

- Added `MatrixSessionOrchestrator` as a minimal session-switch orchestration seam
  for non-default entries (preview/debug preview).
- `MainWindowController` session scheduling details were migrated to orchestrator:
  - preview open/close routes through orchestrator open/close APIs
  - debug preview session-id generation and last-session close targeting moved to orchestrator
- Controller keeps compatibility:
  - supports explicit orchestrator injection (`matrix_session_orchestrator=...`)
  - fallback construction remains in controller when injection is absent
- Added unit coverage for:
  - orchestrator open/switch/close behavior
  - debug preview id generation and close behavior
  - controller orchestrator injection/fallback structure.

## Phase 8 Preparation Note (2026-04-11 Addendum: Orchestrator Assembly Ownership)

- Current runtime wiring: `MatrixSessionOrchestrator` is assembled in `MainWindow` (view layer).
  Target wiring: move it to app composition (`src/app/...`) and inject into `MainWindow` / `MainWindowController`.
  - `MainWindow.__init__` now builds a single orchestrator from `matrix_session_manager`
  - `_initialize_controllers` injects orchestrator into `MainWindowController`
- This aligns session composition layers in shell assembly:
  - registry -> policy table -> session manager -> orchestrator -> controller
- Added AST assembly guard coverage to ensure:
  - UI creates `matrix_session_orchestrator`
  - UI injects it into `MainWindowController`.

## Phase 8 Preparation Note (2026-04-11 Addendum: Debug State Orchestration)

- Moved matrix session debug-state assembly from `MainWindowController` into
  `MatrixSessionOrchestrator.get_debug_state(registry_snapshot=...)`.
- `MainWindowController._build_matrix_session_debug_state()` now only:
  - retrieves optional registry snapshot
  - delegates state assembly to orchestrator
- Effect:
  - controller responsibility is reduced to orchestration call + status publishing
  - manager/registry debug-state merge logic is centralized in orchestrator.

## Phase 8 Preparation Note (2026-04-11 Addendum: Atomic Session Switch Semantics)

- Added structured switch result in orchestrator:
  - `SessionSwitchResult(success, session_id, reason, session)`
  - `switch_to_session(...)` now returns explicit outcome instead of raw nullable object
- Added controller-side debug explicit switch command:
  - `MainWindowController.debug_switch_isolated_matrix_preview_session(session_id)`
  - behavior:
    - debug mode disabled -> `False`
    - switch failed (`session_not_found` / `missing_session_id`) -> `False`
    - switch success -> publishes debug status and returns `True`
- Added unit coverage for:
  - orchestrator switch success/failure reasons
  - controller debug switch success/failure and status publish behavior.

## Phase 8 Preparation Note (2026-04-11 Addendum: Debug Switch Reachability)

- Added hidden debug shortcut entry in `MainWindow` for explicit preview-session switching:
  - action: `[DEBUG] Switch Isolated Matrix Preview`
  - shortcut: `Ctrl+Alt+Shift+J`
  - input: `Session ID` dialog
- Controller now exposes switch failure reason through status text:
  - `[debug:switch:failed] reason=<...> session_id=<...>`
- This closes the debug loop:
  - command is reachable from UI
  - failure reason is directly observable in status bar.

## Phase 8 Preparation Note (2026-04-11 Addendum: Debug Switch Confirmation Visibility)

- Upgraded debug switch success status text to include explicit confirmation:
  - `switched_to=<session_id>`
  - `entry=<entry_name>`
- `MatrixSessionOrchestrator` debug-state payload now includes:
  - `last_debug_preview_session_id`
- Purpose:
  - make manual switch operation verifiable from status bar + debug snapshot
  - keep controller as thin orchestration/display layer.

## Phase 8 Preparation Note (2026-04-11 Addendum: Debug Query Shortcut)

- Added hidden debug query shortcut in `MainWindow`:
  - action: `[DEBUG] Show Matrix Session State`
  - shortcut: `Ctrl+Alt+Shift+L`
- Query action calls `debug_get_matrix_session_state()` and shows concise snapshot:
  - active session ids
  - last debug preview session id
  - entry-level counts
- This completes debug operation loop for non-default session orchestration:
  - open / switch / query / close.

## Phase 8 Preparation Note (2026-04-11 Addendum: Debug Command Constants)

- Introduced centralized debug command constants/config:
  - `src/features/matrix/service/matrix_session_debug_commands.py`
- Centralized scope includes:
  - debug action labels
  - debug shortcuts
  - debug dialog titles/labels
  - debug status text formatters
  - debug query summary formatter
- `MainWindow` and `MainWindowController` now consume this table instead of hardcoded
  strings, reducing UI/controller string drift before promoting debug paths to formal entries.

## Phase 8 Preparation Note (2026-04-11 Addendum: Debug Facade Extraction)

- Added `MatrixSessionDebugFacade` to consolidate non-default debug entry operations:
  - preview open/close
  - debug preview open/close
  - debug switch
  - debug snapshot query
- `MainWindowController` now delegates these operations to facade and keeps:
  - debug-mode guard checks
  - status publishing / UI-facing side effects
- `MainWindow` composition now explicitly assembles and injects:
  - `matrix_session_debug_facade`.

## Phase 8 Preparation Note (2026-04-11 Addendum: New-File Entry Facade)

- Added `MatrixSessionEntryFacade` to centralize entry-policy resolution for
  non-debug business entry points.
- First migrated target:
  - `MainWindowController.handle_new_file()` no longer reads `new_file_pilot`
    policy directly; it now calls facade to resolve session mode/session_id.
- `MainWindow` composition now also assembles and injects:
  - `matrix_session_entry_facade`
- Result:
  - controller no longer carries direct entry-policy decision branches for new-file path
  - session-entry strategy continues converging toward facade-based orchestration.

## Phase 8 Preparation Note (2026-04-11 Addendum: Controller Legacy Helper Cleanup)

- Removed obsolete controller helper:
  - `_get_matrix_session_entry_policy(...)` in `MainWindowController`
- Rationale:
  - after introducing `MatrixSessionEntryFacade` + `MatrixSessionDebugFacade`, direct
    controller policy lookup path is no longer used.
- Effect:
  - controller session-entry concerns are further reduced to facade delegation + orchestration.

## Phase 8 Milestone Acceptance (2026-04-11)

Status: Completed

Acceptance summary:
- Non-default matrix session path has been fully moved to composed seams:
  - policy table
  - manager
  - orchestrator
  - debug/entry facades
- MainWindow assembly root now explicitly injects all sessionized dependencies into controller.
- MainWindowController has completed baseline slimming for non-default session flows:
  - no direct new-file pilot policy branch
  - no legacy direct policy helper path
  - debug commands are centralized and observable (open/switch/query/close).
- Debug observability loop is complete:
  - status publish (success/failure)
  - snapshot query
  - last debug session id visibility.

Phase 9 entry gates:
1. Keep default `shared` path as stable baseline (no behavior migration by default).
2. Promote one hidden debug entry to controlled non-debug pilot entry with explicit product gate.
3. Define formal session-switch contract for page-level consumers (who can switch, when, and rollback semantics).
4. Add targeted integration checks for:
   - new-file pilot isolation consistency
   - preview/debug multi-session coexistence
   - shutdown cleanup correctness under mixed session sets.
5. Decide deprecation timeline for debug-only shortcuts once formal entry is available.

---

## 12. 阶段 9：正式会话化过渡（已完成）

### 12.1 阶段目标

- 保持默认 `shared` 主线行为不变
- 将“可观测的 debug 会话能力”升级为“受控、可回滚的业务试点能力”
- 在不引入 UI 大改的前提下，冻结会话切换契约并建立回归口径

### 12.2 可执行任务清单

#### T9-1 建立一个受控正式入口（非默认）

- 状态：已完成（2026-04-11）

- 任务：
  - 选择一个低风险入口作为正式试点（默认推荐 `new_file_pilot`）
  - 保留 feature gate，默认关闭；仅开关打开时走 `isolated`
  - 关闭时完整回退到 `shared`
- 涉及文件：
  - [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
  - [matrix_session_entry_facade.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_session_entry_facade.py)
  - [matrix_session_entry_policy.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_session_entry_policy.py)
- 主要风险：
  - 入口策略漂移导致默认行为被动改变
- 验收标准：
  - 开关关闭时行为与当前主线一致
  - 开关开启时可创建并释放 isolated session
  - 有对应单元测试覆盖开关 on/off 两条路径

- 当前结果：
  - `new_file_pilot` 开关解析已收口到 `MatrixSessionEntryFacade`（显式 product gate）
  - `MainWindowController` 不再直接解析该开关字符串，改为委托 facade
  - 已补 gate 默认关闭与 truthy 开启测试，且与新建项目入口回归测试一起通过

#### T9-2 冻结会话切换契约

- 状态：已完成（2026-04-11）

- 任务：
  - 固化 `switch_to_session` 的返回语义（成功、失败原因、目标 id、entry 标识）
  - 明确谁可以发起切换，何时允许切换，失败时如何回滚
  - 统一由 orchestrator/facade 暴露，不允许页面层自行拼接切换逻辑
- 涉及文件：
  - [matrix_session_orchestrator.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_session_orchestrator.py)
  - [matrix_session_debug_facade.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_session_debug_facade.py)
  - [main_window_controller.py](D:/PythonProject/TestFlowManager/src/features/main_window/controller/main_window_controller.py)
- 主要风险：
  - 多入口并发切换时语义不一致
- 验收标准：
  - 切换契约在文档中有明确条目
  - 失败原因枚举稳定，不再出现隐式 `None` 语义
  - 相关单元测试稳定通过

- 当前结果：
  - `MatrixSessionOrchestrator.switch_to_session(...)` 已固化契约参数：
    - `expected_entry_names`
    - `requested_by`
  - 失败原因已收敛为常量语义：
    - `missing_session_id`
    - `session_not_found`
    - `entry_not_allowed`
    - `activation_failed`
  - 切换结果已明确携带契约字段：
    - `requested_by`
    - `previous_active_session_id`
    - `active_session_id`
    - `rollback_performed`
  - `MatrixSessionDebugFacade` 已固定 preview/debug 可切换 entry 白名单并透传调用方标识
  - `MatrixSessionManager` 已增加 `activate()/get_active_session_id()`，用于切换激活语义对齐

#### T9-3 补齐三类集成回归

- 状态：已完成（2026-04-11）

- 任务：
  - 新建文件试点隔离一致性（shared -> isolated -> shared）
  - preview/debug 多会话并存与独立关闭
  - shutdown 在 mixed session 集合下的清理顺序与结果
- 涉及文件：
  - [test_project_creator_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_creator_flow.py)
  - [test_matrix_session_manager.py](D:/PythonProject/TestFlowManager/tests/unit/test_matrix_session_manager.py)
  - [test_matrix_session_orchestrator.py](D:/PythonProject/TestFlowManager/tests/unit/test_matrix_session_orchestrator.py)
  - [test_main_window_controller_session_manager_injection.py](D:/PythonProject/TestFlowManager/tests/unit/test_main_window_controller_session_manager_injection.py)
- 主要风险：
  - 缺乏跨入口验证导致后续 Phase 10 返工
- 验收标准：
  - 3 类场景均有自动化测试
  - 与会话相关测试集可独立运行通过

- 当前结果：
  - 已新增集成测试文件：
    - [test_matrix_session_transition_flow.py](D:/PythonProject/TestFlowManager/tests/integration/test_matrix_session_transition_flow.py)
  - 新增覆盖场景：
    - shared -> isolated(new_file_pilot) -> shared 切换一致性
    - preview/debug_preview 多会话并存与独立关闭
    - mixed session 集合下仅清理 isolated（保留 shared）
  - 与现有 unit 会话测试组合执行通过（59 passed）

#### T9-4 兼容层收缩与守卫

- 状态：已完成（2026-04-11）

- 任务：
  - 清理 registry 外部的 shared service 访问残留
  - 禁止新增绕过 `MatrixSessionRegistry` 的访问点
  - 更新兼容清单，标记可删除和保留项
- 涉及文件：
  - [refactor_compatibility_backlog.md](D:/PythonProject/TestFlowManager/docs/refactor_compatibility_backlog.md)
  - [test_matrix_service_access_guard.py](D:/PythonProject/TestFlowManager/tests/unit/test_matrix_service_access_guard.py)
- 主要风险：
  - 旧通道未完全收口导致行为分叉
- 验收标准：
  - 兼容清单有“已删除/暂保留”状态
  - guard 测试可阻止新直连访问回归

- 当前结果：
  - `MatrixService` 直连 import 白名单守卫保持生效（仅允许 `MatrixSessionRegistry`）
  - `MatrixServiceProvider.get_service()` / switch methods 在 `src/` 下调用点必须为 0（guard 覆盖）
  - 兼容清单已同步记录该守卫与当前结论

#### T9-5 debug 通道退役策略

- 状态：已完成（2026-04-11）

- 任务：
  - 定义 debug-only 快捷键保留周期
  - 明确何时从“调试通道”迁移到“正式入口”
  - 保留必要诊断能力但不作为业务入口依赖
- 涉及文件：
  - [matrix_session_switching_inventory.md](D:/PythonProject/TestFlowManager/docs/matrix_session_switching_inventory.md)
  - [main_window_ui.py](D:/PythonProject/TestFlowManager/src/features/main_window/view/main_window_ui.py)
  - [matrix_session_debug_commands.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/matrix_session_debug_commands.py)
- 主要风险：
  - 正式入口上线后仍长期依赖 debug 交互
- 验收标准：
  - 有明确退役时点或退役条件
  - 文档与代码入口策略一致

- 当前结果：
  - 已明确 debug-only 通道定位：
    - 仅用于 phase-9 过渡期诊断，不作为正式业务入口
    - 继续由 `TFM_ENABLE_DEBUG_COMMANDS` 显式开关控制
  - 已定义退役条件：
    - 至少一个正式非 debug 入口稳定上线
    - phase-9 回归口径连续通过
    - session 切换契约在非 debug 消费方稳定一轮迭代
  - 已定义 phase-10 动作：
    - 从 `MainWindow` 移除 debug 快捷入口注册
    - 保留必要诊断能力到测试/日志通道，不再暴露快捷菜单入口

### 12.3 阶段 9 回归口径（最小集）

- `python -m pytest tests/unit/test_matrix_session_registry.py tests/unit/test_matrix_session_factory.py -q`
- `python -m pytest tests/unit/test_matrix_session_manager.py tests/unit/test_matrix_session_orchestrator.py -q`
- `python -m pytest tests/unit/test_matrix_session_entry_facade.py tests/unit/test_matrix_session_debug_facade.py -q`
- `python -m pytest tests/unit/test_project_creator_flow.py tests/unit/test_main_window_controller_session_manager_injection.py -q`

### 12.4 阶段 9 退出条件

- 默认 shared 主线行为稳定，无回归
- 至少一个受控正式入口可用，且可关闭回退
- 会话切换契约冻结并被测试锁定
- debug-only 通道退役策略已确定

### 12.5 阶段结论

- `T9-1` ~ `T9-5` 已全部完成。
- 默认 `shared` 主线行为保持稳定。
- 下一阶段进入 `Phase 10`：多会话对象管理。

---

## 13. 阶段 10：多会话对象管理（进行中）

### 13.1 阶段目标

- 将当前“非默认路径会话化”扩展到页面级可管理会话
- 建立可控的多会话生命周期（创建、激活、切换、关闭、回收）
- 在业务入口稳定后逐步移除过渡兼容层

### 13.2 预置任务（草案）

- T10-1 页面级 session 绑定模型（MatrixPage/Workspace 与 session_id 显式关联）【已完成 2026-04-11】
- T10-2 会话注册与激活策略（active session 与可见页面一致性）【已完成 2026-04-11】
- T10-3 会话清理策略（shutdown、入口退出、异常回滚）【已完成 2026-04-11】
- T10-4 兼容层退役（debug-only 快捷入口、临时 fallback）【已完成 2026-04-11】
- T10-5 集成回归升级（跨入口、多页面、混合会话集合）【已完成 2026-04-11】

### 13.2.1 T10-1 当前结果

- `MatrixSessionManager` 已增加页面绑定能力：
  - `bind_page_session(page_id, session_id)`
  - `unbind_page_session(page_id)`
  - `get_page_session_id(page_id)`
  - `get_page_session_bindings()`
- manager snapshot/stats 已暴露 `page_session_bindings`，并在 session close 时自动解绑关联页面。
- `MatrixSessionOrchestrator` 已增加页面绑定入口：
  - `bind_page_session(...)`
  - `get_bound_session_for_page(...)`
- `MatrixPage` 已增加 session 绑定元数据接口：
  - `bind_session(...)`
  - `clear_session_binding()`
  - `get_session_binding()`
- `MainWindow` 在初始化 `MatrixPage` 时，已通过 controller 注入当前工作区绑定元数据。
- 当前实现为“元数据绑定模型”，不改变默认 shared 业务行为。

### 13.2.2 T10-2 当前结果

- `MainWindowController` 已新增页面可见性一致性策略入口：
  - `ensure_matrix_workspace_session_consistency(page_id="matrix.main")`
- 策略行为：
  - 页面无绑定且有 active session 时，自动将页面绑定到 active session
  - 页面绑定与 active 不一致时，统一走 orchestrator 切换契约：
    - `bind_page_session(...)`
    - 透传 `expected_entry_names` 与 `requested_by`
  - 切换失败时保留 rollback 语义并返回结构化结果
  - 无 active 且无绑定时维持默认 shared 绑定语义
- `MainWindow._on_page_changed_for_matrix(...)` 已在页面切换时触发该一致性检查，
  并同步更新 `MatrixPage` 的 session 绑定元数据。
- 当前策略为“可见页面一致性收口”，未改变默认 shared 主线行为。

### 13.2.3 T10-3 当前结果

- 页面退出清理：
  - `MainWindow._on_page_changed_for_matrix(...)` 在离开 Matrix 页时调用
    `MainWindowController.handle_matrix_workspace_hidden()`，
    释放 `matrix.main` 的页面绑定。
- shutdown 清理：
  - `MainWindowController.shutdown()` 在关闭 isolated session 前，
    会先清理所有页面绑定映射（若 manager 支持 `clear_page_session_bindings`）。
- manager 清理能力：
  - `MatrixSessionManager.clear_page_session_bindings()` 已提供统一页面绑定清理入口。
- 语义约束：
  - 页面解绑不等于 session 关闭；
  - session 生命周期仍由 manager/orchestrator 统一管理；
  - 切换失败回滚语义继续由 T10-2 契约结果承载。

### 13.2.4 T10-4 当前结果（完成）

- `MainWindow` 已移除 legacy debug UI 快捷入口注册与对应 handler（open/close/switch/query）。
- `MainWindow` UI 层不再依赖 `TFM_ENABLE_DEBUG_COMMANDS_UI`，不再暴露隐藏 debug 快捷键入口。
- `MainWindowController` 已移除 `_is_legacy_debug_ui_enabled()`；`matrix_session_debug_commands.py` 已移除 `LEGACY_UI_GATE` 常量。
- `matrix_session_debug_commands.py` 已移除仅 UI 使用的 action/shortcut/dialog 常量与 `format_query_message`，仅保留 controller 使用的状态格式化函数。
- 非 UI 诊断能力保留：
  - `MainWindowController` debug API 仍可用于测试与日志诊断；
  - `matrix_session_debug_commands.py` 仍作为 controller/status 文本常量表。
- 结果：debug 通道从“UI 可触发”收敛为“代码/测试可触发”，满足 phase-10 兼容层退役目标。

### 13.2.5 T10-5 当前结果

- 新增 phase-10 集成回归文件：
  - [test_matrix_workspace_session_consistency_flow.py](D:/PythonProject/TestFlowManager/tests/integration/test_matrix_workspace_session_consistency_flow.py)
- 覆盖场景：
  - 页面绑定与 active session 不一致时的切换一致性
  - 页面绑定 entry 不可切换时的回滚语义（`entry_not_allowed`）
  - shutdown 下“先清页面绑定、再关 isolated、保留 shared”的混合集合清理
- 与既有 phase-9/10 套件组合执行通过（66 passed）。

### 13.3 启动前置条件

- Phase 9 全部退出条件达成
- 会话切换契约稳定至少一个迭代周期
- 关键业务链路（打开项目/新建项目/导入导出）无新增行为回归

### 13.4 阶段 10 验收结论（2026-04-11）

- `T10-1` ~ `T10-5` 已全部完成，且完成了 UI/Controller 两层 debug 兼容退役收口。
- 默认 `shared` 主线行为保持不变；非默认会话路径具备页面绑定一致性、切换回滚和清理顺序保障。
- Phase 9/10 回归口径已集中验证通过（2026-04-11）：
  - `tests/unit/test_matrix_session_registry.py`
  - `tests/unit/test_matrix_session_factory.py`
  - `tests/unit/test_matrix_session_manager.py`
  - `tests/unit/test_matrix_session_orchestrator.py`
  - `tests/unit/test_matrix_session_entry_facade.py`
  - `tests/unit/test_matrix_session_debug_facade.py`
  - `tests/unit/test_project_creator_flow.py`
  - `tests/unit/test_main_window_controller_session_manager_injection.py`
  - `tests/unit/test_main_window_ui_session_policy_assembly.py`
  - `tests/integration/test_matrix_session_transition_flow.py`
  - `tests/integration/test_matrix_workspace_session_consistency_flow.py`
  - 执行结果：`119 passed`

### 13.5 下一阶段入口（Phase 11 候选）

- 将 `refactor_compatibility_backlog.md` 中剩余兼容收口项转为阶段化任务（优先清理/防止 `MatrixServiceProvider.*` 残留调用面回归）。
- 评估并确定“正式非 debug 多会话业务入口”扩展点（在不改变默认 `shared` 的前提下）。
- 对会话切换契约补充跨模块消费边界测试（避免新入口直接绕过 orchestrator/facade）。

### 13.6 Phase 11 主线完成验收清单（必须同时满足）

- 默认行为不变：所有 pilot 开关关闭时，关键链路（打开项目/新建项目/Matrix 导入导出/报告入口）按既有 shared 基线运行。
- 装配收口：`MatrixController`/`MatrixProjectController` 必须显式注入，且只能通过 `MatrixSessionFactory` 装配（assembly guard 覆盖）。
- 会话闭环（受控入口）：至少 `new_file_pilot` 与 `preview_pilot` 具备 open/close，且关闭后不遗留 page binding 或 active session 指向 pilot（回归覆盖）。
- 一致性与回滚：页面切换触发的 active/binding 一致性校验生效；不允许 entry 时必须回滚且保留原 active（integration 覆盖）。
- 兼容面守卫：`MatrixServiceProvider.*` 在 `src/` 下调用点保持为 0；`MatrixService` 直连 import 仅允许在 `MatrixSessionRegistry`（guard 覆盖）。

验收回归结论（2026-04-11）：通过。

- 回归命令：
  - `python -m pytest -q tests/unit/test_matrix_session_registry.py tests/unit/test_matrix_session_factory.py tests/unit/test_matrix_session_manager.py tests/unit/test_matrix_session_orchestrator.py tests/unit/test_matrix_session_entry_facade.py tests/unit/test_matrix_session_debug_facade.py tests/unit/test_project_creator_flow.py tests/unit/test_main_window_controller_session_manager_injection.py tests/unit/test_main_window_ui_session_policy_assembly.py tests/unit/test_main_window_open_project_flow.py tests/unit/test_project_session_flow.py tests/unit/test_project_creation_application_service.py tests/unit/test_project_open_side_effects_guard.py tests/unit/test_project_session_open_project_guard.py tests/unit/test_project_open_event_dispatch_guard.py tests/unit/test_project_open_title_guard.py tests/unit/test_project_session_state_guard.py tests/unit/test_matrix_service_provider_guard.py tests/integration/test_matrix_session_transition_flow.py tests/integration/test_matrix_workspace_session_consistency_flow.py`
- 执行结果：`144 passed`
- 测试隔离修复（避免收集顺序导致 sys.modules 污染）：
  - `tests/unit/test_main_window_open_project_flow.py`
  - `tests/unit/test_project_creator_flow.py`

### 13.7 Phase 12 打开项目链路收口（已完成）

- 触发侧收口：`MainWindowController.handle_open_project()` 只负责 `prepare_project(...)` + `project_session_service.apply_project_context(...)`，不直接编排 UI/Matrix 自动导入/标题等副作用。
- 副作用单点化：所有 project-open 副作用只允许从 `project.opened` 事件消费侧进入，并由 `ProjectSessionCoordinator.apply_project_context(...)` 统一编排（本地 fallback 例外：`ProjectCreatorController` 在没有 MainWindowController 时允许兜底）。
- 回归守卫：新增 AST guard，防止其他入口再次直接调用 `project_session_coordinator.apply_project_context(...)` 绕过 `project.opened` 链路：
  - `tests/unit/test_project_open_side_effects_guard.py`
- 兼容口收缩：禁止 `src/` 内再使用 `project_session_service.open_project(...)`（仅允许在 `ProjectSessionService` 内保留该 legacy helper）：
  - `tests/unit/test_project_session_open_project_guard.py`
- 事件派发守卫：禁止 `src/` 内直接 `event_dispatcher.dispatch('project.opened', ...)`，统一从 `ProjectSessionService.apply_project_context(...)` 触发：
  - `tests/unit/test_project_open_event_dispatch_guard.py`
- 副作用继续收敛：窗口标题 `TestFlow Manager - 项目: ...` 只能由 `ProjectSessionCoordinator.apply_project_context(...)` 设置（guard 覆盖）：
  - `tests/unit/test_project_open_title_guard.py`

### 13.8 Phase 13 兼容收口任务化（进行中）

阶段目标：

- 将剩余兼容点从“文档描述/历史惯性”转成“可执行任务 + 验收标准 + 回归/guard”。
- 优先消灭会导致主线回退的兼容面：
  - 入口绕过（绕过 factory/orchestrator/coordinator）
  - 触发侧编排副作用（绕过 `project.opened` 消费侧）
  - 隐式全局通道回流（重新引入 provider/singleton bypass）

任务清单（按回退风险从高到低排序）：

- T13-1 ProjectCreator shared-mode 侧副作用收敛（已完成 2026-04-11）
  - 内容：当主窗口控制器存在且 `matrix_session_mode="shared"` 时，`ProjectCreatorController` 不再重复编排 Matrix 刷新/上下文写入；仅在本地兜底或 `isolated` pilot 下保留本地 Matrix 侧上下文应用。
  - 验收：
    - `tests/unit/test_project_creator_flow.py` 覆盖 shared/local/isolated 三种分支并通过。
    - 不引入新的 `project_session_coordinator.apply_project_context(...)` 非受控调用点（既有 guard 通过）。

- T13-2 Session/Project 文档盘点校准（已完成 2026-04-11）
  - 内容：复核 session/context 相关文档（`project_session_state_flow.md`、`matrix_session_switching_inventory.md`、`refactor_compatibility_backlog.md`）中“已移除/已收口”的描述，避免文档滞后误导下一步拆分。
  - 验收：
    - 文档中的“残留点清单”与代码检索一致（至少覆盖：`matrix_service` 兼容入口、`get_current_project_context` fallback、provider 模块残留）。
  - 当前进展（2026-04-11）：
    - `docs/project_session_state_flow.md` 明确记录当前只剩下 `ProjectContext` + `project.opened` 主线，剩余状态事件通道仅用于兼容记录。
    - `docs/matrix_session_switching_inventory.md` 与 `docs/refactor_compatibility_backlog.md` 都同步了新的 `MatrixWorkspaceCoordinator`/`src/app/composition/main_window_assembler.py` 装配路径，并把剩余兼容点收敛到文档层（code path 清单为零）。

- T13-3 测试装配 stub 污染治理（已完成 2026-04-11）
  - 内容：将单测中对 `sys.modules` 的导入期 stub 注入统一收口为“导入期生效、导入后还原”的模式，避免收集顺序导致的跨文件污染，保证回归口径稳定可重复。
  - 验收：
    - Phase 11/12 最小回归集可重复运行通过（不依赖测试收集顺序）。
    - 关键 stub 文件不再永久覆盖 `src.core.*` 模块（尤其 `src.core.logger`、`src.core.project_session_service`）。
  - 当前进展（2026-04-11）：
    - 已修复：`tests/unit/test_main_window_open_project_flow.py`、`tests/unit/test_project_creator_flow.py`、`tests/unit/test_matrix_service_singleton_access.py`
    - 已修复：`tests/unit/test_matrix_session_factory.py`、`tests/unit/test_matrix_session_registry.py`、`tests/unit/test_matrix_session_manager.py`
    - 已修复：`tests/unit/test_matrix_project_controller.py`、`tests/unit/test_output_path_decisions.py`
    - 交叉顺序回归（正序/逆序）通过：`128 passed`

- T13-4 主窗口 Matrix 会话栈装配权迁移到 app composition（已完成 2026-04-11）
  - 内容：将 `MatrixSessionRegistry/Manager/Orchestrator/*Facade` 的默认装配从 `MainWindow`(view) 迁移到 `src/app` 的 composition/assembler，并通过显式注入传递到 `MainWindow`/`MainWindowController`，保持默认 shared 行为不变。
  - 验收：
    - `src/app/application.py:create_main_window` 通过 `assemble_main_window()` 构造 `MatrixWorkspaceCoordinator` 并让 `MainWindow`/`MainWindowController` 都通过该 coordinator 获取 manager/orchestrator/entry facades。
    - `MainWindow` 与 `MainWindowController` 只通过注入接口交给 coordinator 绑定 parent view，避免重复创建 session manager。
    - 原有 session switching / pilot / guard 回归集通过（Phase 11/12 最小集合 + `test_main_window_controller_session_manager_injection.py`）。

## 14. Phase 14 Guard Lockdown（2026-04-11）

- 目标：把所有旧的事件、状态和 provider 通道彻底封死，只保留 `MatrixSessionFactory`/`ProjectSessionCoordinator`+`ProjectContext` 主线，避免未来代码重新绕过 Guard。
- T14-1：新增 guard `tests/unit/test_project_session_state_guard.py`，限制 `state_manager.set_state("current_project_context", …)` 只能在 `src/core/project_session_service.py` 发生。
- T14-2：新增 guard `tests/unit/test_matrix_service_provider_guard.py`，确保 `MatrixServiceProvider` 不出现在 `src/`，保持 Phase-11 guard 的 “provider 调用点为 0” 断言。
- 验收：这两条 guard 与 Phase‑12/Phase‑13 回归集一起运行（Phase 11/12 最小集合 +  guard tests），任何旧 channel 重现都会在 CI 阶段被拒。
- CI 增加了 `Phase 14 Guard Lockdown` workflow（`.github/workflows/phase14-guard-lockdown.yml`），在 `windows-latest` 上跑 `tools/run_phase14_guard_regression.ps1`，确保 guard tests 与 Phase 11/12 回归同步。

## 15. Phase 15 Report Export Boundary Cleanup（2026-04-12）

- 目标：在 Phase 14 guard 奠定的 `ProjectContext + project.opened` 主线之上，把报告生成/更新的业务组合交给 `ReportExportCoordinator`，让 `ReportWizardController` 与 `ReportUpdaterController` 只负责 UI 输入/反馈、显式注入 `ProjectContext` + `MatrixController`，所有输出路径与 COM 操作都由 coordinator/service 组合处理，彻底淘汰 `ProjectContext.from_project_path` 的隐式补偿。
- T15-1：让 `ReportWizardController` 不再直接实例化 `ReportGenerationService`，而是通过 coordinator 回调生成报告文档；`ReportWizardDialog` 只接收 controller 注入的回调，负责展示结果并把 `matrix_controller`/`project_context` 传给下游页。
- T15-2：让 `ReportUpdaterController`/`ReportUpdaterData` 只接受 `ProjectContext` 并把上下文透传给 coordinator，`ReportUpdaterService` 也只在明确的 `ProjectContext` 下工作；最终的 guard+regression 套件继续跑通 Phase 11/12+Phase 14 guard（`tools/run_phase14_guard_regression.ps1` 最新一次 2026-04-12 运行成功 143 条测试），确保旧通道不会复活。
- 验收标准：
  1. `ReportWizardController`/`ReportUpdaterController` 代码中不再出现 `ProjectContext.from_project_path`，所有项目上下文在 controller 层由 `MainWindow` 注入。
  2. `ReportGenerationService`/`ReportUpdaterService` 只依赖 `ProjectContext`，`ReportWizardDialog` 通过 coordinator 回调创建报告。
  3. `tools/run_phase14_guard_regression.ps1` 最新一次运行（2026-04-12）包含 143 条测试并全部通过，说明 guard suite 与 Phase 15 协作已稳定。
  4. QA 可通过 `docs/tasks/phase15_report_export.md` 中记录的步骤重现报告创建/更新流程。
  5. 文档里明确 `ReportExportCoordinator` 是 `ReportWizard`/`ReportUpdater` 的统一入口，便于未来 isolated entry 拓展。
