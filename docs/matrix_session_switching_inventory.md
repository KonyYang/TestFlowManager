# Matrix Session Switching Inventory

> 更新时间：2026-04-10
> 目的：盘点从共享 Matrix 会话切换到独立 Matrix 会话前的约束、入口和残留依赖。

---

## 1. 当前结论

当前代码已经具备以下能力：

- `matrix_service_provider.py` 已删除（Phase-11）：不再作为共享实例入口
- `MatrixSessionRegistry` 已引入，用于管理“当前 shared/isolated service 路由选择”
- `MatrixSessionFactory` 支持 `shared / isolated` 两种装配模式
- `MainWindowController` 与 `ProjectCreatorController` 已改为通过 `MatrixSessionFactory` 装配 Matrix 会话
- `MatrixController / MatrixProjectController` 支持显式注入

当前默认行为仍保持：

- `shared`

---

## 2. 当前适合保持 `shared` 的入口

以下入口当前应继续保持共享模式：

- 主窗口启动时的默认 Matrix 工作区
- 项目创建完成后接入主窗口 Matrix 工作区
- 报告向导整体仍以主窗口当前 Matrix 会话为默认数据源的链路

原因：

- 这些链路仍默认假设“当前只有一份活动 Matrix 状态”
- 切到 `isolated` 会导致部分下游仍读共享状态的模块看到的不是同一份数据

---

## 3. 未来可切换到 `isolated` 的候选入口

以下入口在补齐剩余依赖后，可优先尝试切到独立会话模式：

- 新建独立 Matrix 编辑窗口
- 专门的测试/预览型 Matrix 会话
- 不依赖主窗口共享状态的后台导入处理链

判断标准：

- 下游不再直接读取共享 `MatrixService`
- 项目上下文显式传入
- 页面刷新和导出入口显式绑定到当前 controller

---

## 4. 当前阻塞 `isolated` 默认化的残留点

### 4.1 仍保留隐式项目态假设或旧兼容入口的消费方

- `report_updater`（仍存在较多历史“project_path 字符串通道”，需要继续收口到 `ProjectContext`）
- 其他历史页面/对话框中仍可能存在“从 UI 侧临时拼路径/兜底默认目录”的通道（需按模块逐步清理）

说明：

- `get_current_project_context()` 的主线回退已清零（主线不再依赖全局回退来推断项目路径）。
- `report_wizard`/`test_record` 的 legacy `matrix_service` 兼容入口已清理完成（详见文档后续更新段落）。
- 当前更主要的残留点转为：部分模块仍以“共享 Matrix 会话”为默认数据源假设，以及少量目录/输出路径的历史兜底惯性。

### 4.2 报告向导仍保留的旧 MatrixService 兼容入口

（已清理 2026-04-10~2026-04-11）

- `report_wizard` 页面层对 legacy `matrix_service` 的兼容入口已移除，主线改为消费显式注入的 `matrix_controller + project_context`。

### 4.3 MatrixService 本体仍保留单例语义

- `matrix_service.py`

说明：

- 当前 `isolated` 模式已改为通过 `MatrixService.create_isolated()` 创建独立实例
- `MatrixService()` 已回归普通实例语义
- 当前共享语义只保留在 `MatrixService.shared()`
- 这仍属于过渡实现，后续应继续评估如何弱化或替换

---

## 5. 推荐切换顺序

1. 继续保持默认 `shared`，只在受控入口（pilot）扩展 `isolated` 能力与回归覆盖面。
2. 选择一个“非 debug 的正式业务入口”作为下一批 `isolated` 试点（保持默认不变）。
3. 在完成跨入口/跨页面的隔离与回滚契约覆盖后，再评估是否推进更广范围的会话化（包括主窗口默认是否切换）。

---

## 6. 当前建议

当前阶段建议：

- 默认继续使用 `shared`
- 只把 `isolated` 作为工厂能力和测试能力保留
- 在未清理完第 4 节残留点前，不建议把主窗口默认 Matrix 会话切到 `isolated`
## 7. Pilot Entry (2026-04-10)

- Added an isolated-session pilot switch for one controlled entry only:
  - entry: `MainWindowController.handle_new_file()` -> `ProjectCreatorController`
  - switch: environment variable `TFM_MATRIX_SESSION_ISOLATED_PILOT`
  - truthy values: `1 / true / yes / on` (case-insensitive)
- Default remains unchanged:
  - switch absent or falsy => shared mode with injected `MatrixSessionRegistry`
- Pilot behavior when enabled:
  - project-creation entry uses `mode="isolated"`
  - the shared `MatrixSessionRegistry` may still be passed into that entry
    (safe because `session_id`-scoped mode routing does not mutate the default shared mode)

### 7.1 Preview Pilot Entry (2026-04-11)

- Added a second isolated-session pilot switch for a non-default preview entry:
  - entry API: `MainWindowController.handle_open_isolated_matrix_preview_pilot()`
  - switch: environment variable `TFM_MATRIX_SESSION_ISOLATED_PREVIEW_PILOT`
  - fixed session id: `pilot:preview`
- UI trigger (only when the switch is enabled):
  - shortcut: `Ctrl+Alt+Shift+P` (MainWindow action)
  - close shortcut: `Ctrl+Alt+Shift+L` (MainWindow action)
- Default remains unchanged:
  - switch absent or falsy => no preview session is opened

## 8. Report Wizard Boundary Update (2026-04-10)

- `report_wizard` page/controller compatibility entry to legacy `matrix_service` has been removed.
- Current data path for Test Spec filling is now:
  - `matrix_controller` -> explicit `matrix_headers / matrix_rows` snapshot
  - optional `ProjectContext` for document/session metadata
- This clears the remaining page-level dependency that could accidentally read shared service state
  when testing isolated session entry points.

## 9. Test Record Boundary Update (2026-04-10)

- `test_record_controller.py` no longer accepts or consumes legacy `matrix_service`.
- Current Test Record data path is aligned to:
  - `matrix_controller` snapshot (`get_matrix_rows()` + `create_matrix_data_structure(...)`)
  - explicit `ProjectContext` (or controller-provided project context)
- This removes another page/controller-level shared-service compatibility path and reduces
  accidental coupling to shared session state.

## 10. Matrix Controller Legacy API Cleanup (2026-04-10)

- Removed `MatrixController.get_matrix_service()` legacy compatibility API.
- Current consumption path is now controller-level explicit APIs (`get_matrix_headers()`,
  `get_matrix_rows()`, `create_matrix_data_structure(...)`, export/import/initialize methods).
- Added cross-entry isolation regression coverage to ensure:
  - shared entry remains stable
  - isolated pilot entry does not mutate shared entry service binding.

## 11. Session ID Mapping Prep (2026-04-10)

- `MatrixSessionRegistry` now supports optional `session_id` routing:
  - `set_mode(mode, session_id=...)`
  - `get_service(session_id=...)`
  - per-session isolated instance cache
  - `release_session(session_id)` lifecycle cleanup hook
- `MatrixSessionFactory.create(...)` now accepts optional `session_id` and forwards it when using registry.
- Default runtime behavior remains unchanged:
  - existing call paths still use `session_id=None`
  - default mode remains `shared`.

## 12. Pilot Session Lifecycle Wiring (2026-04-10)

- Controlled entry `MainWindowController.handle_new_file()` now passes:
  - `matrix_session_mode="isolated"` (when pilot switch enabled)
  - fixed `matrix_session_id="pilot:new-file"`
  - existing shared `matrix_session_registry` instance
- `ProjectCreatorController.cleanup()` now releases pilot isolated session via:
  - `matrix_session_registry.release_session(matrix_session_id)`
  - only for `isolated` mode with non-empty `session_id`
- This keeps default behavior unchanged while adding explicit create/reuse/release lifecycle
  for the non-default isolated pilot entry.

## 13. Session Scope Wrapper (2026-04-10)

- Added `MatrixSessionScope` and `MatrixSessionRegistry.open_scope(...)` as lightweight
  lifecycle wrapper for session-scoped mode routing and cleanup.
- `ProjectCreatorController` now prefers holding/closing scope instead of directly managing
  `release_session(...)` calls.
- `cleanup()` keeps fallback release logic for compatibility when scope is unavailable.

## 14. Secondary Non-Default Entry (2026-04-10)

- Added a second non-default entry on `MainWindowController` for future isolated preview windows:
  - `open_isolated_matrix_preview_session(session_id)`
  - `close_isolated_matrix_preview_session(session_id)`
- Entry behavior:
  - uses `MatrixSessionScope` when registry supports `open_scope`
  - creates matrix session via `MatrixSessionFactory(..., mode="isolated", session_id=...)`
  - supports multiple concurrent preview session ids
  - supports independent close/release per session id
- This entry is prewired only; it is not bound to default UI/menu flow.

## 15. Hidden Debug Command (2026-04-10)

- Added a hidden debug-only shortcut command path (development mode only):
  - env switch: `TFM_ENABLE_DEBUG_COMMANDS`
  - open preview shortcut: `Ctrl+Alt+Shift+M`
  - close preview shortcut: `Ctrl+Alt+Shift+K`
- Command behavior:
  - opens/closes isolated preview sessions through `MainWindowController` debug APIs
  - uses session-scope lifecycle and keeps default non-debug behavior unchanged.

## 16. Service Access Consolidation (2026-04-10)

- `MatrixSessionFactory` no longer directly imports or instantiates `MatrixService`.
- Default shared mode resolves through `MatrixSessionRegistry` -> `MatrixService.shared()`.
- Default isolated mode is now delegated to a local `MatrixSessionRegistry(initial_mode="isolated")`,
  keeping factory behavior stable while centralizing service-mode routing semantics in the registry.
- Added unit guard `test_matrix_service_access_guard.py` to prevent new direct `MatrixService`
  imports in mainline modules outside scoped service-routing points.

## 17. Registry Diagnostics Baseline (2026-04-11)

- Added read-only diagnostics interfaces on `MatrixSessionRegistry`:
  - `snapshot()`
  - `get_session_modes()`
  - `get_active_isolated_session_ids()`
- Snapshot now exposes:
  - default mode
  - session-mode routing map
  - active isolated session ids
  - whether default isolated instance is allocated
- Added unit coverage to verify:
  - cross-session mode map visibility
  - active isolated session visibility
  - returned structures are copies and do not mutate registry internals.

## 18. Session Manager Pilot Baseline (2026-04-11)

- Added lightweight `MatrixSessionManager` with explicit lifecycle APIs:
  - `create_or_get(session_id, mode=...)`
  - `get(session_id)`
  - `close(session_id)`
  - `list_session_ids()`
- Wired manager only into non-default preview/debug entry paths in `MainWindowController`.
- Default mainline behaviors remain unchanged:
  - default shared session assembly is still routed by existing startup/new-file/open-project paths.

## 19. Debug Session State Visibility (2026-04-11)

- Added debug-only session state snapshot API on `MainWindowController`:
  - `debug_get_matrix_session_state()`
- Snapshot is built from:
  - `MatrixSessionManager.list_session_ids()`
  - `MatrixSessionRegistry.snapshot()`
- Added debug open/close status publishing:
  - after debug preview open/close, status text includes preview count, active isolated count, and default mode.
- Scope remains debug-only (`TFM_ENABLE_DEBUG_COMMANDS`), with no default navigation behavior change.

## 20. Entry Policy Table Baseline (2026-04-11)

- Added `MatrixSessionEntryPolicyTable` for non-default entry routing strategy.
- Current policy entries:
  - `new_file_pilot` -> isolated + fixed `session_id="pilot:new-file"`
  - `preview` -> isolated
  - `debug_preview` -> isolated + session id prefix `debug:preview:`
- `MainWindowController` now resolves non-default entry mode/session-id from policy table
  instead of hardcoded branch constants.
- Policy table now supports explicit injection override at controller assembly time
  (`matrix_session_entry_policies=...`) for test/experiment scenarios.

## 21. Policy Assembly Injection (2026-04-11)

- `MainWindow` composition now owns session-entry policy table construction:
  - creates one `MatrixSessionEntryPolicyTable` instance in UI initialization
  - injects that instance into `MainWindowController` during `_initialize_controllers`
- Impact:
  - non-default entry policy behavior is now anchored in shell-level assembly instead of
    being only controller-internal defaulting
  - default shared runtime behavior is unchanged
- Compatibility:
  - `MainWindowController` keeps its fallback default policy construction when injection
    is absent, to preserve isolated unit-test and legacy assembly scenarios.

## 22. Session Manager Assembly Injection (2026-04-11)

- `MatrixSessionManager` assembly is now owned by MainWindow shell:
  - create once in `MainWindow.__init__` with shared registry
  - inject into `MainWindowController` in `_initialize_controllers`
- Why:
  - aligns manager lifecycle with shell-level composition root
  - prepares for future multi-session orchestration without controller-internal construction
- Behavior impact:
  - default shared runtime flow is unchanged
  - non-default preview/debug entries continue to use same manager APIs
- Compatibility:
  - controller still supports internal fallback manager creation for tests/legacy assembly paths.

## 23. Manager-First Debug State Alignment (2026-04-11)

- `MainWindowController` debug snapshot now follows:
  - manager view first (`MatrixSessionManager.snapshot()`)
  - registry view second (`MatrixSessionRegistry.snapshot()`)
- Purpose:
  - provide a consistent cross-view diagnostic payload before multi-session orchestration rollout
  - reduce dependence on list-only manager introspection
- Added manager diagnostics fields in debug state:
  - `manager_total_sessions`
  - `manager_session_modes`
  - `manager_active_isolated_session_ids`
- Default runtime behavior remains unchanged; this is debug observability hardening only.

## 24. Shutdown Lifecycle Cleanup Hook (2026-04-11)

- Added manager lifecycle close APIs:
  - `MatrixSessionManager.close_by_mode(mode)`
  - `MatrixSessionManager.close_all()`
- `MainWindowController.shutdown()` now explicitly cleans non-default preview/debug sessions:
  - target: `isolated` managed sessions
  - fallback: `close_all()` when `close_by_mode` is unavailable
- Intent:
  - prevent residual non-default sessions from leaking past app shutdown
  - keep default shared mainline session behavior unchanged.

## 25. Entry Metadata & Counting (2026-04-11)

- `MatrixSessionManager` now records optional session entry identity (`entry_name`) per managed session.
- Current explicit tagged entries in `MainWindowController`:
  - `preview`
  - `debug_preview`
- Manager snapshot/stats now provide entry-level observability:
  - session -> entry mapping
  - per-entry active-session counts
- Debug session state now surfaces entry mapping/counts to support next-step
  session-switch orchestration design.

## 26. Session Orchestrator Pilot (2026-04-11)

- Introduced `MatrixSessionOrchestrator` (non-default path only) to centralize session
  scheduling operations:
  - `open_session(...)`
  - `switch_to_session(...)`
  - `close_session(...)`
  - `open_debug_preview(...)`
  - `close_debug_preview(...)`
- Current wiring scope:
  - `MainWindowController` preview/debug preview paths
- Result:
  - session-id generation and last-debug-session tracking are no longer controller-local details
  - controller now delegates scheduling to orchestrator while preserving default shared behavior.

## 27. Orchestrator Assembly Injection (2026-04-11)

- `MainWindow` now owns orchestrator construction and injects it into `MainWindowController`.
- Current composition chain is explicit in shell layer:
  - `MatrixSessionRegistry`
  - `MatrixSessionEntryPolicyTable`
  - `MatrixSessionManager`
  - `MatrixSessionOrchestrator`
  - `MainWindowController`
- Impact:
  - controller side remains behavior-compatible
  - non-default session orchestration seam is now fully composable from assembly root.

## 28. Debug State Merge Delegation (2026-04-11)

- Debug-state merge is now delegated to orchestrator:
  - manager snapshot + registry snapshot aggregation is handled in
    `MatrixSessionOrchestrator.get_debug_state(...)`
- Controller keeps only thin responsibilities:
  - fetch registry snapshot
  - request orchestrator state
  - publish debug status text.

## 29. Structured Switch Result & Debug Switch Command (2026-04-11)

- `MatrixSessionOrchestrator.switch_to_session(...)` now returns structured result:
  - success flag
  - target session id
  - failure reason (`missing_session_id` / `session_not_found`)
  - resolved session object on success
- `MainWindowController` added debug switch entry:
  - `debug_switch_isolated_matrix_preview_session(session_id)`
  - uses orchestrator structured switch result and keeps debug-only guard semantics.

## 30. Debug Switch Shortcut & Failure Visibility (2026-04-11)

- Added hidden debug shortcut in MainWindow:
  - `Ctrl+Alt+Shift+J` -> switch isolated preview by explicit session id input
- Failure visibility:
  - switch failure now publishes reason/status in main status bar
  - reasons include `missing_session_id` and `session_not_found`.

## 31. Debug Switch Success Confirmation (2026-04-11)

- Switch success now publishes explicit confirmation fields in status text:
  - target session id (`switched_to=...`)
  - session entry tag (`entry=...`)
- Orchestrator debug snapshot now exposes:
  - `last_debug_preview_session_id`
- This improves manual verification of switch effects during phase-8 debug orchestration.

## 32. Debug Query Shortcut (2026-04-11)

- Added hidden debug shortcut:
  - `Ctrl+Alt+Shift+L`
  - displays current matrix session debug snapshot summary
- Current display focuses on high-signal fields:
  - session id list
  - `last_debug_preview_session_id`
  - `entry_counts`
- This provides direct observability without requiring logs or test hooks.

## 33. Debug Command Constant Table (2026-04-11)

- Added `matrix_session_debug_commands.py` as single source for:
  - debug action names
  - debug shortcuts
  - switch/query dialog strings
  - status-text formatters
- Current consumers:
  - `MainWindow` (debug action wiring and dialogs)
  - `MainWindowController` (debug status publishing and failure/success messages)

## 34. Debug Facade Layer (2026-04-11)

- Introduced `MatrixSessionDebugFacade` as a focused adapter above orchestrator.
- Controller-side non-default session entry calls now route through facade instead of
  directly combining policy + orchestrator logic.
- Assembly root now includes:
  - registry -> policy table -> manager -> orchestrator -> debug facade -> controller.

## 35. Entry Facade for New-File Pilot (2026-04-11)

- Introduced `MatrixSessionEntryFacade` for session-entry strategy resolution.
- Current scope:
  - resolves `new_file_pilot` on/off to session config (`mode`, `session_id`)
  - consumed by `MainWindowController.handle_new_file()`
- Assembly root now includes both facades:
  - registry -> policy table -> manager -> orchestrator -> (debug facade + entry facade) -> controller.

## 36. Phase 9 Transition Entry (2026-04-11)

Phase 8 status:
- baseline decoupling and non-default session orchestration seams are in place
- default shared behavior remains unchanged.

Phase 9 transition focus:
- move from debug-only controllability to one formal controlled entry
- define and freeze session switch contract for non-debug consumers
- prepare migration/deprecation plan for temporary debug-only command path.

## 37. Session Switch Contract Freeze (2026-04-11)

- `MatrixSessionOrchestrator.switch_to_session(...)` contract is now explicit:
  - inputs:
    - `session_id`
    - `expected_entry_names` (optional allow-list)
    - `requested_by` (caller identity)
  - output:
    - `SessionSwitchResult(success, session_id, reason, session, entry_name, requested_by, previous_active_session_id, active_session_id, rollback_performed)`

- Failure reasons are now a stable enum-like set:
  - `missing_session_id`
  - `session_not_found`
  - `entry_not_allowed`
  - `activation_failed`

- Switch ownership boundary:
  - page/controller layers should not implement ad-hoc switch logic.
  - switching must go through orchestrator/facade only.
  - current debug path (`MatrixSessionDebugFacade.switch_preview_session`) now passes:
    - allow-list: `preview`, `debug_preview`
    - caller id: `main_window.debug_preview_switch`

- Rollback semantics:
  - on pre-check rejection (`entry_not_allowed`) or activation failure (`activation_failed`),
    switch result reports `rollback_performed=True` and keeps previous active session identity.
  - active session tracking is provided by `MatrixSessionManager.activate()/get_active_session_id()`.

- Scope constraint remains unchanged:
  - default shared runtime behavior is not migrated in this step.
  - contract freeze applies to non-default sessionized entries first.

## 38. Transition Integration Checks (2026-04-11)

- Added explicit transition integration checks in:
  - [test_matrix_session_transition_flow.py](D:/PythonProject/TestFlowManager/tests/integration/test_matrix_session_transition_flow.py)

- Covered scenarios:
  - shared -> isolated (`new_file_pilot`) -> shared transition consistency
  - `preview` / `debug_preview` multi-session coexistence and independent close
  - mixed session set cleanup (`close_by_mode("isolated")`) keeps shared session intact

- Purpose:
  - lock phase-9 transition behavior before phase-10 multi-session object management.

## 39. Debug Channel Deprecation Plan (2026-04-11)

- Scope:
  - temporary debug shortcuts in `MainWindow`:
    - `Ctrl+Alt+Shift+M` / `K` / `J` / `L`
  - command definitions centralized in:
    - `matrix_session_debug_commands.py`

- Current policy (effective 2026-04-11):
  - debug shortcuts remain available only behind `TFM_ENABLE_DEBUG_COMMANDS`.
  - they are diagnostic-only and not considered formal business entry.

- Exit criteria to start deprecation:
  - one formal non-debug controlled entry is online and validated.
  - phase-9 regression suite passes consistently on session transition checks.
  - switch contract is consumed by non-debug path for at least one iteration without rollback incidents.

- Phase-10 planned action:
  - remove debug shortcut registration from `MainWindow` menu/shortcut wiring. (Completed 2026-04-11)
  - keep observability via tests/log snapshot paths (not via hidden UI actions).
  - remove debug-only command wiring after formal entry parity is confirmed.

## 40. Page Session Binding Baseline (2026-04-11)

- Added page-level session binding model as phase-10 entry baseline:
  - manager side:
    - `bind_page_session(page_id, session_id)`
    - `unbind_page_session(page_id)`
    - `get_page_session_id(page_id)`
    - `get_page_session_bindings()`
  - orchestrator side:
    - `bind_page_session(...)`
    - `get_bound_session_for_page(page_id)`
  - page side:
    - `MatrixPage.bind_session(...)`
    - `MatrixPage.clear_session_binding()`
    - `MatrixPage.get_session_binding()`

- Behavior note:
  - this step introduces explicit binding metadata only.
  - default shared mainline behavior is unchanged.
  - no page-switch business migration is performed in this baseline step.

## 41. Visible-Page Session Consistency Strategy (2026-04-11)

- Added controller-level consistency policy:
  - `MainWindowController.ensure_matrix_workspace_session_consistency(page_id="matrix.main")`

- Trigger point:
  - `MainWindow._on_page_changed_for_matrix(...)` when matrix page becomes visible.

- Strategy:
  - if page has no binding and an active session exists:
    - bind page to active session.
  - if page binding differs from active session:
    - switch via orchestrator contract (`bind_page_session(...)`).
  - if no binding and no active session:
    - keep default shared workspace semantics.

- Rollback semantics:
  - switch failures return structured failure result with rollback flag,
    and keep previously active session identity (as provided by switch contract).

- Constraint:
  - this is a consistency policy for sessionized entries; default shared baseline remains unchanged.

## 42. Session Cleanup Strategy Baseline (2026-04-11)

- Page-exit cleanup:
  - when matrix page is hidden, `MainWindow` now delegates to
    `MainWindowController.handle_matrix_workspace_hidden()`
    to release `matrix.main` page binding.

- Shutdown cleanup ordering:
  - `MainWindowController.shutdown()` now follows:
    1. clear page-session bindings (if manager supports it)
    2. close non-default isolated sessions
    3. continue existing auto-export/state-save/COM cleanup flow

- Manager support:
  - `MatrixSessionManager.clear_page_session_bindings()` added as explicit lifecycle API.

- Semantic boundary:
  - unbinding page mapping does not close session objects.
  - session close and rollback semantics remain under manager/orchestrator contract.

## 43. Debug UI Legacy Gate (2026-04-11)

- Debug command capability and debug UI exposure are now split:
  - capability gate: `TFM_ENABLE_DEBUG_COMMANDS`
  - legacy UI gate: `TFM_ENABLE_DEBUG_COMMANDS_UI`

- Current behavior (historical at this checkpoint):
  - both gates had to be enabled to register hidden debug shortcuts in `MainWindow`.
  - this set debug UI shortcut path to "default retired" while keeping diagnostic APIs available.
- Follow-up:
  - debug UI shortcut registration has since been fully removed (see section 45).

- Intent:
  - prevent continued reliance on debug shortcuts as business entry.
  - keep a controlled fallback during phase-10 migration window.

## 45. Debug UI Shortcut Removal (2026-04-11)

- `MainWindow` no longer registers hidden debug shortcuts in menu/shortcut wiring.
- Removed UI handlers:
  - `_on_debug_open_isolated_preview`
  - `_on_debug_close_isolated_preview`
  - `_on_debug_switch_isolated_preview`
  - `_on_debug_query_matrix_session_state`
- Removed controller/config legacy gate remnants:
  - `MainWindowController._is_legacy_debug_ui_enabled()`
  - `MatrixSessionDebugCommands.LEGACY_UI_GATE`
- Scope retained:
  - `MainWindowController` debug APIs remain available for test/log diagnostics.
  - session debug constants remain in `matrix_session_debug_commands.py` for controller-facing formatting.
- Result:
  - debug path is no longer reachable from UI shortcut layer
  - default shared behavior and non-debug entry path remain unchanged.

## 46. Debug Command Constant Table Minimization (2026-04-11)

- `matrix_session_debug_commands.py` has been reduced to controller-used formatters only:
  - `format_state_status(...)`
  - `format_switch_failed(...)`
  - `format_switch_success(...)`
- Removed as no-longer-used UI artifacts:
  - debug action text constants
  - debug shortcut constants
  - switch/query dialog text constants
  - `format_query_message(...)`
- Outcome:
  - debug diagnostics stay available through controller/test/log channels
  - debug UI-era constant surface is fully retired.

## 44. Phase-10 Integration Regression Upgrade (2026-04-11)

- Added integration suite:
  - [test_matrix_workspace_session_consistency_flow.py](D:/PythonProject/TestFlowManager/tests/integration/test_matrix_workspace_session_consistency_flow.py)

- New regression checks:
  - visible-page consistency can switch active session to page-bound target when allowed
  - disallowed bound entry triggers rollback semantics (`entry_not_allowed`) and keeps active session
  - shutdown mixed cleanup keeps shared session while clearing page bindings and closing isolated sessions

- Outcome:
  - phase-10 policy chain (binding -> consistency -> cleanup) now has integration-level regression coverage.

## 47. Phase-10 Closeout (2026-04-11)

- Phase-10 objective is accepted as completed:
  - page-level session binding model is online
  - visible-page consistency policy with rollback semantics is online
  - shutdown/page-hide cleanup order is locked
  - debug UI compatibility path is retired
- Regression baseline for phase-9/10 sessionization has been re-run together and passed (`119 passed`).
- Default shared behavior remains unchanged.

## 48. Phase-11 Handoff Notes

- Keep default `shared` as baseline; do not promote default isolated behavior yet.
- Next increment should focus on:
  - formal non-debug sessionized entry expansion (controlled + rollback-safe)
  - compatibility fallback surface reduction under existing guard tests
  - preventing direct switch logic bypass outside orchestrator/facade boundary.

## 49. 文档校准结论（2026-04-11）

- 本文档与 `project_session_state_flow.md`、`refactor_compatibility_backlog.md` 共完成 Session/Project 文档盘点，确保“残留兼容点”只在文档说明里出现，代码层面没有新的 `MatrixServiceProvider` / `current_project_context` fallback。
- 已在 `docs/matrix_session_switching_inventory.md` 说明 `src/app/composition/main_window_assembler.py` 通过 `MatrixWorkspaceCoordinator` 统一装配 `MatrixSessionRegistry/Manager/Orchestrator/Facades`，避免每个 view/controller 重复构建。
- 这次盘点锁定的剩余兼容点（文档、 guard、测试）均已指向具体 TODO，方便之后直接删除。
