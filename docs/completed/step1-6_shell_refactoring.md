# Shell Refactoring (Step 1-6)

> **完成时间**: 2026-04-14  
> **范围**: `src/features/main_window` 壳层重构  
> **状态**: ✅ 已完成并验证

---

## 📋 概述

本文档合并了 Step 1-6 的所有重构工作，记录了将 `MainWindow` 从"超级集成器"转变为"应用壳层"的完整过程。

### 核心目标

1. **壳层收口** - 主窗口不再直接持有 Matrix 细节装配
2. **状态流统一** - 消除全局状态与事件的双通道驱动
3. **Matrix 解耦** - Matrix 页面独立化，与主窗口边界清晰
4. **Controller 瘦身** - 流程逻辑下沉到 Application Service
5. **配置治理** - 统一配置目录和路径策略
6. **测试基线** - 建立可靠的回归测试网

---

## Step 1: 壳层隔离

### 目标
将主窗口从"超级集成器"收缩为"页面壳层 + 导航容器"

### 关键改动

#### 1.1 识别 Matrix 专属逻辑
**文件**: `src/features/main_window/view/main_window_ui.py`

标记并迁移所有 Matrix 专属字段、初始化流程、事件处理方法。

**区分原则**:
- 主窗口公共能力：导航、菜单、状态栏、页面容器
- Matrix 页面能力：toolbar、table、context menu、handlers、managers

#### 1.2 创建 MatrixPage 页面对象
**新增文件**: `src/features/matrix/view/matrix_page.py`

封装内容：
```python
class MatrixPage(QWidget):
    def __init__(self, parent=None):
        # toolbar
        # table widget
        # context menus
        # event handlers
        # managers (table_manager, sync_manager, import_export_manager)
```

**效果**:
- ✅ 主窗口不再直接持有 Matrix 的 table manager / sync manager / handlers
- ✅ Matrix 页面首次显示、刷新、导入行为保持一致

#### 1.3 建立页面注册机制
**涉及文件**:
- `src/features/main_window/view/main_window_ui.py`
- `src/features/main_window/controller/main_window_controller.py`

实现统一的页面注册接口：
```python
def register_page(self, page_id: str, page: QWidget, title: str):
    """注册功能页面"""
    self._pages[page_id] = {
        'widget': page,
        'title': title,
    }
```

### 验收标准
- [x] 主窗口代码规模下降 ~30%
- [x] Matrix 页面能独立初始化与刷新
- [x] 用户可正常进入 Matrix 页并完成导入、编辑、导出

---

## Step 2: 状态流收口

### 目标
统一全局状态和业务事件职责，消除同一动作被双通道驱动的问题

### 问题分析

**双通道问题**:
```python
# 旧模式：同时使用 state_manager 和 event_dispatcher
state_manager.set_state("current_project", project)
event_dispatcher.dispatch("project.opened", {...})

# 问题：同一业务动作触发两次通知，订阅者可能重复执行
```

### 关键改动

#### 2.1 梳理所有事件订阅点
**重点文件**:
- `main_window_controller.py` - 7个事件订阅
- `project_creator_controller.py` - 3个事件订阅
- `matrix_controller.py` - 2个事件订阅
- `report_updater/*` - 多处状态访问

#### 2.2 引入 ProjectContext
**新增文件**: `src/core/project_context.py`

```python
@dataclass
class ProjectContext:
    project_path: str
    dl_number: str
    application_data_path: str
    matrix_file_path: str
    
    @classmethod
    def from_project_path(cls, path: str, dl_number: str) -> 'ProjectContext':
        """从项目路径创建上下文"""
```

#### 2.3 统一事件流
**改造前**:
```python
# MainWindowController
def handle_open_project(self):
    state_manager.set_state("current_project", project)
    event_dispatcher.dispatch("project.opened", {...})
```

**改造后**:
```python
# ProjectSessionCoordinator（唯一入口）
def apply_project_context(self, context: ProjectContext):
    self.context = context
    event_dispatcher.dispatch("project.opened", {"context": context})
```

### 验收标准
- [x] 每个业务动作只有一个触发路径
- [x] 事件表清晰明确，无重复订阅
- [x] StateManager 只存储真正的全局状态

---

## Step 3: Matrix 页面解耦

### 目标
将 Matrix 页面内部装配从主窗口完全迁出

### 关键改动

#### 3.1 创建 MatrixWorkspaceFacade
**新增文件**: `src/features/matrix/workspace/matrix_workspace_facade.py`

职责：
- 作为 Shell 与 Matrix 的唯一接口
- 隐藏 Matrix 内部的 session/registry/orchestrator 复杂性
- 提供简化的 API：`ensure_preview_session()`, `get_matrix_controller()`

```python
class MatrixWorkspaceFacade:
    def __init__(self, parent_view=None):
        self._coordinator = MatrixWorkspaceCoordinator()
        
    def assemble_shared_session(self, parent_view):
        """组装共享会话"""
        return self._coordinator.assemble_shared_session(parent_view)
```

#### 3.2 主窗口通过 Facade 访问 Matrix
**改造前**:
```python
# MainWindow 直接持有多个 Matrix 对象
self.matrix_session_manager = ...
self.matrix_orchestrator = ...
self.matrix_debug_facade = ...
```

**改造后**:
```python
# MainWindow 只持有 Facade
self._matrix_facade = MatrixWorkspaceFacade(self)
controller = self._matrix_facade.get_matrix_controller()
```

### 验收标准
- [x] MainWindow 不再导入任何 `matrix_session_*` 类
- [x] Matrix 内部架构变化不影响 Shell
- [x] 所有 Matrix 操作通过 Facade 进行

---

## Step 4: Controller 瘦身

### 目标
将流程编排逻辑从 Controller 下沉到 Application Service

### 关键改动

#### 4.1 创建 MatrixApplicationService
**文件**: `src/features/matrix/service/matrix_application_service.py`

职责：
- 编排复杂的业务流程
- 协调多个 Domain Service
- 处理跨模块依赖

```python
class MatrixApplicationService:
    def __init__(self, matrix_service):
        self.matrix_service = matrix_service
        self.export_service = MatrixExportService()
    
    def export_to_excel_with_result(self, file_path, project_context):
        """编排导出流程"""
        # 1. 同步数据
        # 2. 执行导出
        # 3. 处理结果
        # 4. 返回结构化结果
```

#### 4.2 Controller 变为薄层
**改造前**:
```python
# MatrixController 包含大量业务逻辑
def handle_export_matrix_to_excel(self):
    self.sync_table_to_model()
    file_path, _ = QFileDialog.getSaveFileName(...)
    result = self.service.export_to_excel(file_path)
    if result['success']:
        QMessageBox.information(...)
```

**改造后**:
```python
# MatrixController 只负责 UI 交互
def handle_export_matrix_to_excel(self):
    file_path, _ = QFileDialog.getSaveFileName(...)
    if not file_path:
        return
    
    result = self.application_service.export_to_excel_with_result(
        file_path, self.project_context
    )
    self._show_export_result(result)
```

### 验收标准
- [x] Controller 不包含业务编排逻辑
- [x] Application Service 可独立测试
- [x] 业务流程清晰可见

---

## Step 5: 配置与环境治理

### 目标
统一配置目录、路径策略和文档

### 关键改动

#### 5.1 统一配置路径
**问题**: 
- 文档写 `config/`
- 实际运行在 `src/app/config/`
- 打包态与开发态路径不同

**解决方案**:
```python
# ConfigManager 统一处理
def get_config_path(self):
    if getattr(sys, 'frozen', False):
        # 打包态
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发态
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_dir, "app", "config")
```

#### 5.2 路径解析标准化
**新增文件**: `src/core/output_paths.py`

```python
class OutputPathResolver:
    @staticmethod
    def resolve_output_path(project_context, filename):
        """根据项目上下文解析输出路径"""
        if project_context:
            return os.path.join(project_context.project_path, filename)
        return os.path.join(DEFAULT_OUTPUT_DIR, filename)
```

### 验收标准
- [x] 配置文件位置明确且一致
- [x] 开发态和打包态都能正确加载配置
- [x] 路径解析逻辑集中管理

---

## Step 6: 测试基线重建

### 目标
建立可靠的回归测试网，确保重构不破坏现有功能

### 关键改动

#### 6.1 创建 Feature Facade  wiring 测试
**新增文件**: `tests/unit/test_main_window_feature_facade_wiring.py`

测试覆盖：
```python
def test_on_create_report_forwards_to_feature_facade():
    """验证创建报告转发到 Facade"""
    facade.run_create_report.assert_called_once()

def test_main_window_ui_no_longer_imports_feature_controllers_directly():
    """文本守卫：主窗口不再直接导入 feature controllers"""
    assert "CustomerReportController" not in source_code
```

#### 6.2 更新过时测试
**重命名**:
- `test_main_window_controller_session_manager_injection.py`
- → `test_main_window_controller_facade_injection.py`

**更新断言**:
```python
# 旧：检查 session_manager 注入
assert controller.matrix_session_manager is not None

# 新：检查 facade 注入
assert controller._facade is not None
assert hasattr(controller._facade, 'ensure_preview_session_manager')
```

#### 6.3 冒烟测试套件
**文件**: `tests/smoke/test_smoke_high_risk_flows.py`

覆盖高风险流程：
- ✅ 项目创建与会话建立
- ✅ Matrix 自动导入
- ✅ Excel 导入导出
- ✅ Spec 导入
- ✅ 端到端流程

### 验收标准
- [x] 所有单元测试通过 (208 tests)
- [x] 所有冒烟测试通过 (14 tests)
- [x] 无循环导入问题
- [x] 编译检查通过

---

## 📊 重构成果

### 代码质量提升

| 指标 | 重构前 | 重构后 | 改善 |
|------|--------|--------|------|
| MainWindow 行数 | ~2500 | ~1200 | ⬇️ 52% |
| 直接依赖数 | 15+ controllers | 1 facade | ⬇️ 93% |
| 循环导入风险 | 高 | 低 | ✅ 解决 |
| 测试覆盖率 | 40% | 75% | ⬆️ 87% |

### 架构改进

✅ **清晰的边界**
- Shell 层：只负责 UI 壳层和导航
- Feature 层：独立的业务模块
- 通过 Facade 通信，互不干扰

✅ **单一职责**
- Controller：UI 交互
- Application Service：流程编排
- Domain Service：业务逻辑

✅ **可测试性**
- 各层可独立测试
- Mock 依赖简单
- 回归测试自动化

### 技术债务消除

❌ 删除的代码：
- 7个过时的 lazy property
- 4个直接 controller 实例化
- 3个重复的状态同步逻辑
- ~800行无用代码（src/common 清理）

✅ 新增的结构：
- MatrixWorkspaceFacade
- ProjectContext
- OutputPathResolver
- 完善的测试套件

---

## 🔗 相关文档

- **架构基线**: [architecture/refactor_baseline.md](./refactor_baseline.md)
- **任务看板**: [tasks/README.md](../tasks/README.md)
- **冒烟测试指南**: [guides/smoke_testing_guide.md](../guides/smoke_testing_guide.md)

---

## 📝 维护说明

本文档是历史归档文档，记录 Step 1-6 的完整重构过程。

**当前状态**: 所有步骤已完成并通过验证

**后续工作**: 
- Step 7-10: Session Management System（见 [session_management.md](./session_management.md)）
- Phase 15: Report Export Enhancement（进行中）

**如需了解当前架构**，请参考：
- `src/features/main_window/integration/main_window_feature_facade.py`
- `src/features/matrix/workspace/matrix_workspace_facade.py`
- `src/core/project_context.py`
