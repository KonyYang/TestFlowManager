# Refactor Compatibility Backlog

This file tracks temporary compatibility aliases and legacy channels retained during refactor,
and serves as the removal checklist.

## 1. Removed Compatibility Aliases

- `show_matrix_dialog()`
- `open_matrix_dialog()`
- `_safe_open_matrix_dialog()`

## 2. Legacy Attribute Channels (Historical)

Historical channels that existed during transition:

- `matrix_controller.project_data_file_path`
- `matrix_service.project_data_file_path`

Mainline strategy:

- Read path from `ProjectContext` first.
- Keep compatibility fallback only when strictly required.
- Remove write-side compatibility once all consumers are migrated.

## 3. Completed Cleanup

- Removed `matrix_integration.py`
- Removed `matrix_dialog.py`
- Removed local `_build_project_context()` fallback path from
  `MainWindowController._on_project_opened()`
- Switched `main_window_controller.py -> project_creator` to direct file import to avoid package cycle import

## 4. Removed Compatibility Modules (Phase-11)

- Removed `matrix_service_provider.py` (2026-04-11):
  - production code now assembles services via `MatrixSessionRegistry` / `MatrixSessionFactory`
  - shared anchor is `MatrixService.shared()` (registry-scoped)

## 7. Phase-10 Closeout Snapshot (2026-04-11)

- Debug UI compatibility layer has been fully retired:
  - no hidden debug shortcut registration in `MainWindow`
  - no legacy debug UI gate in controller/constants
- `matrix_session_debug_commands.py` has been minimized to controller-used status formatters only.
- Phase 9/10 regression suite passed as a combined verification set (`119 passed`).

## 8. Phase-11 Candidate Carry-Over

1. Keep direct `MatrixService` access strictly scoped to `MatrixSessionRegistry` (guarded).
2. Re-check remaining historical references documented in session/context flow docs and
   convert them into explicit removal tasks only when covered by tests.

## 9. Phase-11 Progress (2026-04-11)

- Removed `MatrixServiceProvider.get_service()` fallback from:
  - `MatrixController` (now requires explicit `matrix_service` injection)
  - `MatrixProjectController` (now requires explicit `matrix_controller` injection)
- Updated guard allow-list accordingly and adjusted unit tests.
- Removed `MatrixServiceProvider.get_shared_service()` legacy alias (no production consumers).
- Added assembly guard tests to prevent direct construction outside `MatrixSessionFactory`.
- `MatrixSessionFactory` routes shared/isolated selection through `MatrixSessionRegistry` (provider module deleted).
- Guard upgrades:
  - `MatrixServiceProvider.get_service()` is now expected to have 0 call sites under `src/`.
  - `MatrixServiceProvider` switch methods (`set/reset provider` and `set/reset factory`) have 0 call sites under `src/` (provider wiring retired).
  - `MatrixSessionRegistry.install()/uninstall()` has been removed (provider wiring fully retired); guard remains to prevent reintroduction.
  - `matrix_service_provider` module is guarded as "not imported from src" (and has been deleted).

## 5. Incremental Cleanup Update (2026-04-10)

Completed in this step:

- Removed `basic_info_dialog.py` fallback read:
  `getattr(parent, "project_data_file_path", None)`.
- Replaced `LTRProjectIntegrationService.project_data_file_path` mainline usage with:
  `project_json_path` and `get_project_json_path()`.
- Cleared historical `project_data_file_path` residue from `matrix_service_backup.py`.

## 6. Incremental Cleanup Update (2026-04-11)

Completed in this step:

- Updated guard expectations after deleting `matrix_service_provider.py`:
  - direct `MatrixService` import is allowed only in `matrix_session_registry.py`
  - `MatrixServiceProvider.*` call/import surfaces under `src/` must remain empty

Current conclusion:

- Shared matrix service compatibility access is now under automated guard coverage.
- No new provider bypass points should be introduced without test breakage.

## 10. Phase-13 Taskization Progress (2026-04-11)

High-risk compatibility cleanups have been converted into explicit tasks and started:

1. Project-creation entry side-effect consolidation:
   - `ProjectCreatorController` no longer duplicates Matrix-side side effects in `shared` mode
     when the main window controller exists; isolated pilot keeps local Matrix context application.
   - Covered by unit regression (`test_project_creator_flow.py`).
2. Remaining carry-over items are tracked in the task board under "Phase 13 兼容收口任务化".

## 11. Phase-13 文档盘点（2026-04-11）

- Session/Project 文档盘点已完成：`project_session_state_flow.md`、`matrix_session_switching_inventory.md` 与本文件都指向相同的“已收口/剩余兼容点”清单，文档内容与代码搜索结果一致。
- 已在文档中记录 `MatrixWorkspaceCoordinator` 作为 `src/app/composition/main_window_assembler.py` 的统一组装点，替代了旧有的 MainWindow 直接创建 `MatrixSessionManager` 的行为。
- 这次盘点也把剩余兼容点限定为文档级警示（refactor_task_board.md 的 Phase-13 任务），后续只需在文档/guard/测试里跟踪，代码层面不存在新曝光。
- 作为 “永远闭通道” 的验证，Phase-14 guard tests (`tests/unit/test_project_session_state_guard.py` + `tests/unit/test_matrix_service_provider_guard.py`) 已纳入 Phase 11/12+ guard 回归清单，任何 attempt 要写旧通道都会在 CI 阶段被提醒。

## 12. Phase-14 Guard Lockdown（2026-04-11）

- 新增 guard tests 已上线：
  - `tests/unit/test_project_session_state_guard.py` 保证 `current_project_context` 只有 `ProjectSessionService` 写入；
  - `tests/unit/test_matrix_service_provider_guard.py` 确保 `MatrixServiceProvider` 没有 `src/` 代码路径。
- 结果：旧的状态通道和 provider 入口在代码层面完全消失，只在文档中留存“历史兼容备注”，任何尝试绕过默认路径的提议都会在 guard tests 里立刻被发现。
