# MainWindow 重构追踪

## 1. 重构目标

- 把 `MainWindow` 削减成**纯 UI 容器**（只是 header/sidebar/page stack + QSS shell），不再直接持有 Matrix/报告/文档的复杂生命周期。
- 拆分 `MainWindowController` 为一组**单职责协调组件**（ProjectLifecycleCoordinator、MatrixWorkspaceFacade、DocumentWorkflowCoordinator、StatusManager），让每个组件独立可 lazy load。
- **消除重复写入/COM 释放逻辑**，统一放到 service 层（如 ProjectDataWriter、ComResourceManager），MainWindow 只通过事件触发接口。
- 让 lazy load 真正生效（import 在冷路径以外），并清理无用模块/垃圾文件，腾出启动性能/扩展能力。
- 为后续启动优化与功能扩展奠定结构基础（更小的文件、明确的依赖、可插拔的协调层）。

## 2. 核心问题总结（需在文档/追踪中明确）

| 问题 | 说明 |
| --- | --- |
| 模块拆分不彻底 | `components/header`/`sidebar` 未真正接入主流程，`main_window_ui.py` 仍维护所有 UI+业务，未构成清晰 shell。 |
| MainWindow / Controller 过重 | 两个类同时初始化 Matrix/workspace/project services，并在 constructor 里做 full lifecycle，导致 cold path 过重。 |
| UI / 业务 / 平台混在 | 视图里直接触发 `project_session_service.apply_project_context`、Word/Excel release 等，难以审计。 |
| 重复写文件 | 例如 `_ensure_project_data_file` 被 `main_window_ui` 与 controller 共同触发，存在多次写入 `application_data.json` 的风险。 |
| Lazy load 只是逻辑 | heavy import（MatrixPage、controllers）仍在文件顶部，冷启动时会全集中加载。 |
| 运行垃圾 | 无效模块（空 handlers）、`__pycache__` 目录等增加打包体积，埋伏安全风险。 |

## 3. 关键任务与分解步骤

1. **让 `components`/`constants`/`handlers` 真正承接主流程**
   - 确认 `components/header_components.py`/`sidebar_components.py` 被 `main_window_ui.py` 以接口形式调用（例如 `from src.features.main_window.components import build_header`）。原本 inline 的 header/sidebar 构建逻辑迁移出去。
   - 采用 `constants/main_window_styles.py` 里的 `_LIMS_APP_STYLESHEET` 常量，删除 `main_window_ui.py` 内部的重写版本，确保 QSS 由 constants 管理。
   - 引入 `view/handlers/event_handlers.py`，把 `QAction`/slot 的回调统一到 handler 类，MainWindow 只负责 connect/signals，不再嵌入业务逻辑。

2. **分离 shell UI 与 MainWindow 视图逻辑**
   - 新增 `view/ui_shell.py`，提供 `build_shell(main_window)`/`install_navigation(main_window)` 等函数，把 header、sidebar、status、page stack 构造搬进去。
   - `main_window_ui.py` 只调用 shell 接口，并通过轻量 signal/slot 控件保持响应（如 `startup_progress`、`status`）。
   - 所有 heavy widget/placeholder（MatrixPage、reports、tools）只能在 shell/handlers 中以工厂方式创建，保证冷路径不 import heavy modules。

3. **Controller 重塑 & 管理层拆分**
   - 拆出 `MatrixWorkspaceFacade`（控制 Matrix workspace、MatrixPage lifecycle、session binding 与 shutdown）和 `ProjectLifecycleCoordinator`（项目 open/create、ProjectContext、application_data.json 保证）。
   - 重写 `MainWindowController` 构造，保持轻量：只读入 status service、coordinator references，真正实例化 Matrix/workflow 由 facade/coordination getters 延迟完成。
   - 把 `application_data.json`、COM release、report/file export 逻辑移至新的 service（如 `ProjectDataWriter`, `ComResourceManager`），避免 controller/view 重复写入。

4. **真正实现 lazy load**
   - 实现 `src/core/utils/lazy_loader.py`（或 `LazyImportFactory`），提供 `lazy_import("module.path", "ClassName")` helper，并在 MainWindow/handler/Controller 中调用，把 heavy import 延到 first use。
   - 对 MatrixPage、LTREditorController、DocumentParserController、MatrixWorkspaceCoordinator 等做按需加载，首次创建时才 import 并缓存。
   - 扩展 `MatrixWorkspaceFacade` 接口可被 `MainWindow` 按需激活（如在 `_on_page_changed_for_matrix` 中调用 `facade.ensure_ready()`）。

5. **文档与追踪**
   - 本文档持续更新每个阶段状态，将“补漏/集成”作为子任务（例如 “header component wiring 完成”）。
   - 每次修改后在文档 “## 5. 追踪记录” 添加条目，记录里程碑（shell wiring、facade 初版、lazy loader 引入等）。

## 4. 验收标准

## 4. 验收标准

1. `main_window_ui.py` 行数显著下降（目标 < 12k），只包含 UI wiring + minimal signal handling。
2. MatrixPage、报告/文档 controller 相关 import 只出现在 lazy loader 中，冷启动时不加载。
3. 重写之后没有重复 `application_data.json` 写入 —— 通过 audit logger 或单元测试确保只写一次。
4. `MainWindowController` 只负责 orchestrate，Matrix/project 协调均通过新 coordinator 提供接口。
5. 针对重构点补充文档并留下 change log/issue 说明。

## 5. 追踪记录（后续补充）

| 日期 | 更改 | 负责人 | 备注 |
| --- | --- | --- | --- |
| 2026-04-12 | 建立本追踪文档 | Codex | 作为重构基线 |
| 2026-04-12 | 接入 header/sidebar/event handler 模块 & 增加 MatrixWorkspaceFacade | Codex | 主窗口现在使用 components/handlers/const 定义的 shell，新增 facade 抽象 matrix lifecycle，UI 控件只做 wiring。 |
| 2026-04-12 | 增加 ProjectLifecycleCoordinator & 投入 lazy matrix facade | Codex | controller 侧引入 facade + coordinator，项目打开逻辑剥离到 coordinator，减少 controller 责任。 |
| 2026-04-12 | 移动 `BasicInfoDialog` 到 `view/dialogs` 并更新引用路径 | Codex | 确保 ProjectLifecycleCoordinator 与 Matrix 事件处理器引入的模块存在，避免启动时 module-not-found。 |
| 2026-04-12 | 抽离导航逻辑到 `navigation_controller.py` | Codex | 让主窗口只负责 action wiring+UI shell，侧栏/堆叠页的同步由 new NavigationController 管理，便于后续 lazy load。 |

## 7. 近期对话梳理与新增约束

1. **BasicInfoDialog 已迁移**：`BasicInfoDialog` 现位于 `src/features/main_window/view/dialogs/basic_info_dialog.py`，所有依赖该模块的 coordinator/controller/handler 已同步更新 import；后续仍需保持路径一致以避免打包时报错。
2. **新模块尚未真正接入主流程**：`components/header_components.py`、`components/sidebar_components.py`、`view/handlers/event_handlers.py`、`constants/main_window_styles.py` 都已建成，但主窗口仍保留旧的 inline header/sidebar/QSS/事件逻辑，这导致 PyInstaller 打包和冷路径加载仍触发这些模块，无法达成预期的 lazy load。
3. **计划步骤被要求同步记录**：当前对话强调每轮迭代要写入文档、明确任务与步骤、说明关键决策（例如组件 wiring、职责迁移、重写 lazy loader），并持续列出风险/约束。

## 8. 高优先级主任务与细化步骤

### 8.1 任务 A：恢复主窗口可启动状态
- 甄别缺失 `BasicInfoDialog` 的原因（可能因命名为 `base_info_dialog`，亦或文件丢失），并修复引用。
- 若短期内无法提供完整 UI，可临时建立 stub（只实现最低接口），让整个系统能加载壳层与 controller。
- 验收：`python src/app/application.py` 不再因 `ModuleNotFoundError` 中断，能够进入壳层并显示启动提示。

### 8.2 任务 B：让组件/handler 实现真正接入
- 清理 `main_window_ui.py` 中自有 header/sidebar/QSS/事件 wiring，只保留调用 `HeaderComponents`, `SidebarComponents`, `EventHandlers`, `constants/main_window_styles` 的部分。
- 明确 navigation/QAction wiring 路径：`MainWindow` 负责暴露 navigation slot，`EventHandlers` 只做 view-> controller 的转发。
- 确保 components/handlers 的 import 只在需要时发生（例如在 `_setup_basic_ui` 中），便于未来 lazy loader 按需触发。

### 8.3 任务 C：Controller/Coordinator 逐步瘦身
- 弱化 `MainWindowController.__init__`，将 matrix/workspace 的具体创建移至 `MatrixWorkspaceFacade/Coordinator` 由 `ensure_ready()` 等接口触发。
- 为 `ProjectLifecycleCoordinator` 以外的服务（e.g. `ProjectDataWriter`, `ProjectSessionCoordinator`）建接口，集中处理 `application_data.json`、Word/Excel 释放、report/export 的副作用。
- 验收：控制器只协调（event dispatch、status update、shell commands），不再直接构造 Matrix/Matrix session 的 heavy 对象。

### 8.4 任务 D：记录与追踪
- 所有重构阶段都要在本文档 “## 5. 追踪记录” 追加新行，说明完成的模块 wiring/拆分/服务。
- 本轮需要在最终交付（回复）中复盘关键决策、约束（如缺失 dialog）、重构范围，以及后续要完成的具体任务。
- 保持文档一致性：若修改了模块名、路径或新增文件，需同步更新 `docs/main_window_refactor.md` 及任何引用文档。

## 9. 下一步动作（在当前交付中需说明）

1. 修复 `ProjectLifecycleCoordinator` 依赖的 `BasicInfoDialog`，确保入口运行不再失败（可通过补文件或修正路径）。
2. 在接下来的重构中，先将 `MainWindow` 的 UI wiring 完全托管给 `components`/`handlers`，再逐步瘦身 controller/facade。
3. 继续保持对话与文档同步：每完成一步就追加表格行，并在回复中包含关键决策与后续计划。
| 2026-04-12 | 接入 header/sidebar/event handler 模块 & 增加 MatrixWorkspaceFacade | Codex | 主窗口现在使用 components/handlers/const 定义的 shell，新增 facade 抽象 matrix lifecycle，UI 控件只做 wiring。 |
| 2026-04-12 | 增加 ProjectLifecycleCoordinator & 投入 lazy matrix facade | Codex | controller 侧引入 facade + coordinator，项目打开逻辑剥离到 coordinator，减少 controller 责任。 |

## 6. 当前讨论补充总结

1. **组件接入正在推进**：刚完成的工作将 `components/header_components`/`sidebar_components`、`handlers/event_handlers`、`constants/main_window_styles` 真正接回主流程，`main_window_ui.py` 只保留 UI wiring。
2. **MainWindow/Controller 过重，逻辑混乱**：main_window里 UI、Matrix生命周期、LTR、COM、report 逻辑都耦合，controller 中也把 Matrix session 在 constructor 里 fully instantiate， lazy load 只是逻辑上的延后，冷路径 import 仍把所有重模块加载。
3. **重复写逻辑**：`ProjectOpenService` 和 controller/view 里多处写 `application_data.json`，同时还有 COM 释放/Word/Excel 控制，需要集中至单一 service 以免冲突。
4. **接下来要做的每个步骤**：
   - 先把 header/sidebar/event handler wiring 重构到 shell/handler 模块，确保 MainWindow 只做 UI 容器。  
   - 再拆 facade/coordinator，让 controller 成为 orchestration layer，Matrix session/workspace 由 facade 管理。  
   - 最后完善 lazy loader 和 service，清理未用模块与 `__pycache__`，写入文档并记录每一步完成情况。

| 日期 | 更改 | 负责人 | 备注 |
| --- | --- | --- | --- |
| 2026-04-12 | 建立本追踪文档 | Codex | 作为重构基线 |
