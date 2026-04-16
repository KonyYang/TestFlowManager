# Dialog 模块迁移计划

## 背景

`src/shell/main_window/view/dialogs/` 中的对话框存在以下问题：
1. 违反架构边界：业务对话框放在 Shell 层
2. 重复文件：`basic_info_dialog.py` 与 `project_info_dialog.py` 内容相同
3. 命名不准确：无法体现业务语义

## 迁移任务

### T1: DLInputDialog 迁移到 ltr_manager

**源**: `src/shell/main_window/view/dialogs/dl_input_dialog.py`
**目标**: `src/features/ltr_manager/view/ltr_number_input_dialog.py`
**新类名**: `LTRNumberInputDialog`

**使用方**:
- `src/features/ltr_manager/facade/ltr_facade.py`

### T2: DialogBase 迁移到 ltr_manager

**源**: `src/shell/main_window/view/dialogs/base.py`
**目标**: `src/features/ltr_manager/view/ltr_form_dialog_base.py`
**新类名**: `LTRFormDialogBase`

**依赖**:
- `LTRFieldConfigLoader` (ltr_manager.utils)
- `EnglishDateEdit` (ltr_manager.widgets)

### T3: BasicInfoDialog 迁移到 project_creator

**源**: `src/shell/main_window/view/dialogs/basic_info_dialog.py`
**目标**: `src/features/project_creator/view/project_info_dialog.py`
**新类名**: `ProjectInfoDialog`

**使用方**:
- `src/shell/main_window/coordinator/project_lifecycle_coordinator.py`
- `src/features/matrix/view/handlers/matrix_event_handlers.py`

### T4: 删除重复文件

**删除**: `src/shell/main_window/view/dialogs/project_info_dialog.py`

### T5: 更新导入路径

需要更新以下文件的导入语句：

1. `src/features/ltr_manager/facade/ltr_facade.py`
2. `src/shell/main_window/coordinator/project_lifecycle_coordinator.py`
3. `src/features/matrix/view/handlers/matrix_event_handlers.py`
4. `src/shell/main_window/view/__init__.py`
5. `src/shell/main_window/view/dialogs/__init__.py`
6. `src/features/ltr_manager/view/__init__.py`
7. `src/features/project_creator/view/__init__.py`

## 执行步骤

```bash
# 1. 创建 ltr_manager/view 目录结构
mkdir -p src/features/ltr_manager/view

# 2. 复制并重命名文件
cp src/shell/main_window/view/dialogs/dl_input_dialog.py \
   src/features/ltr_manager/view/ltr_number_input_dialog.py

cp src/shell/main_window/view/dialogs/base.py \
   src/features/ltr_manager/view/ltr_form_dialog_base.py

cp src/shell/main_window/view/dialogs/basic_info_dialog.py \
   src/features/project_creator/view/project_info_dialog.py

# 3. 更新类名和导入路径
# (见具体文件修改)

# 4. 删除原文件和重复文件
rm src/shell/main_window/view/dialogs/dl_input_dialog.py
rm src/shell/main_window/view/dialogs/base.py
rm src/shell/main_window/view/dialogs/basic_info_dialog.py
rm src/shell/main_window/view/dialogs/project_info_dialog.py

# 5. 验证
pytest tests/ -v
```

## 验证清单

- [ ] py_compile 所有相关文件
- [ ] 相关单元测试通过
- [ ] 导入语句无遗漏
- [ ] Shell 层无业务对话框残留
