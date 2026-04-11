# TestFlowManager 输出目录盘点

> 更新时间：2026-04-09  
> 目的：盘点当前各导出/生成功能的默认落盘目录，标记哪些已接入统一目录规则，哪些仍保留历史兜底。

---

## 1. 目录规则总览

当前项目统一目录语义：

- `Submitted Material`
  - 提交材料型输出
  - 例如：报告生成、Test Record

- `Test results`
  - 测试结果类导出
  - 例如：LLCR、CR

- 项目子目录 / 项目工作目录
  - 与项目目录结构强绑定的输出
  - 例如：费用表

- `D:\OutFile`
  - 仅无项目态或目录解析失败时的全局兜底

当前统一入口：

- [output_paths.py](D:/PythonProject/TestFlowManager/src/core/output_paths.py)
  - `OutputPathResolver`

---

## 2. 已符合目录策略的链路

### 2.1 Report Wizard

- 入口：
  - [report_generation_service.py](D:/PythonProject/TestFlowManager/src/features/report_wizard/service/report_generation_service.py)
- 当前策略：
  - 已打开项目时，优先输出到项目下 `Submitted Material`
  - 无项目态时，回退 `D:\outfile`
- 结论：
  - 主线已符合目录策略
  - 保留无项目态兜底即可

### 2.2 Test Record

- 入口：
  - [test_record_controller.py](D:/PythonProject/TestFlowManager/src/features/test_record_generator/controller/test_record_controller.py)
- 当前策略：
  - 已打开项目时，优先输出到项目下 `Submitted Material`
  - 仅在目录解析失败时回退 `D:\outfile\testrecord.docx`
- 结论：
  - 主线已符合目录策略
  - 后续只需统一兜底路径大小写即可

### 2.3 LLCR / CR

- 入口：
  - [record_data_table_export_controller.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/export/controller/record_data_table_export_controller.py)
- 当前策略：
  - 已打开项目时，默认保存到项目下 `Test results`
  - 无项目态时，回退 `D:\OutFile`
- 结论：
  - 已完成目录策略收口

### 2.4 费用表

- 入口：
  - [fee_sheet_export_service.py](D:/PythonProject/TestFlowManager/src/features/matrix/service/export/service/fee_sheet_export_service.py)
- 当前策略：
  - 已打开项目时，优先保存到项目子目录中的既有费用表文件或项目工作目录
  - 仅无项目态时回退 `D:\OutFile`
- 结论：
  - 主线已符合目录策略

### 2.5 客户版报告

- 入口：
  - [customer_report_service.py](D:/PythonProject/TestFlowManager/src/features/customer_report_generator/service/customer_report_service.py)
  - [document_utils.py](D:/PythonProject/TestFlowManager/src/features/customer_report_generator/service/utils/document_utils.py)
- 当前策略：
  - 默认保存在源报告所在目录
- 结论：
  - 该功能属于“基于现有报告另存为”，目录策略合理
  - 不需要强行改到 `Submitted Material` 或 `Test results`

---

## 3. 当前保留的历史兜底点

### 3.1 Report Updater

- 入口：
  - [report_updater_controller.py](D:/PythonProject/TestFlowManager/src/features/report_updater/controller/report_updater_controller.py)
  - [report_updater_data.py](D:/PythonProject/TestFlowManager/src/features/report_updater/model/report_updater_data.py)
  - [report_updater_service.py](D:/PythonProject/TestFlowManager/src/features/report_updater/service/report_updater_service.py)
- 当前状态：
  - 已打开项目时，优先从项目目录选择报告
  - 无项目态时，仍以 `D:\OutFile` 作为报告选择起始目录
  - `paths.ini` 仍包含 `D:\OutFile\EquipmentID.docx` 等配置
- 结论：
  - 这是“更新已有报告”的链路，不是纯生成落盘链
  - 当前可接受保留兜底
  - 后续阶段可继续收口为“优先项目目录，配置只保存无项目态默认值”

### 3.2 Report Wizard / Test Record / Fee Sheet 的全局兜底

- 当前状态：
  - 代码里仍保留 `D:\outfile` / `D:\OutFile` 作为异常或无项目态兜底
- 结论：
  - 符合当前策略
  - 不应在已有项目态主链路中触发

---

## 4. 后续优先候选

下一轮若继续做路径治理，建议按以下顺序：

1. 统一 `D:\outfile` / `D:\OutFile` 大小写与常量来源
2. 收口 `ReportUpdater` 的无项目态目录配置
3. 为新功能禁止直接硬编码 `D:\OutFile`
4. 若需要，再抽单独的 `OutputPathPolicy` / `OutputPathResolver`

---

## 5. 当前结论

当前项目态输出主线已经基本稳定：

- `Submitted Material`
  - Report Wizard
  - Test Record

- `Test results`
  - LLCR
  - CR

- 项目工作目录
  - Fee Sheet

- 原目录另存
  - Customer Report

`D:\OutFile` 目前已经从主线项目态输出目录退回到“无项目态兜底”。下一阶段不应再新增依赖该目录的主流程功能。
