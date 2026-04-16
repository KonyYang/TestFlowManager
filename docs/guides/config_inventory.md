# TestFlowManager 配置项分层清单

> 更新时间：2026-04-09  
> 目的：盘点当前 `settings.json` 与 `paths.ini` 中的配置项，明确哪些属于部署变量、哪些属于默认值、哪些仍有历史硬编码兜底。

---

## 1. 当前有效配置文件

开发态：

- [settings.json](D:/PythonProject/TestFlowManager/src/app/config/settings.json)
- [paths.ini](D:/PythonProject/TestFlowManager/src/app/config/paths.ini)

打包态外部配置：

- `D:\TestFlowManager\config\settings.json`
- `D:\TestFlowManager\config\paths.ini`

约束：

- 仓库根目录下的 `config/` 不再作为有效配置来源
- 配置路径解析统一由 [config_manager.py](D:/PythonProject/TestFlowManager/src/core/config_manager.py) 提供

---

## 2. settings.json 分层

### 2.1 应用元信息

- `app.name`
- `app.version`
- `app.debug`

分类：

- 运行时基础配置
- 非部署敏感项

### 2.2 窗口默认值

- `window.width`
- `window.height`
- `window.position_x`
- `window.position_y`

分类：

- UI 默认值
- 允许保留在 `settings.json`

### 2.3 日志配置

- `logging.level`
- `logging.file`

分类：

- 运行环境配置
- 其中 `logging.file` 属于路径类配置，但当前仍保留在 `settings.json`

当前结论：

- `logging.level`
- `logging.file`

继续保留在 `settings.json`

原因：

- 它们属于应用运行时配置
- 不属于业务路径映射
- 当前不存在第二配置来源

### 2.4 LTR 字段配置入口

- `ltr.fields_config`

分类：

- 应用内部资源路径
- 更接近“应用资源引用”，不是用户部署变量

### 2.5 paths 段

- `paths.template_dir`
- `paths.default_project_path`
- `paths.backup_path`
- `paths.temp_dir`

分类：

- 部署变量
- 当前实际由业务模块高频使用
- 应继续保留在配置中，而不是写死在代码里

### 2.6 passwords 段

- `settings.json` 中不再保留密码配置

说明：

- 敏感项不再保留在主配置 JSON 中
- 当前仍以明文配置形式存在

---

## 3. paths.ini 分层

### 3.1 Paths

- `ltr_file`

分类：

- 部署变量

说明：

- `ltr_file` 已正式收口为 `paths.ini [Paths]` 的唯一来源
- `settings.json` 中的重复项已删除
- 当前代码主线已通过 `ConfigManager.get_path("ltr_file")` 统一访问

### 3.2 Passwords

- `ltr_password`

分类：

- 敏感部署变量

说明：

- `ltr_password` 已正式收口为 `paths.ini [Passwords]` 的唯一来源

### 3.3 Defaults

- `project_leader`

分类：

- 业务默认值
- 属于“可被界面预填”的默认参数，不是部署路径

### 3.4 STANDARD_FILES

- `standard_version_info_file`
- `standard_version_sheet_name`

分类：

- `standard_version_info_file`：部署变量
- `standard_version_sheet_name`：业务默认值

### 3.5 EquipmentDataSources

- `excel_file_path`
- `source_doc_path`
- `default_output_path`

分类：

- `excel_file_path`：部署变量
- `source_doc_path`：无项目态兜底
- `default_output_path`：无项目态兜底

说明：

- 这组配置主要服务 `report_updater`
- 已打开项目时：
  - `source_doc_path` 不再作为项目主路径使用
  - `default_output_path` 不再覆盖项目目录选择逻辑
- 当前主线已明确它们只在“无项目态”或“项目目录解析失败”时作为兜底

---

## 4. 当前已完成的配置访问收口

当前已通过 [config_manager.py](D:/PythonProject/TestFlowManager/src/core/config_manager.py) 提供显式访问接口：

- `get_path()`
- `get_default()`
- `get_password()`
- `get_standard_file()`
- `get_equipment_data_source()`

当前结果：

- 源码里已没有 `config_manager.get("paths.xxx")` 这一类散乱前缀访问
- 主线和高频模块已统一改走显式 API

---

## 5. 当前仍存在的历史硬编码兜底

以下位置仍保留硬编码路径作为 fallback，不代表主线配置来源：

- [document_parser_service.py](D:/PythonProject/TestFlowManager/src/features/document_parser/service/document_parser_service.py)
  - `D:\TestFlowManager\Template`
- [email_extractor_service.py](D:/PythonProject/TestFlowManager/src/features/email_extractor/service/email_extractor_service.py)
  - `D:\TestFlowManager\Temp`
- [folder_manager_service.py](D:/PythonProject/TestFlowManager/src/features/folder_manager/service/folder_manager_service.py)
  - `D:\TestFlowManager\Template`
  - `D:\TestFlowManager\Projects`
  - `D:\TestFlowManager\Backup`
- [output_paths.py](D:/PythonProject/TestFlowManager/src/core/output_paths.py)
  - `D:\OutFile`

说明：

- 这些路径当前仍可工作，但它们属于“代码兜底”，不是长期理想状态
- 后续阶段 5 可继续决定：
  - 保留为兜底常量
  - 迁入配置
  - 或按语义改为资源目录解析

相关决策文档：

- [fallback_path_decisions.md](D:/PythonProject/TestFlowManager/docs/fallback_path_decisions.md)

---

## 6. 建议的下一步分层治理

建议按以下顺序继续：

1. 明确哪些模板目录应视为“应用资源路径”，哪些应视为“用户可配置部署变量”
2. 决定 `logging.file` 是否继续保留在 `settings.json`
3. 继续去重其他可能重复的配置来源
4. 决定部分代码级硬编码兜底是继续保留还是迁回配置
5. 如有需要，再补一层 `ConfigSchema` / `TypedConfig`

---

## 7. 当前结论

当前阶段 5 已完成两件关键事：

- 配置根目录入口已统一到 `ConfigManager`
- 配置访问口径已从字符串前缀访问收口到显式 API

并已完成首个重复来源去重：

- `ltr_file` 已只保留在 `paths.ini`

并已完成第二项重复来源去重：

- `ltr_password` 已只保留在 `paths.ini [Passwords]`

并已明确日志配置归属：

- `logging.level`
- `logging.file`

继续保留在 `settings.json`

并已完成 `report_updater` 历史路径语义收口：

- `EquipmentDataSources.source_doc_path`
- `EquipmentDataSources.default_output_path`

两者都已降级为无项目态兜底配置

后续继续做配置治理时，应把重点放在：

- 配置项职责分层
- 历史硬编码兜底的去留决策
- 配置来源去重

## 8. 模板目录语义结论

当前结论：

- `paths.template_dir`
  - 应视为部署变量
  - 用于外部模板资产目录，例如：
    - 项目骨架目录 `DL-XXXX-YY-ZZZ`
    - 报告模板
    - 客户报告模板
    - Test Record 模板
    - 费用表模板

- `ltr.fields_config`
  - 应视为应用内部资源引用
  - 对应仓库内 `src/app/config/ltr_fields.json`
  - 不属于用户部署模板目录

当前已落地：

- [report_generation_service.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/service/report_generation_service.py) 已改为通过 `config_manager.get_template_dir()` 获取模板目录
- [fee_sheet_export_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/export/service/fee_sheet_export_service.py) 已改为通过 `config_manager.get_template_dir()` 获取模板目录

后续约束：

- 新增需要读取外部模板资产的功能，默认优先使用 `paths.template_dir`
- 不再把 `D:\TestFlowManager\Template` 直接写死成主路径
