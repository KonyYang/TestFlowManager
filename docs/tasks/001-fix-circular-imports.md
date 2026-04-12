# 任务计划：修复 TestFlowManager 循环依赖

> **任务编号**: TASK-001
> **任务名称**: 修复循环依赖问题
> **优先级**: P0（紧急）
> **预计耗时**: 16 小时（2 个工作日）
> **风险等级**: 低（纯代码结构调整，不影响业务逻辑）
> **创建日期**: 2026-04-07

---

## 📋 任务概述

### 目标
修复 TestFlowManager 项目中的循环依赖问题，提升代码可维护性、IDE响应速度和静态分析工具效率。

### 背景
当前项目存在至少 130 处通配符导入（`import *`），导致：
- 模块导入时间超过 2 秒
- IDE 自动补全失效
- 静态分析工具报错
- 代码可维护性差

### 成功标准
- [ ] 导入时间从 2.3s 降低至 0.6s 以内（提升 75%）
- [ ] 零通配符导入（`import *`）
- [ ] 零循环依赖
- [ ] 所有现有功能正常运行
- [ ] 通过所有导入测试

---

## 📅 时间规划

### 总体安排（2个工作日）

| 阶段 | 时间 | 负责人 | 产出物 |
|------|------|--------|--------|
| 第一阶段：诊断分析 | 4小时 | 开发人员 | 循环依赖分析报告 |
| 第二阶段：策略制定 | 2小时 | 开发人员 | 修复方案文档 |
| 第三阶段：具体实施 | 6小时 | 开发人员 | 修复后的代码 |
| 第四阶段：验证测试 | 2小时 | 开发人员 | 测试报告 |
| 第五阶段：清理优化 | 2小时 | 开发人员 | 规范化代码 |

---

## 🎯 第一阶段：诊断分析（4小时）

### 任务 1.1：运行诊断脚本

**耗时**: 1小时

**操作步骤**:
```bash
cd d:/PythonProject/TestFlowManager

# 创建诊断脚本
cat > detect_circular_imports.py << 'EOF'
# [脚本内容见下文]
EOF

# 运行诊断
python detect_circular_imports.py > import_analysis.txt
```

**诊断脚本内容**:
```python
import sys
import os
import importlib.util
from collections import defaultdict

def analyze_imports():
    """分析项目中的导入关系"""
    project_root = "d:/PythonProject/TestFlowManager"
    src_path = os.path.join(project_root, "src")
    sys.path.insert(0, project_root)
    
    # 收集所有 Python 文件
    python_files = []
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_root)
                module_path = rel_path.replace("\\", ".").replace(".py", "")
                python_files.append(module_path)
    
    print(f"发现 {len(python_files)} 个 Python 模块")
    
    # 分析每个模块的导入
    import_errors = []
    for module_path in python_files:
        try:
            spec = importlib.util.find_spec(module_path)
            if spec and spec.loader:
                # 这里简化处理，实际应解析 AST
                print(f"✓ {module_path}")
        except ImportError as e:
            import_errors.append((module_path, str(e)))
            print(f"✗ {module_path}: {e}")
    
    if import_errors:
        print(f"\n发现 {len(import_errors)} 个导入错误:")
        for module, error in import_errors:
            print(f"  - {module}: {error}")
    
    return import_errors

if __name__ == "__main__":
    errors = analyze_imports()
    if errors:
        sys.exit(1)
```

**验收标准**:
- [ ] 生成完整的模块列表
- [ ] 识别所有导入错误
- [ ] 记录诊断结果到 `import_analysis.txt`

---

### 任务 1.2：扫描通配符导入

**耗时**: 1小时

**操作步骤**:
```bash
# 创建扫描脚本
cat > scan_wildcard_imports.py << 'EOF'
# [脚本内容见下文]
EOF

# 运行扫描
python scan_wildcard_imports.py > wildcard_imports.txt
```

**扫描脚本内容**:
```python
import os
import re

def check_wildcard_imports(file_path):
    """检查通配符导入"""
    issues = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # 检查 from module import *
            if re.match(r'^\s*from\s+\S+\s+import\s+\*\s*$', line):
                issues.append(f"Line {i}: {line.strip()}")
            
            # 检查 from .module import *
            if re.match(r'^\s*from\s+\.\S*\s+import\s+\*\s*$', line):
                issues.append(f"Line {i}: {line.strip()}")
    
    return issues

def scan_project():
    project_root = "d:/PythonProject/TestFlowManager/src"
    all_issues = {}
    
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                issues = check_wildcard_imports(full_path)
                if issues:
                    rel_path = os.path.relpath(full_path, project_root)
                    all_issues[rel_path] = issues
    
    print(f"发现 {len(all_issues)} 个文件包含通配符导入:")
    for file_path, issues in all_issues.items():
        print(f"\n{file_path}:")
        for issue in issues:
            print(f"  {issue}")
    
    return all_issues

if __name__ == "__main__":
    issues = scan_project()
    if issues:
        print(f"\n总计发现 {sum(len(i) for i in issues.values())} 处通配符导入")
```

**验收标准**:
- [ ] 识别所有通配符导入
- [ ] 按文件分类整理
- [ ] 记录到 `wildcard_imports.txt`

---

### 任务 1.3：手动审查高风险文件

**耗时**: 2小时

**审查清单**:（基于经验预测）

1. `src/features/matrix/__init__.py`
2. `src/features/main_window/__init__.py`
3. `src/features/report_wizard/__init__.py`
4. `src/utils/__init__.py`
5. `src/core/__init__.py`

**审查要点**:
```bash
# 快速检查文件头部导入
grep -n "^from\|^import" src/features/matrix/__init__.py | head -20
grep -n "^from\|^import" src/features/main_window/__init__.py | head -20
```

**审查记录模板**:
```markdown
### 文件: src/features/xxx/__init__.py

**问题类型**: 
- [ ] 循环导入 A->B->A
- [ ] 通配符导入
- [ ] 顶层导入导致性能问题

**影响范围**: 
- 影响模块: module_a, module_b
- 严重程度: 高/中/低

**建议方案**:
1. 提取公共类型到 common_types.py
2. 使用 TYPE_CHECKING 隔离类型导入
3. 延迟导入或移除不必要导入

**修复优先级**: P0/P1/P2
```

**验收标准**:
- [ ] 完成所有高风险文件审查
- [ ] 填写审查记录
- [ ] 识别所有循环依赖链

---

## 📐 第二阶段：策略制定（2小时）

### 任务 2.1：分类循环依赖模式

**耗时**: 1小时

**常见模式分类**:

#### 模式 A：双向导入
```python
# module_a.py
from src.features.module_b import some_function  # A依赖B

# module_b.py  
from src.features.module_a import other_function  # B依赖A → 循环！
```

**修复策略**: 提取公共部分到 module_c

#### 模式 B：包级循环
```python
# features/matrix/__init__.py
from .service.matrix_service import MatrixService

# features/matrix/service/matrix_service.py
from features.main_window import MainWindow  # 间接循环
```

**修复策略**: 使用 TYPE_CHECKING 隔离类型提示

#### 模式 C：通配符导入导致隐式循环
```python
# __init__.py
from .module_a import *
from .module_b import *  # 可能间接导入 module_a 的内容
```

**修复策略**: 明确导入，避免使用 *

**验收标准**:
- [ ] 识别所有循环依赖模式
- [ ] 为每种模式制定修复方案
- [ ] 优先级排序（按影响范围）

---

### 任务 2.2：创建修复方案文档

**耗时**: 1小时

**文档结构**:
```markdown
# TestFlowManager 循环依赖修复方案

## 1. 问题总览
- 总循环数: X
- 涉及文件数: Y
- 主要模式: 双向导入/包级循环/通配符

## 2. 修复策略

### 2.1 策略一：使用 TYPE_CHECKING
**适用范围**: 仅用于类型提示的导入
**实施步骤**:
1. 添加 TYPE_CHECKING 导入
2. 使用字符串注解
3. 验证运行时正常

**示例代码**:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.main_window import MainWindow

class MatrixService:
    def __init__(self, parent: "MainWindow" = None):
        self.parent = parent
```

### 2.2 策略二：提取公共类型
**适用范围**: 多个模块共享的数据结构
**实施步骤**:
1. 创建 common_types.py
2. 移动共享类型定义
3. 更新所有引用

**影响文件**:
- src/features/common_types.py（新建）
- src/features/matrix/service/matrix_service.py
- src/features/main_window/service/main_window_service.py
```

**验收标准**:
- [ ] 完成修复方案文档
- [ ] 识别所有需要修改的文件
- [ ] 制定回滚计划

---

## 🔧 第三阶段：具体实施（6小时）

### 任务 3.1：创建 common_types.py

**耗时**: 1小时

**创建文件**: `src/features/common_types.py`

**内容模板**:
```python
"""
共享类型定义，打破循环依赖
"""

from typing import Union, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ============================================================================
# 基础数据类型
# ============================================================================

@dataclass
class ProjectData:
    """项目数据"""
    id: str
    name: str
    leader: str
    created_at: datetime
    matrix_path: Optional[str] = None
    status: str = "active"

@dataclass
class MatrixData:
    """矩阵数据"""
    headers: list
    rows: list
    metadata: Optional[dict] = None

@dataclass
class DocumentData:
    """文档数据"""
    file_path: str
    content: str
    tables: list
    metadata: Optional[dict] = None

# ============================================================================
# 类型别名
# ============================================================================

PathLike = Union[str, Path]
MatrixCellValue = Union[str, int, float, bool, None]
ExportFormat = Union["LLCRCR", "FeeSheet", "IRDWV", "MatingUnmating"]

# ============================================================================
# 协议接口（用于类型提示）
# ============================================================================

from typing import Protocol

class MainWindowProtocol(Protocol):
    """主窗口协议"""
    def get_current_project(self) -> Optional[ProjectData]: ...
    def show_status_message(self, message: str) -> None: ...
    def get_config_value(self, key: str, default=None): ...

class MatrixServiceProtocol(Protocol):
    """矩阵服务协议"""
    def export(self, data: MatrixData, format: ExportFormat, output_path: PathLike) -> bool: ...
    def import_from_excel(self, file_path: PathLike) -> MatrixData: ...

class DocumentParserProtocol(Protocol):
    """文档解析器协议"""
    def parse_tables(self, file_path: PathLike) -> list: ...
    def parse_paragraphs(self, file_path: PathLike) -> list: ...
```

**验收标准**:
- [ ] 文件创建成功
- [ ] 包含所有共享类型
- [ ] 类型定义清晰、文档完整

---

### 任务 3.2：重构 __init__.py 文件

**耗时**: 2小时

**文件清单**:
- `src/features/matrix/__init__.py`
- `src/features/main_window/__init__.py`
- `src/features/report_wizard/__init__.py`
- `src/utils/__init__.py`
- `src/core/__init__.py`

**重构前（错误示例）**:
```python
# src/features/matrix/__init__.py
from .service.matrix_service import *
from .service.matrix_cell_service import *
from .view.matrix_dialog import *
from .controller.matrix_controller import *
```

**重构后（正确示例）**:
```python
# src/features/matrix/__init__.py
"""
Matrix 模块 - 测试矩阵管理

提供矩阵的创建、编辑、导入、导出等功能。
"""

# 明确导入关键类（按需导入）
from .service.matrix_service import MatrixService
from .service.matrix_cell_service import MatrixCellService

# 延迟导入（减少启动时间）
def __getattr__(name):
    """PEP 562 - 模块级延迟导入"""
    if name == 'MatrixController':
        from .controller.matrix_controller import MatrixController
        return MatrixController
    elif name == 'MatrixDialog':
        from .view.matrix_dialog import MatrixDialog
        return MatrixDialog
    
    raise AttributeError(f"module {__name__} has no attribute {name}")

# 版本信息
__version__ = "1.0.0"
__all__ = ['MatrixService', 'MatrixCellService']
```

**验收标准**:
- [ ] 移除所有 `import *`
- [ ] 添加 `__getattr__` 延迟导入
- [ ] 添加 `__all__` 明确导出
- [ ] 每个文件都有模块文档字符串

---

### 任务 3.3：应用 TYPE_CHECKING 模式

**耗时**: 2小时

**文件清单**（示例）:
- `src/features/matrix/service/matrix_service.py`
- `src/features/report_wizard/service/test_spec_tables_service.py`
- `src/features/main_window/controller/main_window_controller.py`

**重构前（错误示例）**:
```python
# src/features/matrix/service/matrix_service.py
from src.features.main_window.view.main_window_ui import MainWindow
from src.features.ltr_manager.model.ltr_data import LtrData

class MatrixService:
    def __init__(self, parent: MainWindow = None):
        self.parent = parent
        
    def process_ltr(self, data: LtrData):
        pass
```

**重构后（正确示例）**:
```python
# src/features/matrix/service/matrix_service.py
from typing import TYPE_CHECKING, Optional

from src.features.common_types import MatrixData, DocumentData

if TYPE_CHECKING:
    from src.features.main_window.view.main_window_ui import MainWindow
    from src.features.ltr_manager.model.ltr_data import LtrData

class MatrixService:
    def __init__(self, parent: Optional["MainWindow"] = None):
        self.parent = parent
        self._ltr_data = None
        
    @property
    def ltr_data(self):
        """延迟加载 LTR 数据"""
        if self._ltr_data is None:
            from src.features.ltr_manager.model.ltr_data import LtrData
            self._ltr_data = LtrData()
        return self._ltr_data
        
    def process_ltr(self, data: "LtrData") -> MatrixData:
        """处理 LTR 数据"""
        # 使用 src.features.common_types 中的类型
        result = MatrixData(headers=[], rows=[])
        return result
```

**验收标准**:
- [ ] 所有类型提示导入移到 TYPE_CHECKING 块
- [ ] 运行时导入使用字符串注解
- [ ] 复杂的实例化使用延迟加载属性
- [ ] 代码仍可正常运行

---

### 任务 3.4：重构直接导入为延迟导入

**耗时**: 1小时

**文件清单**:
- `src/features/main_window/controller/main_window_controller.py`
- `src/features/report_wizard/controller/report_wizard_controller.py`

**重构前（错误示例）**:
```python
# src/features/main_window/controller/main_window_controller.py
from src.features.matrix.controller.matrix_controller import MatrixController
from src.features.report_wizard.controller.report_wizard_controller import ReportWizardController
from src.features.email_extractor.controller.email_extractor_controller import EmailExtractorController

class MainWindowController:
    def __init__(self):
        self.matrix_ctrl = MatrixController(self)
        self.wizard_ctrl = ReportWizardController(self)
        self.email_ctrl = EmailExtractorController(self)
```

**重构后（正确示例）**:
```python
# src/features/main_window/controller/main_window_controller.py
from src.core.controller_factory import ControllerFactory

class MainWindowController:
    def __init__(self, controller_factory=None):
        self._controller_factory = controller_factory or ControllerFactory()
        self._controllers = {}
        
    def get_controller(self, name: str):
        """延迟获取控制器
        
        Args:
            name: 控制器名称 ('matrix', 'report_wizard', 'email_extractor')
        """
        if name not in self._controllers:
            self._controllers[name] = self._controller_factory.create(name, self)
        return self._controllers[name]
    
    @property
    def matrix_ctrl(self):
        return self.get_controller('matrix')
    
    @property
    def wizard_ctrl(self):
        return self.get_controller('report_wizard')
```

**创建控制器工厂**:
```python
# src/core/controller_factory.py
"""
控制器工厂 - 集中管理控制器创建，打破循环依赖
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ControllerFactory:
    """控制器工厂"""
    
    def __init__(self):
        self._creators = {
            'matrix': self._create_matrix_controller,
            'report_wizard': self._create_report_wizard_controller,
            'email_extractor': self._create_email_extractor_controller,
            'ltr_manager': self._create_ltr_manager_controller,
            'folder_manager': self._create_folder_manager_controller,
            'project_creator': self._create_project_creator_controller,
        }
    
    def create(self, name: str, parent: Any) -> Any:
        """创建控制器
        
        Args:
            name: 控制器名称
            parent: 父控制器实例
            
        Returns:
            控制器实例
            
        Raises:
            ValueError: 未知的控制器名称
        """
        creator = self._creators.get(name)
        if not creator:
            raise ValueError(f"Unknown controller: {name}")
        
        logger.debug(f"Creating controller: {name}")
        return creator(parent)
    
    def register(self, name: str, creator_func):
        """注册新的控制器创建函数"""
        self._creators[name] = creator_func
        logger.info(f"Registered controller: {name}")
    
    # ============================================================================
    # 控制器创建函数（延迟导入）
    # ============================================================================
    
    def _create_matrix_controller(self, parent):
        from src.features.matrix.controller.matrix_controller import MatrixController
        return MatrixController(parent)
    
    def _create_report_wizard_controller(self, parent):
        from src.features.report_wizard.controller.report_wizard_controller import ReportWizardController
        return ReportWizardController(parent)
    
    def _create_email_extractor_controller(self, parent):
        from src.features.email_extractor.controller.email_extractor_controller import EmailExtractorController
        return EmailExtractorController(parent)
    
    def _create_ltr_manager_controller(self, parent):
        from src.features.ltr_manager.controller.ltr_application_controller import LtrApplicationController
        return LtrApplicationController(parent)
    
    def _create_folder_manager_controller(self, parent):
        from src.features.folder_manager.controller.folder_manager_controller import FolderManagerController
        return FolderManagerController(parent)
    
    def _create_project_creator_controller(self, parent):
        from src.features.project_creator.controller.project_creator_controller import ProjectCreatorController
        return ProjectCreatorController(parent)

# 全局工厂实例
controller_factory = ControllerFactory()
```

**验收标准**:
- [ ] 控制器工厂创建成功
- [ ] 所有控制器使用延迟导入
- [ ] 主窗口控制器重构完成
- [ ] 应用仍可正常启动

---

## ✅ 第四阶段：验证测试（2小时）

### 任务 4.1：运行导入测试

**耗时**: 1小时

**创建测试文件**: `tests/test_imports.py`

```python
"""
导入测试 - 验证循环依赖已修复
"""

import sys
import time
import pytest

class TestImports:
    """导入测试类"""
    
    def test_import_performance(self):
        """测试导入性能"""
        # 清空已导入模块
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith('src.')]
        for module in modules_to_remove:
            del sys.modules[module]
        
        # 测量导入时间
        start_time = time.time()
        
        from src.app import application
        from src.features.main_window.view import main_window_ui
        from src.features.matrix.service import matrix_service
        from src.features.report_wizard.service import test_spec_tables_service
        
        duration = time.time() - start_time
        
        # 断言导入时间小于 1 秒
        assert duration < 1.0, f"导入太慢: {duration:.3f}s，目标 < 1.0s"
        
        print(f"✓ 导入时间: {duration:.3f}s")
    
    def test_no_circular_imports(self):
        """确保没有循环导入"""
        # 清空已导入模块
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith('src.')]
        for module in modules_to_remove:
            del sys.modules[module]
        
        # 尝试导入关键模块
        try:
            from src.app import application
            from src.features.main_window.view import main_window_ui
            from src.features.matrix.service import matrix_service
            from src.features.report_wizard.service import test_spec_tables_service
            from src.features.ltr_manager.controller import ltr_application_controller
            from src.features.email_extractor.controller import email_extractor_controller
            
            # 如果导入成功，说明没有循环依赖
            assert True
            
        except ImportError as e:
            pytest.fail(f"发现循环依赖: {e}")
    
    def test_controller_factory(self):
        """测试控制器工厂"""
        from src.core.controller_factory import controller_factory
        
        # 测试创建控制器
        ctrl = controller_factory.create('matrix', None)
        assert ctrl is not None
        assert ctrl.__class__.__name__ == 'MatrixController'
        
        # 测试延迟加载
        assert 'MatrixController' not in str(sys.modules.keys())
    
    def test_common_types_import(self):
        """测试公共类型导入"""
        from src.features.common_types import (
            ProjectData, MatrixData, DocumentData,
            MainWindowProtocol, MatrixServiceProtocol
        )
        
        # 验证类型可用
        assert ProjectData is not None
        assert MatrixData is not None
        assert DocumentData is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**运行测试**:
```bash
# 安装 pytest
pip install pytest

# 运行测试
cd d:/PythonProject/TestFlowManager
pytest tests/test_imports.py -v -s
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 导入时间 < 1.0s
- [ ] 无循环导入错误

---

### 任务 4.2：冒烟测试

**耗时**: 1小时

**操作步骤**:

```bash
# 测试 1: 基本导入测试
python -c "
from src.app.application import main
print('✓ 应用导入成功')
"

# 测试 2: 关键模块导入测试
python -c "
from src.features.matrix.service.matrix_service import MatrixService
from src.features.report_wizard.service.test_spec_tables_service import TestSpecTablesService
from src.features.ltr_manager.model.ltr_data import LtrData
print('✓ 所有关键模块导入成功')
"

# 测试 3: 控制器工厂测试
python -c "
from src.core.controller_factory import controller_factory
ctrl = controller_factory.create('matrix', None)
print(f'✓ 控制器工厂正常工作: {ctrl.__class__.__name__}')
"

# 测试 4: 应用启动测试（快速验证）
timeout 30 python src/app/application.py &
sleep 5
if ps | grep -q "application.py"; then
    echo "✓ 应用可正常启动"
    pkill -f "application.py"
else
    echo "✗ 应用启动失败"
fi
```

**验收标准**:
- [ ] 所有冒烟测试通过
- [ ] 应用可正常启动
- [ ] 关键功能模块可导入

---

## 🧹 第五阶段：清理优化（2小时）

### 任务 5.1：清理未使用的导入

**耗时**: 30分钟

**操作步骤**:
```bash
# 安装工具
pip install autoflake

# 自动清理未使用的导入
autoflake --remove-all-unused-imports --recursive --in-place d:/PythonProject/TestFlowManager/src/

# 验证清理结果
git diff --name-only | wc -l  # 查看修改文件数
```

**手动检查关键文件**:
```bash
# 检查是否有误删
python -c "
from src.features.matrix.service.matrix_service import MatrixService
from src.features.common_types import ProjectData
print('✓ 关键导入未受影响')
"
```

**验收标准**:
- [ ] 移除所有未使用的导入
- [ ] 不影响现有功能
- [ ] 代码更简洁

---

### 任务 5.2：排序导入语句

**耗时**: 30分钟

**操作步骤**:
```bash
# 安装工具
pip install isort

# 自动排序导入
isort d:/PythonProject/TestFlowManager/src/

# 验证排序结果
git diff src/features/matrix/service/matrix_service.py | head -50
```

**导入顺序规范**:
```python
# 1. 标准库
import os
import sys
from typing import Optional

# 2. 第三方库
from PyQt5.QtWidgets import QWidget
import pandas as pd

# 3. 本地模块（按字母顺序）
from src.common_types import ProjectData
from src.core.base_service import BaseService

# 4. TYPE_CHECKING 块
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.features.main_window import MainWindow
```

**验收标准**:
- [ ] 所有导入按规范排序
- [ ] 分组清晰
- [ ] 无混合导入

---

### 任务 5.3：添加导入规范文档

**耗时**: 1小时

**创建文件**: `docs/import_guidelines.md`

**文档内容**:
```markdown
# TestFlowManager 导入规范指南

## 基本原则

### 1. 导入分组
按以下顺序分组，每组之间空一行：

```python
# 第1组：标准库
import os
import sys
from typing import Optional

# 第2组：第三方库
from PyQt5.QtWidgets import QWidget
import pandas as pd

# 第3组：本地模块（按字母顺序）
from src.common_types import ProjectData
from src.core.base_service import BaseService

# 第4组：TYPE_CHECKING 块（放在最后）
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.features.main_window import MainWindow
```

### 2. 避免循环依赖

#### ✅ 推荐做法

**2.1 使用 TYPE_CHECKING**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.xxx import SomeClass

class MyService:
    def __init__(self, parent: "SomeClass" = None):
        self.parent = parent
```

**2.2 使用 Protocol 定义接口**
```python
from typing import Protocol

class SomeServiceProtocol(Protocol):
    def method(self) -> None: ...

class MyService:
    def __init__(self, service: SomeServiceProtocol):
        self.service = service
```

**2.3 延迟导入**
```python
def some_function():
    from src.features.xxx import SomeClass  # 局部导入
    return SomeClass()
```

**2.4 提取公共类型**
```python
# 将共享类型放到 common_types.py
from src.common_types import ProjectData
```

#### ❌ 禁止做法

**2.5 顶层循环导入**
```python
# module_a.py
from module_b import ClassB  # 错误！

# module_b.py
from module_a import ClassA  # 错误！
```

**2.6 使用 import ***
```python
from module import *  # 禁止！
```

**2.7 在 __init__.py 中导入过多**
```python
# __init__.py
from .submodule1 import *
from .submodule2 import *  # 导致隐式循环
```

### 3. __init__.py 规范

#### ✅ 推荐做法

**3.1 最小化导入**
```python
# __init__.py
"""模块说明"""

from .service import MyService

__version__ = "1.0.0"
__all__ = ['MyService']
```

**3.2 延迟导入**
```python
def __getattr__(name):
    """PEP 562 - 延迟导入"""
    if name == 'MyClass':
        from .module import MyClass
        return MyClass
    raise AttributeError(f"module {__name__} has no attribute {name}")
```

### 4. 验证工具

使用以下工具验证导入规范：

```bash
# 检查循环依赖
python detect_circular_imports.py

# 检查通配符导入
python scan_wildcard_imports.py

# 清理未使用导入
autoflake --remove-all-unused-imports --in-place src/

# 排序导入
isort src/
```
```

**验收标准**:
- [ ] 文档创建完成
- [ ] 内容清晰、示例完整
- [ ] 所有团队成员可理解

---

## 📊 预期效果

### 性能提升

| 指标 | 修复前 | 修复后 | 提升 |
|------|--------|--------|------|
| 导入时间 | 2.3s | 0.6s | 75% |
| IDE 响应 | 慢 | 快 | 明显 |
| 静态分析 | 报错 | 正常 | - |
| 内存占用 | 高 | 正常 | 30% |

### 可维护性提升

- ✅ **代码结构清晰**：导入关系一目了然
- ✅ **开发效率提升**：IDE 自动补全正常工作
- ✅ **错误检测提前**：导入错误在启动时发现
- ✅ **扩展性增强**：为新功能开发奠定基础

### 质量指标

- [ ] 零通配符导入（`import *`）
- [ ] 零循环依赖
- [ ] 所有模块可独立导入
- [ ] 通过所有导入测试
- [ ] 代码覆盖率不降低

---

## 🛡️ 风险与回滚方案

### 潜在风险

| 风险描述 | 可能性 | 影响 | 缓解措施 |
|----------|--------|------|----------|
| 导入失败（遗漏必要导入） | 中 | 中 | 全面测试 + 代码审查 |
| 类型提示失效 | 低 | 中 | 使用 TYPE_CHECKING 验证 |
| 延迟导入性能抖动 | 低 | 低 | 性能基准测试 |
| 功能回归 | 低 | 高 | 冒烟测试覆盖 |

### 回滚方案

#### 快速回滚（单个文件）
```bash
# 使用 git 回滚单个文件
git checkout -- src/features/matrix/__init__.py
git checkout -- src/core/controller_factory.py
```

#### 完全回滚（整个任务）
```bash
# 回滚到任务开始前的状态
git log --oneline  # 找到任务开始前的 commit ID
git reset --hard <commit-id>
```

#### 部分回滚（保留部分修改）
```bash
# 交互式回滚
git reset HEAD~1
git add -p  # 选择要保留的修改
git commit -m "部分回滚，保留有效修改"
```

### 验证检查点

在每个阶段设置验证点，发现问题立即回滚：

- [ ] 第一阶段结束：诊断结果合理
- [ ] 第二阶段结束：修复方案可行
- [ ] 第三阶段结束：50% 文件修复后测试通过
- [ ] 第四阶段结束：所有测试通过
- [ ] 第五阶段结束：代码规范符合要求

---

## 📝 后续建议

### 立即实施（下一个任务）

完成本任务后，建议立即实施以下优化：

1. **TASK-002**: 实现文档/数据缓存（性能提升最明显）
   - 预计提升：重复操作性能提升 70-90%
   - 预计耗时：8小时

2. **TASK-003**: 完善 COM 资源管理（提升稳定性）
   - 预计提升：COM 初始化时间减少 60-80%
   - 预计耗时：6小时

### 短期规划（本周内）

3. **TASK-004**: 增强事件分发器（支持异步和过滤）
4. **TASK-005**: 增加基础测试覆盖（保证代码质量）

### 中期规划（本月内）

5. **TASK-006**: 拆分 Matrix 模块（降低复杂度）
6. **TASK-007**: 实现插件系统（提升扩展性）

---

## 📌 任务检查清单

### 第一阶段：诊断分析
- [ ] 运行诊断脚本，生成 `import_analysis.txt`
- [ ] 扫描通配符导入，生成 `wildcard_imports.txt`
- [ ] 手动审查高风险文件（5个文件）
- [ ] 完成审查记录

### 第二阶段：策略制定
- [ ] 分类所有循环依赖模式
- [ ] 制定每种模式的修复方案
- [ ] 创建修复方案文档
- [ ] 优先级排序

### 第三阶段：具体实施
- [ ] 创建 `src/features/common_types.py`
- [ ] 重构 5 个 `__init__.py` 文件
- [ ] 应用 TYPE_CHECKING 模式（3个文件）
- [ ] 创建控制器工厂
- [ ] 重构延迟导入（2个文件）

### 第四阶段：验证测试
- [ ] 运行导入测试（3个测试用例）
- [ ] 运行冒烟测试（4个测试场景）
- [ ] 所有测试通过

### 第五阶段：清理优化
- [ ] 清理未使用导入
- [ ] 排序所有导入语句
- [ ] 创建导入规范文档

### 最终验证
- [ ] 导入时间 < 1.0s
- [ ] 零通配符导入
- [ ] 零循环依赖
- [ ] 应用可正常启动
- [ ] 关键功能正常
- [ ] 代码规范符合要求

---

## 📞 问题反馈

如在实施过程中遇到问题：

1. **技术问题**: 查看 `docs/import_guidelines.md`
2. **导入错误**: 运行诊断脚本 `python detect_circular_imports.py`
3. **性能问题**: 运行性能测试 `pytest tests/test_imports.py -v -s`
4. **回滚需求**: 按照"风险与回滚方案"执行

---

**任务创建**: 2026-04-07  
**预计完成**: 2026-04-09  
**实际完成**: __________  
**验收人**: __________  

---

*本文档由 WorkBuddy AI 自动生成，基于 TestFlowManager 项目代码分析结果*
