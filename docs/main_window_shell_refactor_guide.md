# MainWindow Shell Refactor Guide

> Updated: 2026-04-13
> Scope: `src/features/main_window` first, `src/features/matrix` only for boundary cooperation

## 1. Purpose

This document consolidates the current refactor discussion around `MainWindow` into a single execution guide.
It answers four questions:

1. Why `MainWindow` needs another round of refactor
2. Why the next step should prioritize `main_window` instead of deep-diving into `matrix`
3. What the target architecture should look like
4. How to implement the change incrementally without breaking high-risk business flows

This guide is intended to be the execution companion for:

- [refactor_baseline.md](/D:/PythonProject/TestFlowManager/docs/refactor_baseline.md)
- [refactor_task_board.md](/D:/PythonProject/TestFlowManager/docs/refactor_task_board.md)
- [main_window_refactor.md](/D:/PythonProject/TestFlowManager/docs/main_window_refactor.md)

## 2. Background

`MainWindow` used to be both:

- the application shell
- the integration center for Matrix, project lifecycle, report flows, and some platform cleanup behavior

After several refactor iterations, the repository has already improved in these areas:

- `MatrixPage` exists and is no longer just a pile of child widgets owned directly by `MainWindow`
- `ProjectContext` has become the main project-session data carrier
- `ProjectSessionService` and `ProjectSessionCoordinator` already centralize part of the project-open side effects
- `main_window_assembler.py` has started to act as a composition root
- matrix session infrastructure (`registry / manager / orchestrator / entry facade / debug facade`) has already been introduced

However, the codebase is still in a transition state:

- `MainWindow` and `MainWindowController` still know too much about Matrix workspace/session internals
- project lifecycle logic is partially duplicated between old controller paths and newer coordinator-style paths
- some experimental or backup refactor files exist but are not actually part of the runtime mainline
- shell responsibilities and feature responsibilities are not yet fully separated

The result is that `MainWindow` is no longer the old “god object”, but it is still not a clean application shell.

## 3. Why MainWindow First

The next refactor phase should prioritize `main_window`, not deep internal `matrix` surgery.

Reasoning:

- `MainWindow` is still the application entry shell and top-level wiring point.
- As long as it continues to understand Matrix session internals, any deeper Matrix cleanup will be pulled back into shell coupling.
- A large part of the remaining Matrix complexity is not pure Matrix-domain complexity; it is shell-to-workspace boundary complexity.
- Refactoring `main_window` first is lower risk than immediately rewriting Matrix import/export or table behavior.

Recommended phase framing:

- Main target: make `MainWindow` a real shell
- Secondary target: compress `main_window -> matrix` into a stable boundary
- Explicit non-target for this phase: deep rewrite of `matrix_service` and Matrix domain internals

## 4. Current State Summary

### 4.1 MainWindow Current Responsibilities

At the moment, `MainWindow` and `MainWindowController` together still handle too many concerns:

- top-level UI shell
- navigation
- feature entry points
- project open/create entry orchestration
- Matrix workspace visibility / consistency / preview / pilot handling
- part of project-open side effects
- some shutdown sequencing awareness

This means shell concerns and feature concerns are still mixed.

### 4.2 Matrix Current State

`src/features/matrix` is in a middle state:

- better than the historical direct-child-widget era
- not yet a fully sealed independent workspace module

Current Matrix shape:

- external entry layer:
  - `matrix_project_controller.py`
  - `matrix_controller.py`
- page/UI layer:
  - `matrix_page.py`
  - `view/components/*`
  - `view/handlers/*`
- workspace/session layer:
  - `workspace/matrix_workspace_coordinator.py`
  - `service/matrix_session_*`
- service layer:
  - `matrix_application_service.py`
  - `matrix_import_service.py`
  - `matrix_export_service.py`
  - `matrix_service.py`

The critical observation is:

- Matrix is already close to being an independent workspace
- but `MainWindow` still has more Matrix infrastructure knowledge than a shell should

## 5. Current MainWindow -> Matrix Dependency Chain

The real runtime chain currently looks like this:

```text
application.py
  -> main_window_assembler.py
    -> MainWindow(matrix_workspace_coordinator=...)

MainWindow
  -> MainWindowController(matrix_workspace_coordinator=...)
  -> MatrixPage
  -> page-change hooks / matrix-related runtime attributes

MainWindowController
  -> MatrixWorkspaceCoordinator
    -> assemble_shared_session(...)
      -> matrix_project_controller
        -> matrix_controller
          -> matrix_application_service
          -> matrix_import_service
          -> matrix_export_service
          -> matrix_service
  -> ProjectSessionCoordinator(matrix_project_controller=...)
  -> project.opened / state.changed consumers
  -> matrix session consistency / preview / debug / hidden cleanup logic

Project open flow
  -> MainWindowController.handle_open_project()
    -> ProjectOpenService.prepare_project(...)
    -> project_session_service.apply_project_context(...)
      -> project.opened
        -> MainWindowController._on_project_opened(...)
          -> ProjectSessionCoordinator.apply_project_context(...)
            -> matrix workspace refresh
            -> matrix.xlsx auto import
```

The coupling is no longer at table-widget level, but it is still strong at workspace/session level.

## 6. Current vs Target Responsibilities

| Area | Current responsibilities | Target responsibilities |
| --- | --- | --- |
| `MainWindow` / `main_window_ui.py` | shell UI + page assembly + feature lazy load + some feature-specific routing | shell UI only: menu, navigation, page container, status bar, window-level signals |
| navigation | maintained directly in main window flow | independent view-layer navigation component or page registry |
| project lifecycle | partially orchestrated in `MainWindowController` | single lifecycle entry object |
| Matrix integration | shell/controller know workspace/session details | shell only knows `MatrixPage` and a high-level Matrix facade |
| feature entry | shell lazy-loads and partially configures feature controllers | feature pages/actions register into shell; shell does not know internal feature composition |
| shutdown | shell/controller still know some feature cleanup sequencing | shell emits shutdown; service/coordinator owns cleanup sequencing |

## 7. Why “Dual Track” Is Dangerous

One recurring problem in the current repository is what this guide calls dual-track behavior.

Dual track means:

- the old controller path still exists and still looks “mainline”
- a newer coordinator/facade path also exists and also looks “mainline”
- both can orchestrate the same lifecycle concern

Typical example:

- `MainWindowController` still contains project lifecycle orchestration
- `ProjectLifecycleCoordinator` also exists as a candidate lifecycle orchestrator

If both remain alive, the repository suffers from:

- unclear ownership: developers do not know which path is the real one
- behavior drift: one path gets updated, the other silently becomes stale
- documentation drift: docs say “coordinator owns the flow”, runtime still uses controller
- test drift: tests may cover the new path while real runtime still goes through the old path

This is why “introducing a coordinator” is not enough.
If a coordinator takes over, it must become the only real entry, and the previous path must shrink into thin forwarding or be deleted.

## 8. What “MainWindow as Shell” Actually Means

`MainWindow` should not become empty.
It should become a disciplined shell with a stable surface.

The shell should own:

- application window
- menu and global actions
- navigation and page stack
- status bar
- current page identity
- top-level page registration
- top-level session/project display

The shell should not own:

- Matrix internal table logic
- Matrix import/export details
- LTR editor internal flow
- report generation/update workflow internals
- duplicate project-open side effects

Target mental model:

```text
MainWindow
  -> shell container
  -> navigation
  -> page stack
  -> top-level actions

MainWindowController
  -> shell orchestration
  -> project lifecycle entry
  -> high-level workspace gateways

MatrixPage
  -> Matrix UI
  -> Matrix runtime behavior
  -> Matrix controllers/services
```

## 9. Recommended Phase Goal

For the next mainline refactor step, define the phase goal as:

### Phase A: MainWindow Shell Consolidation

Goals:

- make `MainWindow` a real shell
- compress `main_window -> matrix` into stable, limited interfaces
- eliminate dual-track lifecycle orchestration
- keep existing business behavior stable

Non-goals:

- no large rewrite of Matrix domain logic
- no redesign of Matrix import/export file format
- no COM-flow behavior changes

## 10. Recommended Task Sequence

This is the recommended execution order.
Do not reorder unless a blocker forces it.

### Step 1. Freeze the shell boundary

Identify what must remain in `main_window_ui.py`:

- menu
- navigation widgets
- page stack
- status bar
- window behavior

Everything else becomes a migration candidate.

Expected result:

- `MainWindow` becomes visibly easier to read
- shell-only responsibilities become explicit

### Step 2. Move page registration out of ad hoc shell logic

Introduce a page registration model such as:

```text
page_id
title
breadcrumb
subtitle
page_factory or page object
default flag
```

Recommended direction:

- `MainWindow` consumes page definitions
- feature pages register themselves through shell-friendly interfaces
- shell no longer knows page-internal composition details

Expected result:

- navigation and page registration become declarative
- adding a page no longer requires wiring feature internals into shell code

### Step 3. Compress MainWindowController -> Matrix coupling

Current problem:

- `MainWindowController` directly owns too much Matrix session infrastructure knowledge

Recommended change:

- replace direct ownership of session internals with one high-level matrix workspace facade/gateway

The controller should not directly own:

- `MatrixSessionRegistry`
- `MatrixSessionManager`
- `MatrixSessionOrchestrator`
- debug/entry facades

The controller should instead depend on a higher-level Matrix shell boundary such as:

- `MatrixWorkspaceFacade`
- or a similarly named gateway

That boundary should expose:

- main workspace access
- page visible/hidden hooks
- preview/pilot operations when needed
- workspace/session metadata query

Expected result:

- shell orchestration no longer depends on Matrix infrastructure details

### Step 4. Decide whether ProjectLifecycleCoordinator will take over

This must be an explicit decision.

If `ProjectLifecycleCoordinator` takes over:

- it becomes the real lifecycle owner for project open/create shell actions
- `MainWindowController` becomes a thin forwarding entry
- duplicated lifecycle logic must be removed from controller paths

If it does not take over:

- the coordinator should not remain as a “future maybe mainline” implementation
- either delete it or downgrade it into explicit experimental/backlog status

Expected result:

- no dual-track lifecycle logic remains

### Step 5. Move Matrix page visibility policy behind the Matrix boundary

Current problem:

- shell still contains Matrix-specific page-visible / page-hidden logic

Recommended change:

- `MainWindow` emits page change
- controller forwards page identity
- Matrix workspace facade decides what to do when `matrix.main` becomes visible/hidden

Expected result:

- shell stops knowing page-session binding semantics
- Matrix workspace semantics stay inside Matrix-owned boundaries

### Step 5 Status Check and Exit Criteria

Use the following checklist to decide whether Step 5 is actually complete.
Do not close Step 5 merely because page-change hooks and facade methods already exist.

Step 5 can be considered complete only if all items below are true:

- `MainWindow` does not hardcode that a specific stack index such as `0` means Matrix
- `MainWindow` does not directly call `MatrixPage.bind_session(...)`
- `MainWindow` does not directly call `MatrixPage.handle_page_activated()`
- `MainWindow` only forwards page identity or page-change events; it does not implement Matrix visibility policy
- `MainWindowController` only forwards shell page visibility to a Matrix-facing boundary
- Matrix session binding, visible/hidden policy, and activation semantics all stay behind `MatrixWorkspaceFacade` or another Matrix-owned gateway
- Matrix visible/hidden behavior is expressed by page id such as `matrix.main`, not by shell-local index assumptions

Current repository status against that checklist:

- completed:
  - `MainWindowController` already forwards visible/hidden handling to `MatrixWorkspaceFacade`
  - `MatrixWorkspaceFacade` already exposes `on_page_visible(...)` and `on_page_hidden(...)`
  - page-level session consistency logic has moved behind the Matrix boundary
  - `MainWindow` routes Matrix visibility by `page_id`
  - `MainWindow` no longer directly calls `self.matrix_page.bind_session(...)`
  - `MainWindow` no longer directly calls `self.matrix_page.handle_page_activated()`
  - duplicate `_on_page_changed_for_matrix(...)` shell path has been removed
- remaining note:
  - Step 5 runtime cleanup is complete; any follow-up should now be treated as Step 6+ scope, not Step 5 blocker

Current evidence in runtime code:

- `src/features/main_window/view/main_window_ui.py`
  - `_apply_nav_index(...)` forwards page hidden/visible by `page_id`
  - `_on_page_visible(...)` only forwards page identity to controller
  - `activate_matrix_workspace()` resolves Matrix page by `page_id`, not shell-local fixed index
- `src/features/main_window/controller/main_window_controller.py`
  - visible/hidden hooks are delegated to `MatrixWorkspaceFacade`
- `src/features/main_window/facade/matrix_workspace_facade.py`
  - Matrix-owned boundary now performs session binding and first-activation behavior

Recommended remaining work to finish Step 5:

1. Verify no downstream module reintroduces shell-side Matrix visible/hidden policy.
2. Keep new tests aligned to the single forwarding path: `_apply_nav_index(...)` + `_on_page_visible(...)`.
3. Treat any additional shell cleanup as Step 6 work, not as unfinished Step 5 work.

Suggested minimum acceptance check after the cleanup:

- searching `main_window_ui.py` should no longer show:
  - `index == 0` for Matrix-specific page policy
  - direct calls to `self.matrix_page.bind_session(...)`
  - direct calls to `self.matrix_page.handle_page_activated()`
  - `_on_page_changed_for_matrix(...)`
- shell code should only express:
  - current page changed
  - page id
  - generic navigation synchronization

Practical conclusion:

- as of the current mainline, Step 5 can be considered complete
- Step 6 is now the formal next active implementation step

Focused validation used to close Step 5:

- `python -m py_compile src/features/main_window/view/main_window_ui.py src/features/main_window/facade/matrix_workspace_facade.py`
- `python -m pytest -q tests/unit/test_main_window_ui_session_policy_assembly.py`

### Step 6. Remove shell-level feature-specific lazy wiring ✅ IMPLEMENTED

Current problem:

- shell still lazily instantiates some feature controllers directly

Recommended change:

- shell should use page factories, feature entry handlers, or feature page providers
- feature-specific runtime construction should be outside shell UI code

Implementation:

- Created `MainWindowFeatureRegistry` in `src/features/main_window/service/main_window_feature_registry.py`
- Registry owns lazy construction of 4 feature controllers:
  - `CustomerReportController`
  - `ReportWizardController`
  - `DocumentParserController`
  - `ReportUpdaterController`
- Registry provides 5 shell-facing action methods:
  - `run_create_report(project_context, matrix_controller)`
  - `run_update_report(project_context)`
  - `run_convert_customer_report(project_context)`
  - `run_edit_body_content(file_path)`
  - `run_encrypt_test_files()`
- `MainWindow` action handlers now forward to registry instead of directly instantiating controllers
- Removed 4 lazy properties from `MainWindow`
- Removed direct feature controller imports from `main_window_ui.py`

Expected result:

- `MainWindow` no longer acts as a hidden service locator ✅ ACHIEVED

Validation:

- `tests/unit/test_main_window_feature_registry_wiring.py` - 9 tests for shell wiring
- `tests/unit/test_main_window_controller_facade_injection.py` - AST guards for facade boundary
- Old `test_main_window_controller_session_manager_injection.py` removed (stale test)
- Focused Step 6 acceptance set:
  - `python -m pytest -q tests/unit/test_main_window_ui_session_policy_assembly.py`
  - `python -m pytest -q tests/unit/test_main_window_feature_registry_wiring.py`
  - `python -m pytest -q tests/unit/test_main_window_controller_facade_injection.py`
- `python -m pytest -q tests/unit -k "main_window"` is not a Step 6 mandatory acceptance command because it currently includes unrelated `main_window` collection paths beyond Step 6 shell wiring scope

### Step 7. Only after shell consolidation, proceed into Matrix internals

Once the shell boundary is stable, start a separate Matrix-focused phase:

- clarify `matrix_project_controller` vs `matrix_controller`
- continue shrinking `matrix_service.py`
- further isolate workspace/session behavior

Expected result:

- Matrix refactor becomes module-internal optimization, not shell-boundary repair

### Step 7 Architecture Decision Principle

At the current repository stage, do **not** treat the next step as
"fully remove every remaining MainWindow -> Matrix direct dependency first".

That is not the preferred order anymore.

Use this decision rule instead:

- freeze `main_window` at the Step 6 shell boundary unless a Step 7 change strictly requires a shell adjustment
- move into Matrix-internal consolidation first
- let remaining shell-to-Matrix coupling shrink as a consequence of clearer Matrix-owned boundaries

Why:

- the most dangerous shell-side coupling has already been reduced in Step 5 and Step 6
- several remaining couplings are symptoms of unfinished Matrix-internal ownership, not proof that shell must be refactored again first
- forcing shell-side decoupling before Matrix internals are coherent would likely create new placeholder abstractions with unstable ownership

Current practical interpretation:

- `main_window` is no longer the primary refactor target
- `matrix_project_controller`, `matrix_controller`, `matrix_service.py`, and Matrix workspace/session internals are now the primary target
- only make new `main_window` changes when they are the minimum compatibility move needed to support Matrix-internal consolidation

In short:

> do not keep peeling `main_window` first; make Matrix worth depending on, then let shell thin further afterward

## 11. Detailed Operation Guide

### 11.1 Audit before changing code

Before any edit, produce and verify these lists:

- shell-only responsibilities in `main_window_ui.py`
- feature-specific responsibilities in `main_window_ui.py`
- Matrix infrastructure responsibilities currently in `MainWindowController`
- project lifecycle responsibilities currently duplicated across controller/coordinator
- current runtime entry points for:
  - open project
  - create project
  - page changed to `matrix.main`
  - shutdown

Do not start by renaming files or moving directories without a responsibility map.

### 11.2 Introduce one shell-facing page model

Create a page-definition abstraction.
It may be a dataclass, registry entry, or a lightweight object.

It should contain at least:

- `page_id`
- `nav_title`
- `breadcrumb`
- `subtitle`
- `page_factory` or `page_instance`
- `default`

Then convert shell navigation to consume that model instead of manually scattered page wiring.

### 11.3 Introduce one shell-facing Matrix gateway

The shell should talk to Matrix through one stable boundary.

This gateway should be responsible for:

- obtaining the main shared Matrix workspace/controller
- handling page visible/hidden callbacks
- handling preview/pilot paths if those are kept
- exposing session binding metadata when shell needs display-only information

The shell should not directly know:

- how shared/isolated sessions are assembled
- how rollback and entry policy are enforced
- how page-session binding is stored

### 11.4 Normalize lifecycle ownership

Pick one of these and enforce it:

- `MainWindowController` remains lifecycle owner
- or `ProjectLifecycleCoordinator` becomes lifecycle owner

Recommended direction:

- make `ProjectLifecycleCoordinator` the real owner if it is kept
- reduce `MainWindowController` to forwarding plus shell concerns

Mandatory rule:

- there must be exactly one real project-open orchestration path

### 11.5 Keep business behavior stable

High-risk flows that must not regress:

- open project
- create project
- auto import `matrix.xlsx`
- Matrix editing
- Matrix export
- LTR application processing
- report generation / update / customer report conversion

Any shell refactor must preserve:

- user-visible entry path
- project-context propagation timing
- shutdown cleanup sequencing

### 11.6 Clean up stale or misleading backup code

Once the real shell path is chosen, clean up misleading leftovers:

- duplicate dialog paths
- dead navigation backup implementations
- abandoned integration shells
- coordinator/facade files that never actually became part of runtime

If a backup file is intentionally retained, it must be clearly marked as:

- experimental
- not part of runtime mainline

Do not let “future candidate” files continue to look like current mainline.

## 12. Acceptance Criteria

This phase can be considered complete only if all of the following are true:

1. `MainWindow` is readable as shell code
2. `MainWindowController` no longer directly owns Matrix session internals
3. there is only one real project lifecycle orchestration path
4. shell does not directly encode Matrix workspace binding rules
5. Matrix remains the default core page, but its internals are not embedded into shell
6. all mainline imports and docs reflect the actual chosen path
7. relevant regression checks still pass

## 13. Recommended Validation

At minimum, one or more of the following should be run after each incremental step:

- related `pytest`
- `python -m py_compile` for touched Python modules
- text/AST guards where lifecycle ownership or import boundaries are important

Priority regression paths:

- open project
- create project
- project session application
- Matrix auto import
- Matrix export

If GUI automation is not available, document the remaining manual smoke requirement explicitly.

## 14. Practical Next Actions

Use this exact execution order for the next round:

1. Inventory shell-only vs feature-only logic in `main_window_ui.py`
2. Inventory Matrix-specific infrastructure knowledge in `MainWindowController`
3. Decide whether `ProjectLifecycleCoordinator` is promoted or removed
4. Introduce shell-facing page registration and one shell-facing Matrix gateway
5. Migrate page-visible / page-hidden Matrix handling behind the Matrix boundary
6. Remove stale dual-track code
7. Re-run focused regression checks

## 15. Final Principle

For this repository, the guiding rule is:

> Keep Matrix as the default core workspace, but stop letting MainWindow own Matrix internals.

That means:

- Matrix keeps product importance
- MainWindow regains architectural discipline
- future Matrix refactor becomes easier, safer, and more local
