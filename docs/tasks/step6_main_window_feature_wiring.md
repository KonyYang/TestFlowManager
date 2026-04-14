# Step 6 MainWindow Feature Wiring Execution Guide

> Updated: 2026-04-14
> Scope: `src/features/main_window` shell layer first
> Prerequisite: Step 5 is complete

## Current Status

**Implementation: COMPLETE** ✅

- `MainWindowFeatureRegistry` created and integrated
- `main_window_ui.py` no longer directly imports feature controllers
- 4 lazy properties removed from `MainWindow`
- 5 action handlers rewritten to forward through registry
- All syntax and lint checks pass

**Closure Status: COMPLETE**

- Focused Step 6 regression coverage is in place
- Legacy controller-injection guard has been replaced
- Step 6 acceptance is based on the focused shell-wiring suite below, not on the broader `tests/unit -k "main_window"` subset

## 1. Purpose

This document is the execution guide for `Step 6` in
`docs/main_window_shell_refactor_guide.md`.

Step 6 goal:

- remove shell-level feature-specific lazy wiring
- stop letting `MainWindow` directly instantiate feature controllers
- keep `MainWindow` as shell UI and action-forwarding layer only
- preserve current business behavior

This step is not about redesigning feature internals.
It is about moving feature runtime assembly out of `MainWindow`.

## 2. Current Problem

`MainWindow` still directly owns feature-specific lazy wiring in
`src/features/main_window/view/main_window_ui.py`.

Typical current problems:

- `MainWindow` lazily creates feature controllers itself
- shell action handlers call feature controller methods directly
- shell knows feature construction details
- adding a feature still requires wiring runtime assembly into shell UI code

Current direct shell-owned feature wiring includes:

- `CustomerReportController`
- `ReportWizardController`
- `DocumentParserController`
- `ReportUpdaterController`
- runtime import and launch of `FileEncryptionController`

Relevant current code areas:

- `src/features/main_window/view/main_window_ui.py`
  - lazy properties for feature controllers
  - `_on_create_report()`
  - `_on_update_report()`
  - `_on_convert_customer_version()`
  - `_on_edit_body_content()`
  - `_on_encrypt_test_files()`

## 3. Target State

After Step 6:

- `MainWindow` does not directly instantiate feature controllers
- `MainWindow` does not own feature-specific lazy properties
- `MainWindow` only collects UI input and forwards actions
- feature runtime assembly lives in one shell-external entry object

Recommended minimal target structure:

```text
MainWindow
  -> MainWindowController
  -> MainWindowFeatureRegistry   # or similarly named shell-external entry

MainWindowFeatureRegistry
  -> lazy create feature controllers on demand
  -> expose feature action methods
  -> hide construction details from MainWindow
```

This does not need to become a generic plugin framework yet.
Keep it small and explicit.

## 4. Recommended New File

Create:

- `src/features/main_window/service/main_window_feature_registry.py`

Recommended responsibility:

- own lazy construction of shell-triggered feature controllers
- provide feature action methods for shell use
- keep shell-visible API narrow

Do not put business logic here that belongs inside feature modules.
This object is a shell-facing assembly and forwarding layer.

## 5. Execution Order

Do not reorder unless blocked.

### Step 6.1 Create the feature registry

Create `MainWindowFeatureRegistry` with:

- one constructor receiving `main_window`
- internal cached fields for feature controllers
- small getter methods for lazy instantiation
- action methods that `MainWindow` can call directly

Recommended internal cached fields:

- `_customer_report_controller`
- `_report_wizard_controller`
- `_document_parser_controller`
- `_report_updater_controller`

Recommended constructor shape:

```python
class MainWindowFeatureRegistry:
    def __init__(self, main_window):
        self.main_window = main_window
        self._customer_report_controller = None
        self._report_wizard_controller = None
        self._document_parser_controller = None
        self._report_updater_controller = None
```

### Step 6.2 Move controller lazy creation into the registry

From `MainWindow`, migrate the current lazy property logic into registry getter methods.

Recommended getters:

- `get_customer_report_controller()`
- `get_report_wizard_controller()`
- `get_document_parser_controller()`
- `get_report_updater_controller()`

Behavior rule:

- preserve current controller constructor arguments
- preserve lazy creation behavior
- do not change controller semantics in this step

### Step 6.3 Add shell-facing action methods to the registry

Add explicit action methods to the registry.

Recommended methods:

- `run_create_report(project_context, matrix_controller)`
- `run_update_report(project_context)`
- `run_convert_customer_report(project_context)`
- `run_edit_body_content(file_path)`
- `run_encrypt_test_files()`

Recommended semantics:

- shell gives the registry the minimal input it collected
- registry resolves the correct controller
- registry calls the existing feature entry method

Keep method names explicit.
Do not introduce over-generic names such as `run_action(...)`.

### Step 6.4 Inject the registry into MainWindow

Add one field in `MainWindow`:

- `self._feature_registry`

Initialize it after shell/controller setup is available.

Recommended place:

- in `_initialize_controllers()`
- or immediately after controller initialization during startup

Preferred pattern:

```python
self._feature_registry = MainWindowFeatureRegistry(self)
```

Why:

- registry depends on the shell object for current UI context
- this keeps Step 6 small and avoids premature inversion work

### Step 6.5 Remove feature-specific lazy properties from MainWindow

Delete the following shell-owned properties after the registry is in place:

- `customer_report_controller`
- `report_wizard_controller`
- `document_parser_controller`
- `report_updater_controller`

Acceptance rule:

- after this step, `main_window_ui.py` should no longer instantiate those controllers directly

### Step 6.6 Rewrite shell action handlers to call the registry

Refactor these methods in `main_window_ui.py`:

- `_on_create_report()`
- `_on_update_report()`
- `_on_convert_customer_version()`
- `_on_edit_body_content()`
- `_on_encrypt_test_files()`

Target pattern:

- shell gathers UI input
- shell calls registry method
- shell updates status if needed

Example direction:

```python
def _on_create_report(self) -> None:
    logger.debug("Create report action triggered")
    self._feature_registry.run_create_report(
        self.controller.project_context,
        self.matrix_controller,
    )
    self._update_status()
```

For `_on_edit_body_content()`:

- keep `QFileDialog.getOpenFileName(...)` in shell
- after file selection, pass `file_path` into registry

This is acceptable because file-selection dialog is shell/UI behavior.

For `_on_encrypt_test_files()`:

- move runtime import and controller launch into registry
- shell should no longer import `FileEncryptionController` directly

### Step 6.7 Keep behavior stable

Do not change:

- report wizard behavior
- report updater flow
- customer report generation entry behavior
- document parser dialog behavior
- file encryption launch behavior

Do not change controller constructor signatures unless absolutely necessary.

Do not combine Step 6 with:

- page registration redesign
- feature page provider redesign
- coordinator redesign inside feature modules

Those belong to later steps if needed.

## 6. Recommended File-Level Changes

### 6.1 Create the registry file

Create:

- `src/features/main_window/service/main_window_feature_registry.py`

Expected imports:

- `CustomerReportController`
- `ReportWizardController`
- `DocumentParserController`
- `ReportUpdaterController`
- `logger`

Optional:

- method-local import for `FileEncryptionController`

### 6.2 Update MainWindow imports

In `src/features/main_window/view/main_window_ui.py`:

- add import for `MainWindowFeatureRegistry`
- remove direct feature controller imports after migration

Expected removals from shell imports:

- `CustomerReportController`
- `ReportWizardController`
- `DocumentParserController`
- `ReportUpdaterController`

### 6.3 Update MainWindow fields

Remove or stop using:

- `_customer_report_controller`
- `_report_wizard_controller`
- `_document_parser_controller`
- `_report_updater_controller`

Add:

- `_feature_registry`

## 7. Suggested Registry Skeleton

Use this as a minimal direction, not as a strict template:

```python
from src.core.logger import logger
from src.features.customer_report_generator.controller.customer_report_controller import CustomerReportController
from src.features.report_wizard.controller.report_wizard_controller import ReportWizardController
from src.features.document_parser.controller.document_parser_controller import DocumentParserController
from src.features.report_updater.controller.report_updater_controller import ReportUpdaterController


class MainWindowFeatureRegistry:
    def __init__(self, main_window):
        self.main_window = main_window
        self._customer_report_controller = None
        self._report_wizard_controller = None
        self._document_parser_controller = None
        self._report_updater_controller = None

    def get_customer_report_controller(self):
        if self._customer_report_controller is None:
            logger.debug("Lazy loading CustomerReportController")
            self._customer_report_controller = CustomerReportController(self.main_window)
        return self._customer_report_controller

    def get_report_wizard_controller(self):
        if self._report_wizard_controller is None:
            logger.debug("Lazy loading ReportWizardController")
            self._report_wizard_controller = ReportWizardController(self.main_window)
        return self._report_wizard_controller

    def get_document_parser_controller(self):
        if self._document_parser_controller is None:
            logger.debug("Lazy loading DocumentParserController")
            self._document_parser_controller = DocumentParserController(self.main_window)
        return self._document_parser_controller

    def get_report_updater_controller(self):
        if self._report_updater_controller is None:
            logger.debug("Lazy loading ReportUpdaterController")
            self._report_updater_controller = ReportUpdaterController(self.main_window)
        return self._report_updater_controller

    def run_create_report(self, project_context, matrix_controller):
        controller = self.get_report_wizard_controller()
        controller.set_project_context(project_context)
        controller.set_matrix_controller(matrix_controller)
        controller.show_wizard()

    def run_update_report(self, project_context):
        controller = self.get_report_updater_controller()
        controller.set_project_context(project_context)
        controller.show_report_updater_dialog()

    def run_convert_customer_report(self, project_context):
        controller = self.get_customer_report_controller()
        return controller.handle_generate_customer_report_with_context(project_context)

    def run_edit_body_content(self, file_path):
        controller = self.get_document_parser_controller()
        controller.show_body_content_editor(file_path)

    def run_encrypt_test_files(self):
        from src.features.file_encryption.controller.file_encryption_controller import FileEncryptionController

        controller = FileEncryptionController(self.main_window)
        folder_path = controller.show_folder_selection()
        if folder_path:
            controller.start_encryption_task(folder_path)
```

## 8. Detailed Acceptance Checklist

Step 6 can be considered complete only if all items below are true:

- `main_window_ui.py` no longer imports:
  - `CustomerReportController`
  - `ReportWizardController`
  - `DocumentParserController`
  - `ReportUpdaterController`
- `MainWindow` no longer owns lazy properties for those controllers
- shell action handlers call `MainWindowFeatureRegistry` instead of feature controllers directly
- shell still owns UI-only concerns such as file selection dialogs
- feature business behavior remains unchanged

Recommended search-based acceptance checks:

- search `main_window_ui.py` for:
  - `CustomerReportController(`
  - `ReportWizardController(`
  - `DocumentParserController(`
  - `ReportUpdaterController(`
- expected result:
  - no matches in `main_window_ui.py`

Also search for:

- `def customer_report_controller`
- `def report_wizard_controller`
- `def document_parser_controller`
- `def report_updater_controller`

Expected result:

- removed from `MainWindow`

## 9. Validation Plan

At minimum run:

- `python -m py_compile src/features/main_window/view/main_window_ui.py src/features/main_window/service/main_window_feature_registry.py`

Recommended focused tests:

- `python -m pytest -q tests/unit/test_main_window_ui_session_policy_assembly.py`
- `python -m pytest -q tests/unit/test_main_window_feature_registry_wiring.py`
- `python -m pytest -q tests/unit/test_main_window_controller_facade_injection.py`

Step 6 acceptance note:

- `python -m pytest -q tests/unit -k "main_window"` is not a Step 6 mandatory acceptance command
- that broader subset currently includes unrelated `main_window` lifecycle/import-harness collection paths
- Step 6 is closed against the focused shell-boundary suite above

Recommended manual smoke checks:

- create report entry still opens wizard
- update report entry still opens updater dialog
- convert customer report entry still runs
- edit body content still opens file dialog and editor
- encrypt test files still opens folder flow

## 10. Common Mistakes To Avoid

- do not move feature business logic into `MainWindowFeatureRegistry`
- do not redesign feature controller APIs in this step
- do not turn the registry into a global singleton
- do not couple the registry to Matrix internals beyond existing shell inputs
- do not combine this with Step 2 page-registration redesign

## 11. Practical Conclusion

If you execute this step correctly:

- `MainWindow` becomes more shell-like
- feature construction details move out of shell UI code
- future Step 6+ and Step 7 work becomes easier

If you are unsure during implementation, prefer this rule:

> shell may collect UI input and forward actions, but shell should not build feature internals directly

## 12. Closure Completion Checklist

Step 6 is considered **finished** when:

- [x] `main_window_ui.py` no longer contains old feature-controller construction
- [x] `MainWindowFeatureRegistry` exists and is integrated
- [x] Shell action handlers forward through registry
- [x] `tests/unit/test_main_window_feature_registry_wiring.py` exists with 9 tests
- [x] `tests/unit/test_main_window_controller_facade_injection.py` exists (replaces old test)
- [x] Old `test_main_window_controller_session_manager_injection.py` removed
- [x] Step 6 docs aligned with runtime reality
- [x] Focused Step 6 acceptance suite passes:
  - `test_main_window_ui_session_policy_assembly.py`
  - `test_main_window_feature_registry_wiring.py`
  - `test_main_window_controller_facade_injection.py`

### Files Changed

**Created:**
- `src/features/main_window/service/main_window_feature_registry.py`
- `tests/unit/test_main_window_feature_registry_wiring.py`
- `tests/unit/test_main_window_controller_facade_injection.py`

**Modified:**
- `src/features/main_window/view/main_window_ui.py`

**Deleted:**
- `tests/unit/test_main_window_controller_session_manager_injection.py`
