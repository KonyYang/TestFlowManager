# TestFlow Manager

TestFlow Manager 是一个用于管理测试流程的工具，专注于处理测试申请单、邮件通信和相关文档管理。

## 项目结构

本项目采用MVCS架构模式（Model-View-Controller-Service）：

- **Model**: 数据模型层
- **View**: 视图层，负责界面展示
- **Controller**: 控制层，处理业务逻辑
- **Service**: 服务层，处理具体业务操作

### 目录说明

- `src/`: 源代码目录
  - `app/`: 应用程序入口
  - `core/`: 核心组件（事件分发器、日志、状态管理等）
  - `managers/`: 各种管理器
  - `common/`: 公共组件
    - `widgets/`: 自定义控件
    - `services/`: 公共服务
    - `exceptions/`: 自定义异常
  - `utils/`: 工具类
  - `features/`: 功能模块
- `tests/`: 测试代码
- `docs/`: 文档
- `config/`: 配置文件
