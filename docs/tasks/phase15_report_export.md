# Phase 15 Report/Export Boundary Cleanup

> 更新时间：2026-04-11  
> 目的：将报告生成/更新彻底绑定到 `ProjectContext` + Matrix 会话，清理 leftover 的 `project_path` 字符串通道。

## 1. 目标

- 由 Phase 0‑14 保障的上下文/guard 已锁死“老通道”，下一步要在报告、设备更新流程里**完全依赖显式注入的 `ProjectContext` 和 `MatrixController`，摈弃 `ProjectContext.from_project_path` 的隱式补偿**。
- 同时，把 `ReportGenerationService`、`ReportUpdaterService` 的调用集中在一个协调者（coordinator）中，方便 future isolated session 或 API 调用复用。
- 结果：主窗口/控制器只负责传递 context/inputs，业务编排都在 coordinator 里，输出路径/COM 操作经过 `ProjectDocumentContext`/`OutputPathResolver` 计算，任何 legacy fallback 报错都在 guard tests 里被捕捉。

## 2. 任务拆解

### T15-1：新增 ReportExportCoordinator（当前阶段）

- 创建 `src/features/report_wizard/coordinator/report_export_coordinator.py`，封装 `ReportGenerationService` + `ReportUpdaterService`、`ProjectContext` 注入和“生成报告/更新设备” API。
- `ReportWizardController`、`ReportUpdaterController` 通过 coordinator 设置 context，并只依赖 coordinator 提供的 `load_header_data()`, `create_report_from_template()`, `update_equipment_list()` 方法。
- 这样可以把所有 `project_path` fallback 逻辑移动到 coordinator/service，控制器不再单独拼路径。

### T15-2：整合 Matrix/项目验证（后续）

- 把 `ReportWizardDialog`/`ReportUpdaterDialog` 里与 Matrix/ProjectContext 相关的 UI state 统一由 coordinator 读取（例如 header defaults, available reports）。
- 增加/更新 tests（可用 unit/integration）确认在 shared 和 isolated session context 下生成/更新流程仍可运行。

### T15-3：回归 & 文档

- 把 Phase 15 任务写入 `docs/refactor_task_board.md`、`docs/tasks/phase15_report_export.md`，列出 guard/tests/handshake commands（`python -m pytest tests/unit/test_report_wizard_controller.py` 等）。
- 编写 QA 验证脚本或说明，确保内外部团队可以根据文档操作（例如 “打开项目 → 生成报告” 的 manual smoke steps）。

## 3. 验收标准

1. `ReportWizardController` / `ReportUpdaterController` 不再直接构造 `ProjectContext`，全部通过 coordinator 上下文，并且 `set_project_path` 主动转为 `ProjectContext` 然后 `set_project_context`。
2. 新 coordinator 提供的 `create_report_from_template` 與 `update_equipment_list` API 都在 guard tests 中被覆盖（`tests/unit/test_report_export_coordinator.py` 提议增加）。
3. 文档和 `docs/refactor_task_board.md` 的 Phase‑15 段落描述明确“报告/更新流程在 coordinator 里统一上下文”，QA 可以根据 doc 跑 `python -m pytest tests/unit/test_report_export_coordinator.py`（需后续添加）。

## 4. 后续建议

- Phase 16 可以在此基础上把“客户报告 + LLCR/CR 导出”也迁移到 coordinator，并把 `MatrixExportService`/`MatrixApplicationService` 通过 coordinator 暴露给新的 isolated entry（比如 dedicated report preview window）。
- 持续维护 guard tests：T15 中 coordinator API 也应放入 `tools/run_phase14_guard_regression.ps1` 返回 list if necessary.

## 5. QA 与 Guard 验证

### 5.1 QA 验证步骤

1. 在主窗口打开项目，确保 `MainWindowController.project_context` 已被赋值。
2. 点击“生成报告”，确认 `ReportWizardController` 仅通过 `ReportExportCoordinator.create_report_from_template()` 生成文档，`ReportWizardDialog` 只靠 controller 传入的回调完成。
3. 点击“更新报告”，确认 `ReportUpdaterController` 把 `ProjectContext` 交给 coordinator，`ReportUpdaterService` 在明确上下文下执行设备更新，不再调用 `ProjectContext.from_project_path`。
4. 检查输出目录，确保报告/更新结果优先落在 `ProjectDocumentContext.resolve_submitted_material_dir()`/`OutputPathResolver` 解析的项目结构中，仅在无 ProjectContext 时才回退 `D:\OutFile`。

### 5.2 Guard + 回归命令

- `tools/run_phase14_guard_regression.ps1`（Phase 11/12 与 Phase 14 guard 共 143 条测试）仍然在 `.github/workflows/phase14-guard-lockdown.yml` 中作为 CI 命令，持续封死旧状态/Provider 通道；最新一次运行（2026-04-12）全部通过，记录为 Phase 15 验收一部分。
- 本地验证命令：

  ```powershell
  powershell -ExecutionPolicy Bypass -File tools/run_phase14_guard_regression.ps1
  ```

  输出含 `143 passed` 表示 guard/regression 套件与 Phase 15 coordinator 流协作正常。
