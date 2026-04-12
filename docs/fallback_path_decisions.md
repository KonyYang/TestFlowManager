# TestFlowManager 硬编码兜底路径去留决策清单

> 更新时间：2026-04-09  
> 目的：明确当前剩余代码级硬编码兜底路径哪些保留、哪些已集中、哪些后续可继续下沉。

---

## 1. 当前决策原则

剩余硬编码兜底路径按三类处理：

- 保留
  - 仅作为代码兜底
  - 已有统一入口

- 已集中
  - 仍是代码兜底，但不再散落在各业务模块

- 后续候选
  - 需要进一步决定是否迁回配置、改为资源解析、或继续保留

---

## 2. 已集中且当前保留

### 2.1 `D:\OutFile`

- 统一入口：
  - [output_paths.py](D:/PythonProject/TestFlowManager/src/core/output_paths.py)
- 当前角色：
  - 无项目态或目录解析失败时的全局兜底输出目录
- 决策：
  - 当前保留
  - 不再允许主线项目态流程优先落到该目录

### 2.2 `D:\TestFlowManager\Template`

- 统一入口：
  - [config_manager.py](D:/PythonProject/TestFlowManager/src/core/config_manager.py)
  - `config_manager.get_template_dir()`
- 当前角色：
  - `paths.template_dir` 的代码兜底默认值
- 当前已接入：
  - [report_generation_service.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/service/report_generation_service.py)
  - [fee_sheet_export_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/export/service/fee_sheet_export_service.py)
  - [document_parser_service.py](D:/PythonProject/TestFlowManager/src/features/document_parser/service/document_parser_service.py)
  - [folder_manager_service.py](D:/PythonProject/TestFlowManager/src/features/folder_manager/service/folder_manager_service.py)
- 决策：
  - 当前保留为部署变量兜底

### 2.3 `D:\TestFlowManager\Projects`

- 统一入口：
  - `config_manager.get_default_project_dir()`
- 当前角色：
  - `paths.default_project_path` 的代码兜底默认值
- 当前已接入：
  - [folder_manager_service.py](D:/PythonProject/TestFlowManager/src/features/folder_manager/service/folder_manager_service.py)
- 决策：
  - 当前保留为部署变量兜底

### 2.4 `D:\TestFlowManager\Backup`

- 统一入口：
  - `config_manager.get_backup_dir()`
- 当前角色：
  - `paths.backup_path` 的代码兜底默认值
- 当前已接入：
  - [folder_manager_service.py](D:/PythonProject/TestFlowManager/src/features/folder_manager/service/folder_manager_service.py)
- 决策：
  - 当前保留为部署变量兜底

### 2.5 `D:\TestFlowManager\Temp`

- 统一入口：
  - `config_manager.get_temp_dir()`
- 当前角色：
  - `paths.temp_dir` 的代码兜底默认值
- 当前已接入：
  - [email_extractor_service.py](D:/PythonProject/TestFlowManager/src/features/email_extractor/service/email_extractor_service.py)
- 决策：
  - 当前保留为部署变量兜底

---

## 3. 后续候选

### 3.1 `D:\Source\...`

- 当前形态：
  - 主要出现在配置默认值或配置文件中
- 涉及：
  - `ltr_file`
  - `standard_version_info_file`
  - `equipment_data_sources.excel_file_path`
- 决策：
  - 暂不处理
  - 这些更像真实部署变量，不适合直接移到应用资源

### 3.2 `logging.file`

- 当前位置：
  - `settings.json`
- 当前形态：
  - 相对路径 `logs/testflow.log`
- 决策：
  - 保留在应用运行时配置
  - 不迁入 `paths.ini`

### 3.3 业务模块里剩余的默认参数字面量

- 当前形态：
  - 少量业务方法调用 `config_manager.get_xxx(..., default=...)`
- 决策：
  - 当前可接受
  - 若后续继续治理，可再抽 `ConfigDefaults`

---

## 4. 当前结论

当前阶段 5 的结果不是“彻底消灭所有字面路径”，而是：

- 先消灭散落的路径判断
- 再把剩余兜底集中到少数明确入口

当前已经做到：

- 输出兜底集中到 `OutputPathResolver`
- 配置类路径兜底集中到 `ConfigManager`
- 业务模块不再各自硬编码主路径

这已经足以支撑后续进入阶段 6，而不必继续在阶段 5 上无限细抠。
