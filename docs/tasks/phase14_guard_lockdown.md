# Phase 14 Guard Lockdown

> 更新时间：2026-04-11  
> 目标人群：开发 / QA / 架构评审

## 1. 背景

在 Phase 0‑13 的重构中，主窗口、Matrix 会话、`ProjectContext` 与 `project.opened` 架构已经完成了剥离与收口，但旧的状态通道（`state_manager.current_project_context`、`current_project_context`）与 `MatrixServiceProvider` 历史 alias 仍留在文档中作为兼容说明。Phase 14 任务的核心是：**把“老通道”彻底在代码层面封死，增加 Guard tests 让未来任何尝试还原这些通道的改动都在 CI 阶段被拦截**。

## 2. 任务拆解

### T14-1：状态流 Guard

- 实现：`tests/unit/test_project_session_state_guard.py`（新建），遍历 `src/` 所有 `.py`，禁止除 `src/core/project_session_service.py` 以外的文件调用 `state_manager.set_state("current_project_context", …)`。
- 结果：当前代码库已经没有其他调用点，Guard 测试通过，任何后来尝试将 `state_manager` 作为旧 channel 重新写入 `current_project_context` 都会失败。

### T14-2：Provider Guard

- 实现：`tests/unit/test_matrix_service_provider_guard.py`（新建），简单搜索 `MatrixServiceProvider` 并确保它不再出现在 `src/` 目录。
- 结果：`MatrixServiceProvider` 模块已经删除，Guard 确保不会被未来代码重新引入，保持 Phase 11 guard “provider 调用为 0” 的约束。

## 3. 验收标准（适合非开发团队核对）

1. 文档 `docs/project_session_state_flow.md`、`docs/matrix_session_switching_inventory.md`、`docs/refactor_compatibility_backlog.md` 已同步说明 “ProjectContext + project.opened” 是唯一主线，Guard tests 列入 Phase 14 报告段落。
2. Guard tests 通过，输出与下面命令一致（截屏或日志可附上对应命令行标志）：
   ```bash
   python -m pytest tests/unit/test_project_session_state_guard.py -q
   python -m pytest tests/unit/test_matrix_service_provider_guard.py -q
   tools/run_phase14_guard_regression.ps1
   ```
3. CI/自动化运行中已包含上述 guard tests：
   - `docs/refactor_task_board.md` 的 Phase 14 回归命令已经加上 guard tests；
   - GitHub Actions workflow `Phase 14 Guard Lockdown` (`.github/workflows/phase14-guard-lockdown.yml`) 在 windows runner 跑 `tools/run_phase14_guard_regression.ps1`。
4. 任何后续试图写回 `state_manager.set_state("current_project_context", …)` 或引用 `MatrixServiceProvider` 会通过 Guard tests 直接失败，确保旧通道不再出现。

## 4. 建议的验证截图（手动作业）

- **Guard 通过**：捕捉 `pytest` 命令成功完成的终端截图（包含 guard tests 名称）。  
- **文档侧**：抓取 `docs/refactor_task_board.md` Phase 14 条目段落的部分页面，说明 guard 被纳入回归清单。  
- **CI 报告**：如果有回归流水线，可附上“guard tests in regression job” 的截图/日志（一般在部署报告中可以截取 green status + guard command 行）。

## 5. 后续建议

- 把 `tools/run_phase14_guard_regression.ps1` 放到 CI/回归脚本的 Guard stage，确保 guard tests 永远跟 Phase 11/12 的回归集合一起跑；当 guard 失败时即视作“旧通道”重现。
- Phase 15 可基于此 Guard Lockdown 继续扩展：例如官方 `isolated` 入口在 guard 保护下不会触碰老通道，再逐步展开新入口。  
- 定期（例如每个大版本）回顾 `docs/refactor_compatibility_backlog.md`，确认 guard tests 的 coverage 无盲点。
