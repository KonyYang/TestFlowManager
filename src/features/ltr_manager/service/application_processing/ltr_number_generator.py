# src/features/ltr_manager/service/application_processing/ltr_number_generator.py
"""
LTR编号生成器模块
负责核心的Excel操作和LTR编号生成逻辑
"""

import os
import re
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from src.core.config_manager import config_manager

# 导入现有的工具函数和服务类，替换重复实现
from src.utils.excel_utils import (
    get_shared_excel_app,
    release_excel_app,
    close_workbook,
    open_excel_file
)
from src.features.ltr_manager.service.ltr_base_service import LTRBaseService

def is_file_open(ltr_file_path):
    """
    检查指定的 Excel 文件是否正在被其他进程打开
    :param ltr_file_path: 文件路径
    :return: True/False 表示是否被占用
    """
    try:
        with open(ltr_file_path, 'a'):
            pass
        return False
    except IOError:
        return True

def _generate_ltr_number_by_month(ws, current_year, current_month, target_row):
    """
    根据当前年月生成当月的 LTR 编号。
    如果已有编号，则根据现有规则生成下一个可用编号。
    """
    month_str = f"{current_month:02d}"  # 确保月份是两位数

    # 正则表达式匹配 DL-XXXX-YY-ZZZ 的格式
    ltr_pattern = re.compile(r'DL-\d{4}-' + re.escape(month_str) + r'-(\d{3})')
    found_numbers = []  # 存储当月已有的 ZZZ 部分

    # 遍历 D 列内容查找当月的 LTR 编号
    # 从第 2 行开始遍历，跳过标题行
    row = 2
    while True:
        cell_value = ws.Cells(row, 4).Value  # D列
        if cell_value is None or cell_value == "":
            # 连续空白行的判断已经在 find_first_blank_cell_from_top 中处理
            if row >= target_row:  # 已经遍历到或超过了目标写入行，说明之前的都检查过了
                break
        else:
            # Ensure cell_value is a string before applying regex
            if isinstance(cell_value, (str, int, float)):
                cell_value_str = str(cell_value)
                match = ltr_pattern.search(cell_value_str)
                if match:
                    try:
                        number = int(match.group(1))
                        found_numbers.append(number)
                    except ValueError:
                        pass
            else:
                pass

        # 防止无限循环，设置上限
        if row > 10000:  # 和 find_first_blank_cell_from_top 的上限保持一致或更高
            break
        row += 1

    if not found_numbers:
        # 当月还没有 LTR 编号
        ltr_number = f"DL-{current_year}-{month_str}-001"
        return ltr_number
    else:
        found_numbers.sort()
        max_number = found_numbers[-1]

        # 检查是否有遗漏的编号 (001 到 max_number 之间)
        missing_numbers = []
        for i in range(1, max_number + 1):
            if i not in found_numbers:
                missing_numbers.append(i)

        if missing_numbers:
            # 找到遗漏的编号，选择最小的遗漏编号填写
            next_number = min(missing_numbers)
            ltr_number = f"DL-{current_year}-{month_str}-{next_number:03d}"
        else:
            # 没有遗漏编号，使用最大编号 + 1
            next_number = max_number + 1
            ltr_number = f"DL-{current_year}-{month_str}-{next_number:03d}"
        return ltr_number

def is_full_ltr_with_suffix(dl):
    """
    判断是否是完整 LTR 编号加后缀的格式，如 DL-2024-06-001W
    """
    return isinstance(dl, str) and bool(re.fullmatch(r'DL-\d{4}-\d{2}-\d{3}[A-Za-z][A-Za-z0-9]*', dl.strip()))

def is_AlphaStart_Numeric_suffix(dl):
    """
    使用正则表达式判断是否符合格式：字母开头，后续为字母或数字
    """
    return isinstance(dl, str) and bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9]*', dl.strip()))

def _get_worksheet_by_base_ltr_year(wb, base_ltr):
    """
    根据 base_ltr 的年份获取工作表对象。
    :param wb: Excel 工作簿对象
    :param base_ltr: 基础 LTR 编号 (如 DL-2025-06-003)
    :return: 对应年份的工作表对象或 None
    """
    match = re.match(r"DL-(\d{4})-\d{2}-\d{3}", base_ltr.strip())
    if not match:
        raise ValueError(f"无法从 '{base_ltr}' 中提取年份信息")

    ltr_year = match.group(1)
    sheet_name = str(ltr_year)

    # 使用 LTRBaseService 的方法获取工作表
    ltr_service = LTRBaseService()
    return ltr_service.get_sheet_by_name(wb, sheet_name)

def base_ltr_exists(ws, base_ltr, target_row, wb=None):
    """
    判断基础编号是否存在于指定工作表或其对应的年份工作表中。
    :param ws: 当前操作的工作表对象（可能是上一年的）
    :param base_ltr: 基础编号（不带后缀）
    :param target_row: 目标写入行
    :param wb: Excel 工作簿对象（用于跨年查找）
    :return: bool
    """
    base_pattern = re.compile(re.escape(base_ltr) + r"(?![A-Za-z0-9])")  # 精确匹配，不接受任何后缀

    # 如果提供了 wb，则尝试定位 base_ltr 所属年份的工作表
    if wb:
        ws_target = _get_worksheet_by_base_ltr_year(wb, base_ltr)
        if ws_target:
            ws = ws_target  # 替换为正确年份的工作表

    row = 2
    while True:
        cell_value = ws.Cells(row, 4).Value
        if cell_value in (None, "", "None"):
            if row >= target_row:
                break
        else:
            cell_str = str(cell_value).strip()
            if base_pattern.fullmatch(cell_str):
                return True

        if row > 10000:
            break
        row += 1

    return False

def collect_similar_numbers_across_years(wb, base_ltr, target_row):
    """
    在当前年和上一年工作表中查找所有与 base_ltr 匹配的编号（含后缀）
    :param wb: Excel 工作簿对象
    :param base_ltr: 基础 LTR 编号（如 DL-2024-06-003）
    :param target_row: 目标写入行
    :return: 所有匹配的编号列表
    """
    similar_numbers = []
    base_pattern = re.compile(re.escape(base_ltr) + r"[A-Za-z0-9]*")

    # 获取 base_ltr 的年份
    match = re.match(r"DL-(\d{4})-\d{2}-\d{3}", base_ltr.strip())
    if not match:
        raise ValueError(f"无法从 '{base_ltr}' 中提取年份信息")
    base_year = int(match.group(1))

    # 确定需要检查的工作表年份
    years_to_check = set()
    current_year = datetime.now().year
    years_to_check.add(base_year)
    years_to_check.add(current_year)
    years_to_check.add(current_year - 1)

    ltr_service = LTRBaseService()
    for year in years_to_check:
        sheet_name = str(year)
        ws_found = ltr_service.get_sheet_by_name(wb, sheet_name)
        if ws_found:
            row = 2
            while True:
                cell_value = ws_found.Cells(row, 4).Value
                if cell_value in (None, "", "None"):
                    if row >= target_row:
                        break
                else:
                    cell_str = str(cell_value).strip()
                    if base_pattern.fullmatch(cell_str):
                        similar_numbers.append(cell_str)
                if row > 10000:
                    break
                row += 1

    return similar_numbers

def validate_user_defined_base_ltr(dl, ws, target_row, current_year, parent=None):
    """
    验证用户提供的基础 LTR 编号（无后缀，如 DL-2025-06-001）
    查找是否已存在，如果存在则显示 E-K 列内容让用户确认是否继续使用该编号
    :param dl: 用户输入的基础编号
    :param ws: Excel 工作表对象
    :param target_row: 目标写入行（用于判断查找范围）
    :param current_year: 当前年份
    :param parent: PyQt5 父窗口
    :return:
        - "confirmed" → 可以继续使用该编号
        - "retry" → 编号重复/无效，需要重新输入
        - "cancel" → 用户取消操作
        - row_num → 找到的行号（若存在）
    """
    dl = dl.strip()

    # 提取年份
    match = re.match(r"DL-(\d{4})-\d{2}-\d{3}", dl)
    if not match:
        raise ValueError(f"DL 格式错误: {dl}")
    ltr_year = int(match.group(1))
    valid_years = (current_year, current_year - 1)

    if ltr_year not in valid_years:
        if parent:
            QMessageBox.critical(
                parent,
                "年份错误",
                f"只能选择当前年 ({current_year}) 或上一年 ({current_year - 1}) 的年份，请重新输入。",
                QMessageBox.Ok
            )
        return "retry"

    # 检查编号是否存在
    found_row = None
    row = 2
    while True:
        cell_value = ws.Cells(row, 4).Value  # D列
        if cell_value is None or cell_value == "":
            if row >= target_row:
                break
        else:
            cell_str = str(cell_value).strip()
            if cell_str == dl:
                found_row = row
                break
        if row > 10000:
            break
        row += 1

    if not found_row:
        if parent:
            QMessageBox.warning(parent, "未找到编号", f"编号 {dl} 在当前工作表中不存在。")
        return "retry"

    # 收集 E-K 列的内容用于展示
    e_to_k_data = []
    for col_index in range(5, 12):  # E=5, F=6,..., K=11
        cell_value = ws.Cells(found_row, col_index).Value
        e_to_k_data.append("" if cell_value is None else str(cell_value).strip())

    # 构建提示信息
    msg = f"您选择的编号 {dl} 已存在。\n"
    msg += f"定位位置：第 {found_row} 行\n\n"
    msg += "当前 E-K 列数据如下：\n"
    msg += "\n".join([f"{chr(64 + i)}: {val}" for i, val in enumerate(e_to_k_data, start=5)])
    msg += "\n\n是否确认更新此行内容？（将覆盖原有内容）"

    if parent:
        reply = QMessageBox.question(
            parent,
            "编号确认",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return "cancel"

    # 设置全局变量用于后续赋值
    validate_user_defined_base_ltr.result = dl
    validate_user_defined_base_ltr.found_row = found_row  # 新增字段记录行号
    return "confirmed"

def validate_user_defined_ltr_with_suffix(dl, ws, target_row, current_year, parent=None, wb=None):
    """
    验证用户提供的完整 LTR 编号 + 后缀（如 DL-2025-03-021A）

    :param dl: 用户输入的完整编号
    :param ws: Excel 工作表对象
    :param target_row: 当前目标行
    :param current_year: 当前年份
    :param parent: PyQt5 父窗口
    :return:
        - "confirmed" → 可以继续写入
        - "retry" → 编号重复，需要用户重新输入
        - "cancel" → 用户取消操作
    """
    dl = dl.strip()
    valid_years = (current_year, current_year - 1)

    # 提取年份
    match = re.match(r"DL-(\d{4})-\d{2}-\d{3}[A-Za-z0-9]*", dl)
    if not match:
        raise ValueError(f"DL 格式错误: {dl}")

    ltr_year = int(match.group(1))
    if ltr_year not in valid_years:
        if parent:
            QMessageBox.critical(
                parent,
                "年份错误",
                f"只能选择当前年 ({current_year}) 或上一年 ({current_year - 1}) 的年份，请重新输入。",
                QMessageBox.Ok
            )
        return "retry"

    # 构建基础编号正则表达式
    base_match = re.match(r"(DL-\d{4}-\d{2}-\d{3})", dl)
    if not base_match:
        raise ValueError(f"无法提取基础编号部分: {dl}")
    base_ltr = base_match.group(1)

    # 检查基础编号是否存在
    if not base_ltr_exists(ws, base_ltr, target_row, wb=wb):
        msg = f"基础编号 {base_ltr} 尚未存在。\n\n您不能直接创建带后缀的编号。\n请先创建基础编号后再尝试添加后缀。"
        if parent:
            QMessageBox.warning(parent, "基础编号缺失", msg)
        return "retry"

    # 收集所有相关编号（跨年份）
    similar_numbers = collect_similar_numbers_across_years(wb, base_ltr, target_row)

    # 判断是否有完全重复项
    if dl in similar_numbers:
        msg = f"您输入的编号 {dl} 已存在。\n\n当前已有编号：\n" + "\n".join(similar_numbers) + "\n\n请重新输入一个未使用的编号。"
        if parent:
            QMessageBox.warning(parent, "编号重复", msg)
        return "retry"

    # 用户确认写入
    msg = f"您输入的编号 {dl} 尚未使用。\n\n当前已有相关编号：\n" + "\n".join(similar_numbers) + "\n\n是否确认写入？"
    if parent:
        reply = QMessageBox.question(parent, "编号确认", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return "cancel"
    else:
        return "cancel"

    # 设置全局变量用于后续赋值
    validate_user_defined_ltr_with_suffix.result = dl
    return "confirmed"

def validate_user_defined_ltr_exact_match(dl, wb, current_year, parent=None):
    """
    精确匹配用户输入的 LTR 编号（含或不含后缀），查找当前年和上一年的工作表中是否有完全匹配项。

    :param dl: 用户输入的完整 LTR 编号（如 DL-2024-06-001 或 DL-2024-06-001A）
    :param wb: Excel 工作簿对象
    :param current_year: 当前年份
    :param parent: PyQt5 UI 上下文
    :return:
        - "confirmed" → 成功找到并确认
        - "retry" → 未找到，需重新输入
        - "cancel" → 用户取消
        - result: 包含 ltr_number 和 found_row 的字典
    """
    # 添加DL值的有效性检查
    if not dl or not isinstance(dl, str) or dl.strip() == "" or dl.strip() == "DL-":
        if parent:
            QMessageBox.warning(parent, "无效编号", "LTR编号不能为空或格式错误。")
        return {"status": "retry"}

    dl = dl.strip()

    # 提取年份
    match = re.match(r"DL-(\d{4})-\d{2}-\d{3}[A-Za-z0-9]*", dl)
    if not match:
        if parent:
            QMessageBox.warning(parent, "格式错误", f"DL编号格式错误: {dl}")
        raise ValueError(f"DL 格式错误: {dl}")
    ltr_year = int(match.group(1))

    valid_years = (current_year, current_year - 1)
    if ltr_year not in valid_years:
        if parent:
            QMessageBox.critical(
                parent,
                "年份错误",
                f"只能选择当前年 ({current_year}) 或上一年 ({current_year - 1}) 的年份，请重新输入。",
                QMessageBox.Ok
            )
        return {"status": "retry"}

    years_to_check = [ltr_year]
    if ltr_year != current_year:
        years_to_check.append(current_year)  # 如果不是今年，也查今年

    found_rows = []
    ltr_service = LTRBaseService()

    for year in years_to_check:
        sheet_name = str(year)
        ws_found = ltr_service.get_sheet_by_name(wb, sheet_name)
        if not ws_found:
            continue

        row = 2
        while True:
            cell_value = ws_found.Cells(row, 4).Value
            if cell_value is None or cell_value == "":
                break
            elif str(cell_value).strip() == dl:
                found_rows.append((ws_found, row))
                break  # 找到第一个就停止（只允许唯一匹配）

            if row > 10000:
                break
            row += 1

    if len(found_rows) == 0:
        if parent:
            QMessageBox.warning(parent, "未找到编号", f"编号 {dl} 在最近两年工作表中均未找到。")
        return {"status": "retry"}
    elif len(found_rows) > 1:
        if parent:
            QMessageBox.warning(parent, "冲突", f"编号 {dl} 在多个工作表中找到，不允许重复使用。")
        return {"status": "retry"}

    ws, found_row = found_rows[0]

    # 收集 E-K 列数据
    e_to_k_data = []
    for col_index in range(5, 12):  # E=5, F=6,..., K=11
        cell_value = ws.Cells(found_row, col_index).Value
        e_to_k_data.append("" if cell_value is None else str(cell_value).strip())

    msg = f"您选择的编号 {dl} 已存在。\n"
    msg += f"定位位置：第 {found_row} 行\n\n"
    msg += "当前 E-K 列数据如下：\n"
    msg += "\n".join([f"{chr(64 + i)}: {val}" for i, val in enumerate(e_to_k_data, start=5)])
    msg += "\n\n是否确认更新此行内容？（将覆盖原有内容）"

    reply = QMessageBox.question(
        parent,
        "编号确认",
        msg,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply != QMessageBox.Yes:
        return {"status": "cancel"}

    return {
        "status": "confirmed",
        "ltr_number": dl,
        "ws": ws,
        "found_row": found_row
    }

def create_and_write_ltr_number(DL, data_columns=None, password="DGLAB", parent=None, is_update=False):
    """
    打开 Excel 文件，根据 DL 值确定 LTR 编号，并写入 D 列的第一个空白行。
    如果 DL 为空，则生成当月的 LTR 编号。
    如果文件被占用，弹窗提示是否以只读模式打开。

    :param DL: 创建 LTR 编号的依据，如果为空，则生成当月 LTR，或者固定前缀（如 W, WS）或其它值
    :param data_columns: 需要写入的数据列（列表）
    :param password: 工作簿密码
    :param parent: PyQt5 UI 上下文 (Optional)，用于弹窗提示
    :param is_update: 是否为更新操作（不申请新编号）
    :return: 包含以下字段的字典:
        - 'excel_app': Excel 应用程序对象
        - 'wb': 工作簿对象
        - 'executed_write': 是否执行了写入 (bool)
        - 'ltr_number': 写入的 LTR 编号 (str or None)
    """
    print("[DEBUG] create_and_write_ltr_number called")
    # 获取文件路径
    ltr_file_path = config_manager.get("paths.ltr_file")
    print(f"[DEBUG] LTR file path from config: {ltr_file_path}")

    # 检查路径是否有效
    if not ltr_file_path:
        error_msg = "LTR文件路径未配置或配置为空"
        print(f"[ERROR] {error_msg}")
        raise FileNotFoundError(error_msg)

    if not isinstance(ltr_file_path, (str, bytes, os.PathLike)):
        error_msg = f"LTR文件路径类型错误: {type(ltr_file_path)}"
        print(f"[ERROR] {error_msg}")
        raise TypeError(error_msg)


    def cleanup_excel_resources(excel_app, wb):
        """统一清理 Excel 资源"""
        try:
            if wb:
                close_workbook(wb)
        except Exception:
            pass
        try:
            if excel_app:
                excel_app.DisplayAlerts = True
                excel_app.EnableEvents = True
                release_excel_app()
        except Exception:
            pass

    if not os.path.exists(ltr_file_path):
        raise FileNotFoundError(f"文件路径不存在: {ltr_file_path}")

    # 检查文件是否被占用
    if is_file_open(ltr_file_path):
        if parent:
            QMessageBox.information(
                parent,
                "文件被占用",
                "该文件当前正在被其他人编辑，请稍后再试。",
                QMessageBox.Ok
            )
            # 直接返回而不是抛出异常，更符合函数式编程风格
            return {
                'excel_app': None,
                'wb': None,
                'executed_write': False,
                'ltr_number': None
            }
        else:
            # 抛出异常前确保资源清理
            raise RuntimeError("文件被占用，且无 UI 上下文进行交互")
    # 如果文件未被占用，继续执行文件打开逻辑
    excel_app = None
    wb = None
    ltr_service = LTRBaseService()  # 创建 LTRBaseService 实例
    try:
        excel_app = get_shared_excel_app()
        excel_app.Visible = False
        excel_app.DisplayAlerts = False
        excel_app.EnableEvents = False

        # 以读写模式打开文件
        wb = ltr_service.open_ltr_file(with_password=True)

        current_year = datetime.now().year
        current_month = datetime.now().month
        sheet_name_current = str(current_year)
        sheet_name_last_year = str(current_year - 1)
        ws = None

        # 尝试查找当前年份的工作表
        for worksheet in wb.Sheets:
            if worksheet.Name == sheet_name_current:
                ws = wb.Sheets(sheet_name_current)
                break
        else:
            for worksheet in wb.Sheets:
                if worksheet.Name == sheet_name_last_year:
                    ws = wb.Sheets(sheet_name_last_year)
                    break
            else:
                raise RuntimeError(f"未找到名为 {sheet_name_current} 或 {sheet_name_last_year} 的工作表")

        # 使用 LTRBaseService 中的方法替代
        ltr_service.clear_filters_and_unhide(ws)

        ltr_number = ""
        target_row = None
        found_row = None

        # ========== 更新模式：is_update=True ==========
        if is_update:
            if not DL:
                QMessageBox.critical(parent, "错误", "更新操作必须提供标准 LTR 编号（如 DL-2024-06-001 或 DL-2024-06-001A）")
                cleanup_excel_resources(excel_app, wb)
                return {
                    'excel_app': excel_app,
                    'wb': wb,
                    'executed_write': False,
                    'ltr_number': None
                }

            result = validate_user_defined_ltr_exact_match(DL.strip(), wb, current_year, parent)
            status = result.get("status")

            if status == "confirmed":
                ws = result.get("ws")
                found_row = result.get("found_row")
                if not ws or not found_row:
                    raise ValueError("validate_user_defined_ltr_exact_match 返回值不完整")

                target_row = found_row
                ltr_number = result.get("ltr_number")

                if not ltr_number:
                    raise ValueError("ltr_number 为空，请检查 validate_user_defined_ltr_exact_match 返回值")

            elif status in ["retry", "cancel"]:
                cleanup_excel_resources(excel_app, wb)
                return {
                    'excel_app': excel_app,
                    'wb': wb,
                    'executed_write': False,
                    'ltr_number': None
                }

        # ========== 默认模式：is_update=False ==========
        else:
            print("[DEBUG] Running in default (new entry) mode")
            # 查找 D 列第一个空白单元格所在的行
            print("[DEBUG] Finding first blank cell in column D...")
            target_cell = ltr_service.find_first_blank_cell_from_top(ws, 4)  # D列索引是4
            print(f"[DEBUG] find_first_blank_cell_from_top returned: {target_cell} (type: {type(target_cell)})")

            # 修正判断逻辑和行号获取方式
            if target_cell == 0:  # find_first_blank_cell_from_top返回0表示未找到
                raise RuntimeError("未找到 D 列的第一个空白行")
            target_row = target_cell  # 直接使用返回的行号
            print(f"[DEBUG] Target row: {target_row}")

            ltr_number = ""
            # 处理 DL 为空的情况
            if DL is None or DL.strip() == "":
                print("[DEBUG] DL is empty, generating LTR number by month")
                ltr_number = _generate_ltr_number_by_month(ws, current_year, current_month, target_row)
                print(f"[DEBUG] Generated LTR number: {ltr_number}")

            # 处理创建带后缀 DL 编号的情况
            elif re.fullmatch(r"DL-\d{4}-\d{2}-\d{3}[A-Za-z][A-Za-z0-9]*", DL.strip()):
                validation_result = validate_user_defined_ltr_with_suffix(DL.strip(), ws, target_row, current_year, parent, wb=wb)

                if validation_result == "confirmed":
                    ltr_number = validate_user_defined_ltr_with_suffix.result
                elif validation_result == "retry":
                    if parent:
                        new_dl, ok = QInputDialog.getText(parent, "重新输入编号", "请输入新的 LTR 编号:", text=DL)
                        if ok and new_dl.strip():
                            DL = new_dl.strip()
                            validation_result = validate_user_defined_ltr_with_suffix(DL, ws, target_row, current_year, parent, wb=wb)
                            if validation_result == "confirmed":
                                ltr_number = validate_user_defined_ltr_with_suffix.result
                            else:
                                raise RuntimeError("用户取消操作或仍为重号")
                        else:
                            QMessageBox.information(parent, "操作取消", "您已取消编号输入，操作已终止。")
                            cleanup_excel_resources(excel_app, wb)
                            return {
                                'excel_app': excel_app,
                                'wb': wb,
                                'executed_write': False,
                                'ltr_number': None
                            }
                    else:
                        QMessageBox.information(parent, "操作取消", "您未输入编号，操作已终止。")
                        cleanup_excel_resources(excel_app, wb)
                        return {
                            'excel_app': excel_app,
                            'wb': wb,
                            'executed_write': False,
                            'ltr_number': None
                        }
                elif validation_result == "cancel":
                    QMessageBox.information(parent, "操作取消", "您已取消编号输入，操作已终止。")
                    cleanup_excel_resources(excel_app, wb)
                    return {
                        'excel_app': excel_app,
                        'wb': wb,
                        'executed_write': False,
                        'ltr_number': None
                    }

            # 插入新分支：处理标准编号（无后缀）
            elif re.fullmatch(r"DL-\d{4}-\d{2}-\d{3}", DL.strip()):
                validation_result = validate_user_defined_base_ltr(DL.strip(), ws, target_row, current_year, parent)

                if validation_result == "confirmed":
                    ltr_number = validate_user_defined_base_ltr.result
                    found_row = getattr(validate_user_defined_base_ltr, 'found_row', None)
                    print(f"[DEBUG] Confirmed base LTR number: {ltr_number}, found_row: {found_row}")
                    if found_row:
                        target_row = found_row  # 直接使用行号
                        print(f"[DEBUG] Updated target row to existing row: {target_row}")
                    else:
                        target_cell = ltr_service.find_first_blank_cell_from_top(ws, 4)
                        print(
                            f"[DEBUG] find_first_blank_cell_from_top returned: {target_cell} (type: {type(target_cell)})")
                        if target_cell == 0:
                            raise RuntimeError("未找到 D 列的第一个空白行")
                        target_row = target_cell
                elif validation_result == "retry":
                    if parent:
                        new_dl, ok = QInputDialog.getText(parent, "重新输入编号", "请输入新的 LTR 编号:", text=DL)
                        if ok and new_dl.strip():
                            DL = new_dl.strip()
                            validation_result = validate_user_defined_base_ltr(DL, ws, target_row, current_year, parent)
                            if validation_result == "confirmed":
                                ltr_number = validate_user_defined_base_ltr.result
                            else:
                                QMessageBox.information(parent, "操作取消", "您已取消编号输入，操作已终止。")
                                cleanup_excel_resources(excel_app, wb)
                                return {
                                    'excel_app': excel_app,
                                    'wb': wb,
                                    'executed_write': False,
                                    'ltr_number': None
                                }
                        else:
                            QMessageBox.information(parent, "操作取消", "您未输入编号，操作已终止。")
                            cleanup_excel_resources(excel_app, wb)
                            return {
                                'excel_app': excel_app,
                                'wb': wb,
                                'executed_write': False,
                                'ltr_number': None
                            }
                elif validation_result == "cancel":
                    QMessageBox.information(parent, "操作取消", "您已取消编号输入，操作已终止。")
                    cleanup_excel_resources(excel_app, wb)
                    return {
                        'excel_app': excel_app,
                        'wb': wb,
                        'executed_write': False,
                        'ltr_number': None
                    }

            # 第三类：字母开头 + 数字/字母组合
            elif is_AlphaStart_Numeric_suffix(DL):
                base_ltr = _generate_ltr_number_by_month(ws, current_year, current_month, target_row)
                ltr_number = base_ltr + DL.strip()
            else:
                raise ValueError(f"DL 类型不支持: {DL}")

        # ========== 写入数据到 Excel ==========
        # 先写入 D 列的 LTR 编号
        ws.Cells(target_row, 4).Value = ltr_number  # D 列索引是 4

        if data_columns and len(data_columns) > 0:
            start_col = 5  # E 列开始
            for i, value in enumerate(data_columns):
                ws.Cells(target_row, start_col + i).Value = value

        # 保存并关闭工作簿
        wb.Save()
        wb.Close(SaveChanges=True)
        release_excel_app()

        return {
            'excel_app': excel_app,
            'wb': wb,
            'executed_write': True,
            'ltr_number': ltr_number
        }

    except Exception as e:
        if 'wb' in locals() and wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        if 'excel_app' in locals() and excel_app is not None:
            try:
                excel_app.DisplayAlerts = True
                excel_app.EnableEvents = True
                release_excel_app()
            except Exception:
                pass
        raise
