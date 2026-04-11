# Project Session State Flow

本文件用于描述当前项目“项目会话”相关的真实状态流，以及下一阶段的收口方案。

## 1. 目标

项目最终目标不是单独编辑 Matrix，而是：

1. 创建或打开项目
2. 基于 Matrix 生成相关测试表格
3. 将相关表格或 Matrix 结构化数据带入报告
4. 自动生成或更新测试报告

因此项目会话状态流必须满足：

- 项目上下文只有一个真来源
- Matrix、导出、报告、Test Record 共用同一项目会话
- 新功能不需要自行猜测项目路径或 JSON 路径
- 状态变化不会重复触发 UI、导入、导出链路

## 2. 当前真实通道

当前与“项目打开 / 切换”相关的主通道有三类：

### 2.1 状态

- `current_project_context`
- `application_status`

### 2.2 事件

- `project.opened`
- `state.changed`

### 2.3 本地控制器状态

- `MainWindowController._project_context`

## 3. 当前写入点

### 3.1 ProjectSessionService（统一入口）

- 写入：
  - `state_manager.set_state("current_project_context", project_context)`
  - `event_dispatcher.dispatch("project.opened", project_context.to_event_data())`

### 3.2 控制器侧

- `MainWindowController` 和 `ProjectCreatorController` 不再直接写项目会话状态
- 两者统一调用 `ProjectSessionService`

## 4. 当前消费点

### 4.1 MainWindowController

- 订阅：
  - `project.opened`
  - `state.changed`
- 当前阶段收口后：
  - `project.opened` 成为项目打开主事件
  - `state.changed` 仅保留 `current_project_context` 的兜底同步
  - `state.changed/current_project` 不再驱动项目打开主流程

### 4.2 其他模块

- 多数主链路已改为直接读取 `ProjectContext`

## 5. 收口后的规则

### 5.1 唯一项目会话状态

- 真状态：`current_project_context`
- 类型：`ProjectContext`

### 5.2 一次性项目打开事件

- 事件：`project.opened`
- 作用：通知“项目会话已建立”

## 6. 设计约束

后续新增功能默认遵守：

1. 写项目会话时，先写 `ProjectContext`
2. 读取项目会话时，优先读 `ProjectContext`
3. 不允许新功能再监听 `state.changed/current_project` 触发主业务动作
4. `project.opened` 只表达“一次性项目打开完成”
5. 任何导出、报告、生成流程都不再自己拼项目路径

配置目录约束：

- 开发态配置目录：`src/app/config`
- 打包态外部配置目录：`D:\TestFlowManager\config`
- 仓库根目录下的 `config/` 不再作为有效配置来源

## 6.1 输出目录策略

项目会话建立后，导出/生成链路默认按以下目录语义落盘：

- `Submitted Material`
  - 用途：项目交付物、报告附件、Test Record、报告向导生成报告等“提交材料型”输出
  - 位置：`<项目工作目录>/Submitted Material`
  - 代表能力：
    - `ProjectDocumentContext.get_submitted_material_dir()`
    - `ProjectDocumentContext.build_submitted_material_output_path()`
    - `OutputPathResolver.resolve_submitted_material_dir()`

- `Test results`
  - 用途：LLCR、CR、后续测试结果类 Excel 导出
  - 位置：`<项目工作目录>/Test results`
  - 代表能力：
    - `ProjectDocumentContext.get_test_results_dir()`
    - `OutputPathResolver.resolve_test_results_dir()`

- 项目子目录 / 项目工作目录
  - 用途：费用表、项目主资料、与具体项目目录结构强绑定的输出
  - 位置：
    - 优先 `<项目目录>/<DL 开头子目录>`
    - 无子目录时回退 `<项目目录>`
  - 代表能力：
    - `ProjectDocumentContext.get_project_workspace_dir()`
    - `OutputPathResolver.resolve_project_workspace_dir()`

- 全局兜底 `D:\OutFile`
  - 用途：仅在“当前没有项目会话”或“项目目录解析失败”时作为兜底输出/选择目录
  - 约束：
    - 不允许在已有 `ProjectContext` 的主链路里优先落到该目录
    - 后续新功能若仍使用该目录，必须明确说明是“无项目态兜底”

新增导出/生成功能默认按以下顺序选目录：

1. 先取 `ProjectContext`
2. 再由 `OutputPathResolver` / `ProjectDocumentContext` 解析目标目录
3. 只有解析失败时才回退 `D:\OutFile`

## 7. 当前阶段结果

- `ProjectContext` 已成为主线项目会话来源
- `MainWindowController` 不再依赖 `state.changed/current_project` 驱动项目打开主流程
- `project.opened + current_project_context` 已成为当前主线
- `current_project` 已退出主线写入与消费
- `ProjectSessionService` 已成为项目会话统一写入口
- 已引入 `ProjectSessionCoordinator`，统一编排项目会话建立后的 UI/Matrix/Report 副作用
- `ProjectOpenService` 已承接“打开已有项目”主流程中的项目数据补建与 `ProjectContext` 准备
- `ProjectCreationApplicationService` 已承接“新建项目完成后进入项目会话”的主流程编排
- 文档生成/更新输入已收口到 `ProjectDocumentContext`
- 已明确输出目录主规则：
  - `Submitted Material` 用于提交材料型输出
  - `Test results` 用于测试结果类导出
  - 项目工作目录用于项目结构强绑定输出
  - `D:\OutFile` 仅保留无项目态兜底

## 8. 当前剩余兼容消费点

- 项目会话主链已无 `current_project` 兼容读写通道
- 主线文档生成链路已基本切换到 `ProjectContext + ProjectDocumentContext`
- 剩余兼容点主要在历史命名、部分旧 controller 兼容入口和历史备份文件

## 9. 下一步建议

1. 继续收缩历史兼容入口，减少 controller 内残留的项目路径字符串通道
2. 进入阶段性结构验收，确认哪些兼容层保留到后续阶段，哪些可以直接删除
3. 补一轮最小自动化/手工回归基线，使项目会话主线具备稳定验证口径

## 10. 已建立的自动化回归基线

当前已落地的最小自动化回归覆盖：

- [test_project_contexts.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_contexts.py)
  - `ProjectContext`
  - `ProjectDocumentContext`
  - `OutputPathResolver`
- [test_project_open_service.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_open_service.py)
  - `ProjectOpenService` 已有项目主路径
  - `ProjectOpenService` 补建 `application_data.json` 主路径
- [test_project_session_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_session_flow.py)
  - `ProjectSessionService`
  - `ProjectSessionCoordinator`
  - `Matrix 自动导入` 的调度边界与异常兜底
- [test_project_creation_application_service.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_creation_application_service.py)
  - `ProjectCreationApplicationService`
  - 新建项目完成后进入项目会话的主编排
- [test_main_window_open_project_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_main_window_open_project_flow.py)
  - `MainWindowController.handle_open_project()`
  - 打开已有项目主编排与异常路径
  - `MainWindowController._on_project_opened()`
  - `project.opened -> _apply_project_context()` 的分流与短路
- [test_output_path_decisions.py](D:/PythonProject/TestFlowManager/tests/unit/test_output_path_decisions.py)
  - 导出/生成链的项目态默认目录规则
  - `Test results / Submitted Material / 项目工作目录` 的链路级落点验证
- [test_project_creator_flow.py](D:/PythonProject/TestFlowManager/tests/unit/test_project_creator_flow.py)
  - 新建项目主入口
  - `ProjectCreatorController.handle_create_new_project()`
  - 项目创建完成后接入项目会话的分流逻辑

当前执行口径：

- `python -m pytest tests/unit/test_project_contexts.py tests/unit/test_project_open_service.py -q`
- `python -m pytest tests/unit/test_config_manager.py tests/unit/test_project_session_flow.py -q`
- `python -m pytest tests/unit/test_project_creation_application_service.py -q`
- `python -m pytest tests/unit/test_main_window_open_project_flow.py -q`
- `python -m pytest tests/unit/test_output_path_decisions.py -q`
- `python -m pytest tests/unit/test_project_creator_flow.py -q`
- `python -m pytest tests/unit/test_project_contexts.py tests/unit/test_project_open_service.py tests/unit/test_config_manager.py tests/unit/test_project_session_flow.py tests/unit/test_project_creation_application_service.py tests/unit/test_main_window_open_project_flow.py tests/unit/test_output_path_decisions.py tests/unit/test_project_creator_flow.py -q`

这批测试的定位是：

- 不依赖 PyQt 主窗口
- 不依赖真实 Word / Excel / Outlook COM
- 先锁定项目会话、项目文档上下文、输出目录和项目打开编排的基础行为

当前结论：

- 阶段 6 的第一轮自动化安全网已建立
- `project.opened + current_project_context` 主线已具备稳定的非 GUI 回归验证口径
