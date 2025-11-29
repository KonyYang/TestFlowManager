# TestFlow Manager 开发指南

## 架构概述

TestFlow Manager 采用 MVCS 架构模式（Model-View-Controller-Service），每个功能模块都遵循此模式进行设计和实现。

### 架构层次说明

1. **Model（模型层）**
   - 负责数据结构定义和数据管理
   - 不包含业务逻辑，仅提供数据访问接口
   - 通常以数据类或简单对象的形式存在

2. **View（视图层）**
   - 负责用户界面展示和用户交互
   - 使用 PyQt5 构建图形用户界面
   - 不包含业务逻辑，仅处理界面展示和用户输入

3. **Controller（控制层）**
   - 负责业务逻辑处理和流程控制
   - 协调 Model 和 View 之间的交互
   - 调用 Service 层处理具体业务操作

4. **Service（服务层）**
   - 负责具体的业务操作实现
   - 提供可重用的业务功能
   - 处理数据持久化、外部接口调用等

## 项目结构

```
src/
├── app/                 # 应用程序入口
├── core/                # 核心组件
├── managers/            # 管理器
├── common/              # 公共组件
│   ├── widgets/         # 自定义控件
│   ├── services/        # 公共服务
│   └── exceptions/      # 自定义异常
├── utils/               # 工具类
└── features/            # 功能模块
    ├── email_extractor/  # 邮件提取模块
    ├── project_creator/ # 项目创建模块
    ├── ltr_manager/     # LTR管理模块
    ├── folder_manager/  # 文件夹管理模块
    └── document_parser/ # 文档解析模块
```

## 核心组件

### 事件分发器 (EventDispatcher)
用于模块间解耦通信，采用发布-订阅模式。

### 日志管理器 (Logger)
统一的日志记录和管理机制。

### 状态管理器 (StateManager)
管理应用程序的全局状态。

### 配置管理器 (ConfigManager)
处理应用程序配置的加载和保存。

### 基础服务类 (BaseService)
所有服务类的基类，提供通用功能。

## 开发规范

### 命名规范
- 类名采用大驼峰命名法（CamelCase）
- 方法和变量采用小驼峰命名法（camelCase）
- 常量采用大写字母加下划线命名法（UPPER_CASE）
- 私有成员以下划线开头（_private_member）

### 注释规范
- 类和方法必须有文档字符串（docstring）
- 复杂逻辑需要添加行内注释
- 使用中文注释，关键接口可添加英文注释

### 异常处理
- 优先使用自定义异常类
- 记录异常日志以便调试
- 向用户显示友好的错误信息

## 异常处理体系

### 异常分类
TestFlow Manager 中的异常主要分为以下几类：

1. **验证异常 (Validation Errors)**
   - 数据验证失败时抛出
   - 包括必填字段缺失、格式错误等

2. **处理异常 (Processing Errors)**
   - 数据处理过程中发生的一般性错误
   - 包括文件操作、网络请求等

3. **配置异常 (Configuration Errors)**
   - 配置加载或验证失败时抛出

4. **系统异常 (System Errors)**
   - 系统级错误，如内存不足、权限不足等

### 自定义异常类
项目中定义了以下自定义异常类：

- `ValidationError`: 基础验证异常
- `RequiredFieldError`: 必填字段异常
- `FormatValidationError`: 格式验证异常
- `ProcessingError`: 基础处理异常
- `FileOperationError`: 文件操作异常
- `ConfigurationError`: 配置异常

### 异常处理最佳实践

1. **明确异常类型**
   - 根据错误性质选择合适的异常类型
   - 避免全部使用通用的 Exception

2. **分层处理异常**
   - Service 层抛出具体异常
   - Controller 层捕获并转换为用户友好的错误信息
   - View 层仅处理界面相关的异常

3. **记录详细日志**
   - 使用 logger 记录异常详情
   - 包含上下文信息和堆栈跟踪

4. **用户友好提示**
   - 向用户显示简洁明了的错误信息
   - 避免暴露系统内部细节

### 异常处理工具
项目提供统一的异常处理工具：

- `handle_exception()`: 统一异常处理函数
- `safe_execute()`: 安全执行函数
- `show_warning()`: 显示警告消息
- `show_info()`: 显示信息消息

使用示例：
```python
from src.utils.exception_handler import safe_execute, handle_exception

# 安全执行函数
result = safe_execute(some_function, arg1, arg2, context="执行某项操作")

# 手动处理异常
try:
    some_operation()
except Exception as e:
    error_info = handle_exception(e, "执行操作时发生错误", parent_view)
```

## 服务层设计规范

### 服务层架构
所有服务类都应该继承 [BaseService](file:///D:/PythonProject/TestFlowManager/src/core/base_service.py#L8-L108) 基类，该基类提供了以下通用功能：

1. **统一的日志记录机制**
   - `log_info()`: 记录信息日志
   - `log_debug()`: 记录调试日志
   - `log_warning()`: 记录警告日志
   - `log_error()`: 记录错误日志

2. **标准的异常处理方法**
   - `handle_processing_error()`: 处理操作错误
   - `handle_configuration_error()`: 处理配置错误
   - `handle_file_operation_error()`: 处理文件操作错误

3. **配置访问功能**
   - `get_config_value()`: 通用配置获取方法（对 ConfigManager.get 的封装）
   - `get_path_config()`: 专门用于获取路径配置的方法
   - `get_default_value()`: 专门用于获取默认值配置的方法

4. **服务标识**
   - 每个服务都有唯一的名称标识，便于日志追踪

### 服务层实现要求

1. **继承 BaseService**
   所有服务类必须继承 [BaseService](file:///D:/PythonProject/TestFlowManager/src/core/base_service.py#L8-L108) 并调用 `super().__init__("ServiceName")`

2. **实现 initialize 方法**
   每个服务类必须实现 `initialize()` 方法用于初始化服务

3. **使用统一日志方法**
   服务内应使用 `self.log_info()` 等方法记录日志，而非直接使用 logger

4. **规范异常处理**
   服务方法应抛出具体的自定义异常，而非通用 Exception

5. **使用通用配置访问方法**
   服务内应使用 `self.get_config_value()` 等方法访问配置，而不是直接调用 `config_manager.get()`

### 服务层示例

```python
from src.core.base_service import BaseService
from src.common.exceptions.validation_error import ProcessingError

class ExampleService(BaseService):
    def __init__(self):
        super().__init__("ExampleService")
        
    def initialize(self) -> bool:
        self.log_info("示例服务初始化完成")
        return True
        
    def do_something(self, data):
        try:
            # 获取路径配置
            template_dir = self.get_path_config("template_dir", "/default/template/path")
            
            # 获取默认值配置
            project_leader = self.get_default_value("project_leader", "Unknown")
            
            # 业务逻辑
            result = process_data(data)
            self.log_info("数据处理完成")
            return result
        except Exception as e:
            raise self.handle_processing_error(f"数据处理失败: {str(e)}", "do_something")
```

## 模块开发指导

### 创建新功能模块
1. 在 `src/features/` 目录下创建模块文件夹
2. 按照 MVCS 模式创建相应的子目录和文件
3. 实现业务逻辑并编写单元测试
4. 在主应用中集成新模块

### 扩展现有功能
1. 分析现有代码结构和依赖关系
2. 确保新增功能与现有架构保持一致
3. 遵循开闭原则，尽量通过扩展而非修改实现功能增强

## 测试策略

### 单元测试
- 针对每个独立功能编写单元测试
- 使用 pytest 作为测试框架
- 测试覆盖率应达到 80% 以上

### 集成测试
- 测试模块间的交互和集成
- 验证完整的业务流程
- 模拟真实使用场景

## 代码质量保证

### 代码审查
- 所有代码提交前需经过审查
- 关注代码可读性和可维护性
- 确保遵循开发规范

### 持续集成
- 自动化构建和测试
- 及时发现和修复问题
- 保证代码质量稳定

## 常见问题和解决方案

### 依赖管理
- 使用 requirements.txt 管理依赖
- 区分运行时依赖和开发依赖
- 定期更新依赖版本

### 性能优化
- 避免不必要的重复计算
- 合理使用缓存机制
- 优化数据库查询和文件操作

### 跨平台兼容性
- 使用标准库和跨平台第三方库
- 避免使用平台特定的API
- 在不同平台上进行测试验证