# TestFlowManager Project AGENTS.md

本文件定义 Codex 在 `D:\PythonProject\TestFlowManager` 仓库中的项目级默认规范。

如果与全局 `C:\Users\White\.codex\AGENTS.md` 冲突，以"更具体、更接近当前项目"的规则为准。

---

## 0. 全局变量与临时文件规范

### 0.1 临时文件目录

**所有临时测试/脚本文件必须放在 `tmp/` 目录下，禁止放在根目录。**

```
d:/PythonProject/TestFlowManager/
├── tmp/                    # 临时文件专用目录
│   ├── _tmp_copy.py
│   ├── _tmp_verify.py
│   └── ...
├── src/
├── tests/
└── ...
```

### 0.2 临时文件命名规则

| 类型 | 命名模式 | 示例 |
|------|----------|------|
| 一次性测试脚本 | `_tmp_{目的}.py` | `_tmp_verify.py`, `_tmp_fix_data.py` |
| 数据迁移脚本 | `_tmp_migrate_{模块}.py` | `_tmp_migrate_session.py` |
| 计数/分析脚本 | `_tmp_count{序号}.py` | `_tmp_count.py`, `_tmp_count2.py` |

### 0.3 文件删除规范（强制）

**删除临时文件时，必须物理删除文件本身，禁止仅清空内容保留空文件。**

```python
# ❌ 禁止：仅清空内容
with open('_tmp_test.py', 'w') as f:
    f.write('')  # 这是错误的！

# ✅ 正确：物理删除文件
import os
os.remove('_tmp_test.py')  # 或 delete_files 工具
```

### 0.4 清理责任

- 临时文件使用完毕后 **必须立即删除**
- 禁止在根目录留下任何 `_tmp_*.py` 文件
- 禁止在根目录留下任何空文件（0字节）

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

默认重构目标不是"重写"，而是"在保留业务行为的前提下逐步恢复边界"。

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
- 只为"复用"而制造无意义抽象层

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
- 所谓"自动化验证已通过"，默认至少包括以下一项或多项：
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

"保持 Matrix 的核心地位，但不要再让主窗口和 Matrix 内部实现继续硬耦合。"

---

## 16. 架构红线（2026-04-18 确立）

### 16.1 禁止行为 🔴

以下行为会破坏已建立的架构边界，**严禁执行**：

1. **禁止在 MainWindow 中直接操作 Matrix 内部组件**
   - ❌ 不得在 `main_window_ui.py` 中直接调用 `matrix_page.xxx()`
   - ❌ 不得在 `MainWindowController` 中持有 `MatrixSessionRegistry/Manager/Orchestrator`
   - ✅ 必须通过 `MatrixWorkspaceFacade` 代理

2. **禁止绕过 Facade 直接访问 Feature 内部**
   - ❌ Shell 层不得直接导入 `src.features.matrix.service.*`
   - ❌ Shell 层不得直接实例化 Feature Controller
   - ✅ 必须通过对应的 Facade（Matrix/LTR/FileOperations）

3. **禁止创建新的巨型文件**
   - ❌ 任何单个 Python 文件不得超过 500 行
   - ❌ 任何 Service 类不得超过 400 行
   - ✅ 超过阈值必须拆分或抽取子服务

4. **禁止在 Service 层操作 UI**
   - ❌ Service 中不得出现 `QMessageBox` / `QFileDialog`
   - ❌ Service 中不得直接使用 `print()`（必须用 logger）
   - ✅ UI 交互必须由 Controller 层决定

5. **禁止 utils → features 反向依赖**
   - ❌ `src/utils/` 不得导入 `src/features/` 中的内容
   - ✅ 如需业务逻辑，应下沉到对应 feature 的 service

### 16.2 强制检查清单 ✅

每次提交代码前，AI 助手必须验证：

- [ ] 新文件行数 < 500 行
- [ ] 无循环导入（运行 `python -m pytest tests/unit/test_import_guards.py`）
- [ ] Shell 层未直接访问 Feature 内部实现
- [ ] 所有 print 已替换为 logger
- [ ] COM 资源释放路径未被破坏

### 16.3 架构演进原则

**渐进式重构优先**:
- 新功能应遵循现有分层模式
- 修改旧代码时，顺手清理相关技术债（Boy Scout Rule）
- 不为了"完美架构"而一次性重写

**边界优于内部**:
- 先确保模块间边界清晰
- 再优化模块内部结构
- 不要为了内部整洁而破坏外部契约

---

## 17. 已知技术债清单（待处理）

> **重要**: 以下问题**不阻塞新功能开发**，但应在适当时机处理。

| 优先级 | 文件 | 问题 | 预计工作量 | 状态 |
|--------|------|------|-----------|------|
| ~~P1~~ | ~~`report_updater_service.py` (923行)~~ | ~~职责过载，需拆分为 3-4 个子服务~~ | ~~2-3 天~~ | **✅ 已完成** (923→199行, -78.4%) |
| ~~P2~~ | ~~`document_editor_mixin.py` (532行)~~ | ~~utils→features 反向依赖~~ | ~~1-2 天~~ | **✅ 已完成** (已消除反向依赖) |
| ~~P3~~ | ~~`matrix_service.py` (243行)~~ | ~~兼容性转发器需制定清除计划~~ | ~~0.5 天~~ | **✅ 已完成** (无兼容层残留) |
| ~~P4~~ | ~~`report_wizard` → `matrix` 耦合~~ | ~~5+ 处直接引用，建议引入 Protocol~~ | ~~1-2 天~~ | **✅ 已完成** (已解耦) |
| ~~P5~~ | ~~`src/` 多个文件 (13个)~~ | ~~40+ 处残留 print 语句（ltr_number_generator 13处最多）~~ | ~~< 1 天~~ | **✅ 已完成** (已全部清理) |

**处理策略**: 
- 新功能涉及这些模块时，顺手重构
- 或专门安排 refactoring sprint 集中处理
- **不要**因为技术债而停止功能开发
## 18. Office 文档处理重构规则（2026-04-18 补充）

### 18.1 Office 双引擎是本项目默认策略

本项目运行环境固定为 Windows 11，默认允许并鼓励采用双引擎 Office 处理方案：

- 非 COM 引擎：`openpyxl`、`python-docx`
- COM 引擎：`win32com`

这不是临时兼容措施，而是本项目长期有效的工程策略。

### 18.2 引擎选型默认规则

默认优先使用非 COM 引擎的场景：

- 纯数据读写
- 简单格式处理
- 不要求保留 Office 运行时行为
- 不要求精确保留复杂对象结构

默认必须使用 COM 引擎的场景：

- 需要高保真保留 Excel 工作簿格式、公式、图表、嵌入对象
- 需要高保真处理 Word 文档布局、样式、表格、字段、分页
- 需要与 Outlook 或 Office 对象模型直接交互
- 需要依赖 Office 实际运行行为而不是静态文件结构

如果两个引擎都可行：

- 优先保证业务行为一致
- 再考虑可维护性、稳定性和资源成本

### 18.3 禁止各 feature 各自管理 Office 生命周期

以下做法默认不合格：

- 在 feature 内部自行启动、复用、关闭 Word/Excel/Outlook 应用
- 在 feature 内部重复实现打开、保存、另存、备份、占用检查逻辑
- 在 feature 内部自行处理 COM 初始化、异常恢复、资源释放
- 在 feature 内部自行决定引擎选型并把策略写死在业务代码中

新增或重构的 Office 处理流程，默认必须逐步收口到统一基础设施层。

### 18.4 Office 公共能力默认收口位置

如无特殊原因，Office 相关公共能力默认收口到：

- `src/infrastructure/office/`

建议至少包含：

- `engine_policy.py`
- `runtime_manager.py`
- `excel_runtime.py`
- `word_runtime.py`
- `outlook_runtime.py`
- `session.py`
- `document_pipeline.py`
- `facade.py`
- `exceptions.py`

在达到该结构之前，可以保留兼容层，但不再鼓励继续向 `src/utils/word_utils.py`、`src/utils/excel_utils.py` 堆积新业务逻辑。

### 18.5 Office 共享能力清单

以下能力默认视为项目级共享能力，而不是 feature 私有实现：

- 引擎选型
- 文档打开
- 只读 / 密码策略
- 保存与另存
- 备份策略
- 输出路径决策
- 文件占用检测
- COM 异常分类与重试
- 运行时资源释放
- 统一日志记录

### 18.6 Office 重构默认迁移顺序

如无用户额外指定，Office 相关重构默认按以下顺序推进：

1. Matrix 导出链路
2. Report Updater 链路
3. Project Creator / LTR 文档处理链路
4. Report Wizard 链路
5. Outlook / 邮件相关链路

### 18.7 Office 改动的验证要求

凡涉及 Office 基础设施或共享逻辑改动，默认需要补充或说明以下验证：

- 至少一项自动化验证：`pytest` 或 `python -m py_compile`
- 至少一项最小冒烟结论：说明验证了哪条文档处理路径
- 明确说明 COM 资源释放路径是否保持不变
- 明确说明行为是否与改动前保持一致

---

## 19. 执行文档与任务推进规则（2026-04-18 补充）

### 19.1 权威执行文档

全项目的重构执行主文档默认是：

- `docs/REFACTOR_GUIDE.md`

凡涉及以下内容，默认应先参照该文档执行：

- 整体重构顺序
- UI 现代化（U1-U4）
- 局部大文件收口（B 线）
- 按需专题（C 线）

### 19.2 AGENTS 与执行文档的分工

默认分工如下：

- `AGENTS.md`
  - 写稳定规则
  - 写边界约束
  - 写禁止事项
  - 写默认决策

- `docs/REFACTOR_GUIDE.md`
  - 写阶段步骤
  - 写迁移顺序
  - 写优先级
  - 写每阶段验收标准
  - 写当前活跃任务（§三）

- `docs/refactor_task_board.md`
  - 写当前任务状态
  - 写阻塞点
  - 写下一步执行项

- `docs/architecture/refactor_baseline.md`
  - 写当前架构现状与量化评分

### 19.3 结构性改动的文档同步规则

如果改动属于以下任一类型，默认同步检查或更新相关文档：

- 模块划分变化
- 架构边界变化
- Office 公共能力收口
- 项目会话流转变化
- Matrix / MainWindow 入口职责变化
- Config / Path 策略变化

默认需要检查：

- `docs/REFACTOR_GUIDE.md`
- `docs/refactor_task_board.md`
- `docs/architecture/refactor_baseline.md`

### 19.4 默认执行主线

如果用户没有指定更具体的下一步，默认按以下主线推进：

> **已越过以下早期主线（Phase 0-10 已完成）**：
> 1. ~~文档基线与任务板归一~~ ✅
> 2. ~~项目会话入口收口~~ ✅
> 3. ~~Matrix Session Facade 防越界预拆分~~ ✅
> 4. ~~Office 基础设施骨架落地~~ ✅
> 5. ~~Matrix 导出接入新 Office 管理层~~ ✅
> 6. ~~Report Updater 接入新 Office 管理层~~ ✅
> 7. ~~Matrix Workspace / Session 边界二次拆分的剩余部分~~ ✅
> 8. ~~Project Creator 控制器瘦身~~ ✅
> 9. ~~Config / Path 策略统一~~ ✅
> 10. ~~仓库残留清理~~ ✅

**当前活跃主线（A/B/C 三线并行）**：

- A 线：UI 现代化（U1-U4）
- B 线：局部大文件收口（>500 行文件）
- C 线：按需专题（Notification 替换、深色模式等）

### 19.4.1 文档参考顺序

如果要基于重构文档继续执行，默认按以下顺序参考：

1. `AGENTS.md`
2. `docs/REFACTOR_GUIDE.md`（核心执行参考，含路线图）
3. `docs/refactor_task_board.md`
4. `docs/architecture/refactor_baseline.md`

默认含义：

- `AGENTS.md` 提供稳定规则和禁止事项
- `docs/REFACTOR_GUIDE.md` 提供当前阶段任务、优先级、路线图
- `docs/refactor_task_board.md` 提供当前活跃任务与阶段编号
- `docs/architecture/refactor_baseline.md` 提供当前架构现状基线

### 19.5 不应出现的执行错误

- 不要把 `AGENTS.md` 写成详细任务清单
- 不要只改代码不更新执行文档
- 不要只更新执行文档不同步基线文档
- 不要在没有最小验证的前提下拆除兼容层
