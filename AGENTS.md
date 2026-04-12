# TestFlowManager Project AGENTS.md

本文件定义 Codex 在 `D:\PythonProject\TestFlowManager` 仓库中的项目级默认规范。

如果与全局 `C:\Users\White\.codex\AGENTS.md` 冲突，以“更具体、更接近当前项目”的规则为准。

---

## 1. 项目定位

TestFlowManager 是一个运行在 Windows 平台上的 PyQt5 桌面应用，核心目标是围绕测试项目全生命周期提供：

- 项目创建
- LTR 申请单处理
- Matrix 编辑、导入、导出
- 测试条件确认
- 测试表格生成
- 报告生成、更新、客户版转换
- Word / Excel / Outlook 相关自动化处理

---

## 2. 项目核心判断

### 2.1 Matrix 是系统核心，不是普通子功能

默认视为：

- Matrix 是系统的核心工作区
- 相关测试条件确认、测试表格生成、报告生成都依赖 Matrix
- 主窗口可以默认显示 Matrix
- 但 Matrix 仍应保持独立模块边界，不应继续把内部实现直接揉进主窗口

默认架构方向：

```text
MainWindow
  -> MatrixWorkspace / MatrixPage   # 默认首页
  -> Other feature pages
```

不推荐继续强化：

```text
MainWindow
  -> 直接持有 Matrix 的 table / toolbar / managers / handlers / sync logic
```

### 2.2 主窗口是应用壳层，不是业务杂糅层

主窗口默认职责：

- 页面容器
- 导航与菜单
- 顶层状态展示
- 项目会话切换
- 全局生命周期管理

主窗口不应长期承担：

- Matrix 内部表格同步
- 具体导入导出实现细节
- 某一 feature 的页面内部事件处理

---

## 3. 当前技术栈

默认按以下栈理解和修改本项目：

- Python 3.12+
- PyQt5
- pywin32
- python-docx
- openpyxl
- pandas
- pytest
- PyInstaller

项目是 Windows 优先，不默认追求跨平台兼容。

---

## 4. 真实代码结构认知

处理本项目时，默认以下判断成立：

- 真实入口在 `src/app/application.py`
- 全局基础设施在 `src/core`
- 业务功能在 `src/features`
- `matrix` 是最大、最复杂的模块
- `main_window` 是当前耦合中心
- `project_creator`、`ltr_manager` 是重要业务流程入口
- `utils` 中包含大量 COM 与文档处理逻辑

默认优先关注以下文件：

- `src/app/application.py`
- `src/core/config_manager.py`
- `src/core/event_dispatcher.py`
- `src/core/state_manager.py`
- `src/core/logger.py`
- `src/features/main_window/view/main_window_ui.py`
- `src/features/main_window/controller/main_window_controller.py`
- `src/features/matrix/controller/matrix_controller.py`
- `src/features/matrix/service/matrix_service.py`
- `src/features/project_creator/controller/project_creator_controller.py`

---

## 5. 项目级重构目标

默认重构目标不是“重写”，而是“在保留业务行为的前提下逐步恢复边界”。

优先级按以下顺序执行：

1. 收口主窗口职责
2. 保留 Matrix 默认首页地位，但提取为独立页面或工作区
3. 收口状态流和事件流
4. 拆分胖 controller
5. 拆解过载的 Matrix service
6. 统一配置与路径策略
7. 重建测试基线

---

## 6. 项目级架构原则

### 6.1 渐进式重构

除非用户明确要求，否则不要对本项目做：

- 一次性大重写
- 一次性整体替换 Matrix 架构
- 一次性移除所有全局单例

优先采用：

- 兼容层
- 页面级抽离
- 上下文对象引入
- 单点入口收口

### 6.2 先边界，后内部

对本项目，重构优先顺序必须是：

1. 先理清主窗口与 Matrix 的边界
2. 再理清项目上下文传递方式
3. 再理清状态和事件职责
4. 最后再拆 Matrix 内部服务

### 6.3 先保行为，再优化结构

只要涉及以下流程，默认视为高风险：

- 打开项目
- 新建项目
- 自动导入 `matrix.xlsx`
- Matrix 编辑
- Matrix 导出
- LTR 申请处理
- 报告更新
- 客户版报告生成

这些流程在重构中必须优先保行为一致。

---

## 7. 状态、事件与上下文规范

### 7.1 当前问题默认成立

默认认为本项目存在：

- `event_dispatcher` 与 `state_manager` 双通道并存
- `current_project`、`dl_number` 等上下文散落传递
- 同一业务动作存在重复触发路径

### 7.2 默认改造方向

优先引入：

- `ProjectContext`
- 必要时引入 `MatrixContext`

建议 `ProjectContext` 至少包含：

- `project_path`
- `dl_number`
- `application_data_path`
- `matrix_file_path`

### 7.3 默认约束

- 全局状态只存真正的全局上下文
- 事件只表达一次性动作
- 同一业务动作不要同时依赖重复事件和重复状态写入

---

## 8. 配置与路径规范

处理本项目配置时，默认检查以下事实：

- 文档可能写根目录 `config/`
- 真实运行配置实际位于 `src/app/config/`
- 打包态与开发态路径解析规则不同
- 配置中存在绝对 Windows 路径

默认要求：

- 以代码真实行为为准
- 如果改配置路径，必须同步修正文档
- 任何配置治理都要考虑开发态和打包态

---

## 9. COM 与资源释放规范

本项目大量依赖 Word / Excel / Outlook COM。

因此默认要求：

- 不破坏 COM 资源释放路径
- 不随意改动应用退出时的清理逻辑
- 对 Word / Excel 文件操作保留异常日志
- 修改导入导出逻辑时，优先确认句柄释放与占用问题

凡涉及以下文件，默认提高审慎级别：

- `src/utils/word_utils.py`
- `src/utils/excel_utils.py`
- `src/utils/email_utils.py`
- `src/app/application.py`

---

## 10. 代码风格补充约束

### 10.1 本项目中应避免的结构

- 巨型 `controller`
- 巨型 `service`
- 主窗口直接持有某个 feature 的所有内部部件
- 依赖隐式全局状态完成正常业务流程
- 只为“复用”而制造无意义抽象层

### 10.2 本项目中鼓励的结构

- `Workspace` / `Page` 级封装
- `ApplicationService` 负责编排
- `DomainService` 负责纯业务逻辑
- 上下文对象替代散乱参数
- 页面注册机制替代硬编码页面拼装

---

## 11. 默认文档要求

只要涉及结构性改动，默认同步维护或新增：

- `docs/refactor_baseline.md`
- `docs/refactor_task_board.md`
- 必要时补充迁移说明

如果发现文档与代码不一致：

- 先指出
- 再修正
- 不允许默认忽略

---

## 12. 默认测试要求

对本项目进行任何非微小改动时，默认至少做以下之一：

- 运行相关 pytest 测试
- 做最小冒烟验证
- 若无法验证，明确说明原因和剩余风险

默认优先覆盖的回归路径：

- 配置加载
- 打开项目
- 新建项目
- Matrix 导入
- Matrix 导出
- LTR 申请处理

如果测试目录继续演进，优先整理为：

- `tests/unit`
- `tests/integration`
- `tests/gui_manual`
- `tests/fixtures`

---

## 12.1 自动推进规则

为了减少不必要的人工确认，默认采用以下执行规则：

- 如果当前改动属于低风险结构收口、兼容层收缩、文档同步、配置访问治理、路径解析治理、非 GUI 的 service/controller 重构，且相关自动化验证已通过，Codex 默认可以直接继续下一步主线任务，无需再次征求用户确认。
- 所谓“自动化验证已通过”，默认至少包括以下一项或多项：
  - 相关 `pytest` 通过
  - 相关 `python -m py_compile` 通过
  - 相关静态扫描或文本盘点结果符合预期
- 如果改动已经存在自动化测试覆盖，则默认以自动化验证结果作为继续推进依据，不重复要求用户做人肉确认。

以下情形仍默认需要用户人工确认后再继续下一步：

- 涉及 PyQt 可见交互变化、页面布局变化、操作路径变化
- 涉及 Word / Excel / Outlook COM 调用流程变化
- 涉及导入 / 导出结果文件结构变化
- 涉及端到端业务行为变化：
  - 打开项目
  - 新建项目
  - 报告生成
  - 报告更新
  - 客户版报告
  - 费用表
  - LLCR / CR
- 涉及删除旧功能入口、删除文件、删除兼容层、迁移默认策略
- 存在多个合理架构分叉，需要用户做产品或设计决策

默认继续策略：

- 若当前步骤属于结构重构主线，且不触发上述高风险条件，Codex 应在自动验证通过后直接继续最合适的下一步。
- 只有在以下情况才主动停下询问用户：
  - 验证失败
  - 遇到高风险行为变更
  - 需要用户在多个方案之间做选择
  - 发现与当前主线冲突的仓库状态或需求变化

---

## 13. 默认交付要求

在这个仓库中，高质量交付默认应包括：

- 对真实代码结构的准确判断
- 对关键耦合点的明确说明
- 小步、兼容、可回归的修改路径
- 风险说明
- 验收标准

如果用户要做长期重构，默认优先沉淀：

- 架构基线
- 任务看板
- 回归清单
- 项目级 AGENTS 规范

---

## 14. 当前仓库的默认实施方向

如果用户没有明确指定下一步，默认按以下方向协助：

1. 将 Matrix 从主窗口内部细节中抽离为独立 `MatrixPage` 或 `MatrixWorkspace`
2. 保持 Matrix 作为主窗口默认核心页面
3. 引入 `ProjectContext`
4. 收口 `project.opened` 与 `current_project` 的双通道行为
5. 为关键流程建立最小回归验证

---

## 15. 最终原则

对 TestFlowManager，默认遵守以下一句话原则：

“保持 Matrix 的核心地位，但不要再让主窗口和 Matrix 内部实现继续硬耦合。”
