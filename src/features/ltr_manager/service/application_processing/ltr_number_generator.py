# src/features/ltr_manager/service/application_processing/ltr_number_generator.py
"""
LTR编号生成器模块
负责核心的Excel操作和LTR编号生成逻辑
"""

import os
import re
import sys
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from src.core.config_manager import config_manager
from src.utils.excel_utils import get_sheet_by_name, close_workbook, release_excel_app
from src.features.ltr_manager.service.ltr_base_service import LTRBaseService
from src.features.ltr_manager.service.ltr_editor_service import LTREditorService


class LTRNumberGenerator:
    """LTR编号生成器类"""

    def __init__(self, parent=None):
        """初始化LTR编号生成器"""
        self.parent = parent
        self.excel_app = None
        self.workbook = None
        self.worksheet = None
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.ltr_service = LTRBaseService()

    def create_and_write_ltr_number(self, DL, data_columns=None, is_update=False):
        """
        打开 Excel 文件，根据 DL 值确定 LTR 编号，并写入 D 列的第一个空白行。

        :param DL: 创建 LTR 编号的依据
        :param data_columns: 需要写入的数据列（列表）
        :param is_update: 是否为更新操作
        :return: 包含以下字段的字典:
            - 'executed_write': 是否执行了写入 (bool)
            - 'ltr_number': 写入的 LTR 编号 (str or None)
        """
        try:
            # 打开LTR文件
            if not self._open_ltr_file():
                return {
                    'executed_write': False,
                    'ltr_number': None
                }
            # 根据DL值的不同情况处理
            if not DL or DL.strip() == "":
                # 情况1: 空号的情况
                return self._handle_empty_dl(data_columns)
            elif DL.strip().startswith(('W', 'w')):
                # 情况2: W开头的字符串
                print(f"[DEBUG] 处理W后缀编号: {DL}")
                return self._handle_w_prefix_dl(DL.strip(), data_columns)
            elif re.fullmatch(r"DL-\d{4}-\d{2}-\d{3}", DL.strip()):
                # 情况3: 基础编号
                return self._handle_base_dl(DL.strip(), data_columns)
            elif re.fullmatch(r"DL-\d{4}-\d{2}-\d{3}[A-Za-z][A-Za-z0-9]*", DL.strip()):
                # 情况4: 基础号加后缀
                return self._handle_base_with_suffix_dl(DL.strip(), data_columns)
            else:
                # 不支持的格式
                if self.parent:
                    QMessageBox.warning(self.parent, "格式错误", f"不支持的DL编号格式: {DL}")
                return {
                    'executed_write': False,
                    'ltr_number': None,
                    'retry': True
                }

        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"处理DL编号时发生错误: {str(e)}")
            return {
                'executed_write': False,
                'ltr_number': None
            }
        finally:
            self._cleanup_resources()

    def _open_ltr_file(self):
        """打开LTR文件"""
        try:
            ltr_file_path = config_manager.get_path("ltr_file")
            print(f"[DEBUG] 获取LTR文件路径: {ltr_file_path}")
            if not ltr_file_path or not os.path.exists(ltr_file_path):
                # 检查路径是否为相对路径
                if ltr_file_path and not os.path.isabs(ltr_file_path):
                    # 尝试在可执行文件目录下查找
                    if getattr(sys, 'frozen', False):
                        # 可执行文件模式
                        base_path = os.path.dirname(sys.executable)
                    else:
                        # 开发模式
                        base_path = os.path.abspath(".")
                    ltr_file_path = os.path.join(base_path, ltr_file_path)
                    print(f"[DEBUG] 尝试在目录查找LTR文件: {ltr_file_path}")
                    
                # 再次检查文件是否存在
                if not os.path.exists(ltr_file_path):
                    if self.parent:
                        QMessageBox.critical(self.parent, "错误", f"LTR文件不存在: {ltr_file_path}")
                    return False

            # 检查文件是否被其他进程占用
            if not self.ltr_service.check_file_not_locked(ltr_file_path):
                if self.parent:
                    QMessageBox.warning(self.parent, "文件被占用", f"LTR文件当前被其他用户或程序占用，请稍后再试：\n{ltr_file_path}")
                return False

            self.workbook = self.ltr_service.open_ltr_file(with_password=True)
            if not self.workbook:
                if self.parent:
                    QMessageBox.critical(self.parent, "错误", "无法打开LTR文件")
                return False

            self.excel_app = self.workbook.Application
            self.excel_app.Visible = False
            self.excel_app.DisplayAlerts = False
            self.excel_app.EnableEvents = False  # 建议添加

            # 定位到当前年份工作表
            sheet_name = str(self.current_year)
            self.worksheet = self.ltr_service.navigate_to_year_sheet(self.workbook, sheet_name)

            if not self.worksheet:
                if self.parent:
                    QMessageBox.critical(self.parent, "错误", f"未找到{sheet_name}或{self.current_year - 1}工作表")
                return False
            else:
                print(f"[DEBUG] 成功定位到工作表: {self.worksheet.Name}")

            print("[DEBUG] LTR文件打开成功")
            return True
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"打开LTR文件时发生错误: {str(e)}")
            return False

    def _handle_empty_dl(self, data_columns):
        """处理空DL编号的情况"""
        try:
            # 生成当月的基础编号
            ltr_number = self._generate_monthly_ltr_number()
            target_row = self._find_target_row()

            # 写入数据
            self._write_data_to_excel(ltr_number, target_row, data_columns)
            self._save_and_close()

            if self.parent:
                QMessageBox.information(self.parent, "成功", f"成功创建新编号: {ltr_number}")

            return {
                'executed_write': True,
                'ltr_number': ltr_number
            }
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"创建新编号时发生错误: {str(e)}")
            return {
                'executed_write': False,
                'ltr_number': None
            }

    def _handle_w_prefix_dl(self, dl, data_columns):
        """处理W开头的DL编号"""
        try:
            print(f"[DEBUG] 开始验证W前缀编号: {dl}")
            # 验证W后缀格式：W/w后面只能跟数字或字母
            pattern = r'^[Ww][A-Za-z0-9]*$'
            is_valid = re.match(pattern, dl)
            print(f"[DEBUG] 正则表达式 {pattern} 匹配结果: {is_valid}")
            if not is_valid:
                print(f"[DEBUG] W前缀编号格式验证失败: {dl}")
                if self.parent:
                    QMessageBox.warning(self.parent, "格式错误", f"W后缀编号格式无效，只能包含字母和数字: {dl}")
                else:
                    print(f"[DEBUG] parent为None，无法显示警告对话框")
                return {
                    'executed_write': False,
                    'ltr_number': None
                }

            print(f"[DEBUG] W前缀编号格式验证通过: {dl}")
            # 生成当月的基础编号
            base_number = self._generate_monthly_ltr_number()
            print(f"[DEBUG] 生成的基础编号: {base_number}")
            # 添加后缀
            suffix = dl.upper()  # 转换为大写并使用整个字符串作为后缀
            print(f"[DEBUG] 提取的后缀: '{suffix}'")
            ltr_number = base_number + suffix
            print(f"[DEBUG] 最终LTR编号: {ltr_number}")
            target_row = self._find_target_row()

            # 写入数据
            self._write_data_to_excel(ltr_number, target_row, data_columns)
            self._save_and_close()
            if self.parent:
                QMessageBox.information(self.parent, "成功", f"成功创建新编号: {ltr_number}")
            return {
                'executed_write': True,
                'ltr_number': ltr_number
            }
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"创建带后缀编号时发生错误: {str(e)}")
            return {
                'executed_write': False,
                'ltr_number': None
            }

    def _handle_base_dl(self, dl, data_columns):
        """处理基础编号"""
        try:
            # 验证并解析DL编号
            parse_result = self.ltr_service.validate_and_parse_dl_number(dl)
            if not parse_result["valid"]:
                if self.parent:
                    QMessageBox.warning(self.parent, "更新失败", f"DL编号格式无效: {dl}")
                return {
                    'executed_write': False,
                    'ltr_number': None
                }

            # 解析基础编号获取年份
            year = parse_result["year"]
            has_suffix = parse_result["has_suffix"]

            # 查找该编号
            find_result = self.ltr_service.find_dl_number_in_workbook(self.workbook, year, has_suffix, dl)
            if find_result["success"]:
                # 编号存在，提取当前信息并让用户确认是否替换
                target_worksheet = find_result["worksheet"]
                target_row = find_result["row"]
                row_data = self.ltr_service.extract_row_data(target_worksheet, target_row)
                if not self._confirm_overwrite(dl, row_data):
                    return {
                        'executed_write': False,
                        'ltr_number': None,
                        'retry': True
                    }
                # 用户确认替换，使用LTREditorService更新数据
                return self._update_existing_data(dl, data_columns, target_worksheet, target_row)
            else:
                # 编号不存在，仅提示用户
                if self.parent:
                    QMessageBox.information(self.parent, "提示", f"编号 {dl} 不存在")

                return {
                    'executed_write': False,
                    'ltr_number': None,
                    'retry': True
                }
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"处理基础编号时发生错误: {str(e)}")
            return {
                'executed_write': False,
                'ltr_number': None
            }

    def _handle_base_with_suffix_dl(self, dl, data_columns):
        """处理基础编号加后缀"""
        try:
            # 验证并解析DL编号
            parse_result = self.ltr_service.validate_and_parse_dl_number(dl)
            if not parse_result["valid"]:
                if self.parent:
                    QMessageBox.warning(self.parent, "更新失败", f"DL编号格式无效: {dl}")
                return {
                    'executed_write': False,
                    'ltr_number': None
                }

            # 提取基础编号
            base_dl_match = re.match(r"(DL-\d{4}-\d{2}-\d{3})", dl)
            if not base_dl_match:
                if self.parent:
                    QMessageBox.critical(self.parent, "错误", "无法解析基础编号")
                return {
                    'executed_write': False,
                    'ltr_number': None
                }
            base_dl = base_dl_match.group(1)

            # 解析基础编号获取年份
            year = parse_result["year"]
            has_suffix = parse_result["has_suffix"]

            # 查找完整编号是否存在
            find_result = self.ltr_service.find_dl_number_in_workbook(self.workbook, year, has_suffix, dl)
            if find_result["success"]:
                # 完整编号存在，提取当前信息并让用户确认是否替换
                target_worksheet = find_result["worksheet"]
                target_row = find_result["row"]
                row_data = self.ltr_service.extract_row_data(target_worksheet, target_row)
                if not self._confirm_overwrite(dl, row_data):
                    return {
                        'executed_write': False,
                        'ltr_number': None
                    }

                # 用户确认替换，使用LTREditorService更新数据
                return self._update_existing_data(dl, data_columns, target_worksheet, target_row)
            else:
                # 完整编号不存在，检查基础编号是否存在
                base_parse_result = self.ltr_service.validate_and_parse_dl_number(base_dl)
                base_find_result = self.ltr_service.find_dl_number_in_workbook(
                    self.workbook,
                    base_parse_result["year"],
                    base_parse_result["has_suffix"],
                    base_dl
                )

                if base_find_result["success"]:
                    # 基础编号存在，显示摘要信息，提示是否创建新的关联编号而不是覆盖
                    target_worksheet = base_find_result["worksheet"]
                    target_row = base_find_result["row"]
                    row_data = self.ltr_service.extract_row_data(target_worksheet, target_row)
                    if not self._confirm_create_new(dl, base_dl, row_data):
                        return {
                            'executed_write': False,
                            'ltr_number': None
                        }

                    # 用户确认创建新编号
                    target_row = self._find_target_row()
                    self._write_data_to_excel(dl, target_row, data_columns)
                    self._save_and_close()

                    if self.parent:
                        QMessageBox.information(self.parent, "成功", f"成功创建关联编号: {dl}")

                    return {
                        'executed_write': True,
                        'ltr_number': dl
                    }
                else:
                    # 基础编号也不存在，检查是否是W开头的特殊后缀
                    suffix = dl[len(base_dl):]  # 获取后缀部分
                    # 检查后缀是否是W开头的字符串
                    if re.fullmatch(r'^[Ww][A-Za-z0-9]*$', suffix):
                        # 构造基础编号+W的组合进行查找
                        base_with_w = base_dl + "W"
                        base_w_parse_result = self.ltr_service.validate_and_parse_dl_number(base_with_w)
                        if base_w_parse_result["valid"]:
                            base_w_find_result = self.ltr_service.find_dl_number_in_workbook(
                                self.workbook,
                                base_w_parse_result["year"],
                                base_w_parse_result["has_suffix"],
                                base_with_w
                            )
                            
                            # 如果找到基础编号+W的记录
                            if base_w_find_result["success"]:
                                # 显示摘要信息，提示是否创建新的关联编号
                                target_worksheet = base_w_find_result["worksheet"]
                                target_row = base_w_find_result["row"]
                                row_data = self.ltr_service.extract_row_data(target_worksheet, target_row)
                                if self._confirm_create_new(dl, base_with_w, row_data):
                                    # 用户确认创建新编号
                                    target_row = self._find_target_row()
                                    self._write_data_to_excel(dl, target_row, data_columns)
                                    self._save_and_close()

                                    if self.parent:
                                        QMessageBox.information(self.parent, "成功", f"成功创建关联编号: {dl}")

                                    return {
                                        'executed_write': True,
                                        'ltr_number': dl
                                    }
                        
                        # 如果没有找到基础编号+W的记录或者用户未确认创建
                        if self.parent:
                            QMessageBox.warning(self.parent, "警告", f"未找到可关联的基础编号，无法生成关联编号{dl}")
                        return {
                            'executed_write': False,
                            'ltr_number': None,
                            'retry': True
                        }
                    else:
                        # 基础编号也不存在，提醒用户
                        if self.parent:
                            QMessageBox.warning(self.parent, "警告", f"基础编号{base_dl}不存在，无法生成关联编号")
                        return {
                            'executed_write': False,
                            'ltr_number': None,
                            'retry': True
                        }
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"处理带后缀编号时发生错误: {str(e)}")
            return {
                'executed_write': False,
                'ltr_number': None
            }

    def _update_existing_data(self, dl_number, data_columns, worksheet, row):
        """使用LTREditorService更新现有数据"""
        try:
            # 使用基类的通用更新方法
            if self.ltr_service.update_worksheet_data(worksheet, row, data_columns, self.parent):
                # 保存工作簿
                self.workbook.Save()

                if self.parent:
                    QMessageBox.information(self.parent, "更新成功", f"DL编号 {dl_number} 的数据已成功更新。")

                return {
                    'executed_write': True,
                    'ltr_number': dl_number
                }
            else:
                return {
                    'executed_write': False,
                    'ltr_number': None
                }
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "更新失败", f"更新数据时发生错误: {str(e)}")
            return {
                'executed_write': False,
                'ltr_number': None
            }

    def _generate_monthly_ltr_number(self):
        """生成当月的基础LTR编号"""
        month_str = f"{self.current_month:02d}"
        # 查找当前月份已有的编号
        found_numbers = []
        row = 2  # 从第2行开始（跳过标题行）

        while row < 10000:  # 设置上限防止无限循环
            cell_value = self.worksheet.Cells(row, 4).Value  # D列
            if cell_value is None or cell_value == "":
                break

            if isinstance(cell_value, (str, int, float)):
                cell_value_str = str(cell_value)
                # 设置匹配模式，匹配当前年月的编号
                pattern = re.compile(rf'DL-{self.current_year}-{month_str}-(\d{{3}})[A-Za-z]*')
                match = pattern.search(cell_value_str) # 执行匹配
                if match:
                    try:
                        number = int(match.group(1)) # 将第一个捕获组的数字内容转换为整数
                        found_numbers.append(number)
                    except ValueError:
                        pass
            row += 1

        if not found_numbers:
            # 当月还没有编号
            return f"DL-{self.current_year}-{month_str}-001"
        else:
            # 找到最大编号并加1
            max_number = max(found_numbers)
            next_number = max_number + 1
            return f"DL-{self.current_year}-{month_str}-{next_number:03d}"

    def _find_target_row(self):
        """查找目标写入行"""
        row = 2  # 从第2行开始
        while row < 10000:
            cell_value = self.worksheet.Cells(row, 4).Value  # D列
            if cell_value is None or cell_value == "":
                return row
            row += 1
        raise RuntimeError("无法找到空白行")

    def _confirm_overwrite(self, dl_number, row_data):
        """确认是否覆盖现有数据"""
        if not self.parent:
            return True

        msg = f"编号 {dl_number} 已存在。\n\n当前数据:\n"
        for col, value in row_data.items():
            msg += f"{col}: {value}\n"
        msg += "\n是否确认覆盖？"

        reply = QMessageBox.question(
            self.parent,
            "确认覆盖",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def _confirm_create_new(self, new_dl, base_dl, row_data):
        """确认是否创建新编号"""
        if not self.parent:
            return True

        msg = f"基础编号 {base_dl} 已存在。\n\n当前数据:\n"
        for col, value in row_data.items():
            msg += f"{col}: {value}\n"
        msg += f"\n是否基于此信息创建关联编号 {new_dl}？"

        reply = QMessageBox.question(
            self.parent,
            "确认创建",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def _write_data_to_excel(self, ltr_number, row, data_columns, worksheet=None):
        """将数据写入Excel"""
        target_worksheet = worksheet or self.worksheet

        # 添加安全检查
        if not target_worksheet:
            raise RuntimeError("未指定有效的工作表")

        # 写入DL编号到D列
        target_worksheet.Cells(row, 4).Value = ltr_number

        # 写入其他数据列
        if data_columns:
            for i, value in enumerate(data_columns):
                    target_worksheet.Cells(row, 5 + i).Value = value  # 从E列开始

    def _save_and_close(self):
        """保存并关闭工作簿"""
        if self.workbook:
            self.workbook.Save()
            self.workbook.Close(SaveChanges=True)

    # 在 _cleanup_resources 方法中应该完善资源释放逻辑
    def _cleanup_resources(self):
        """清理资源"""
        try:
            # 保存并关闭工作簿
            if self.workbook:
                try:
                    self.workbook.Close(SaveChanges=False)
                except:
                    pass
        except:
            pass
        finally:
            # 释放Excel应用程序
            try:
                if self.excel_app:
                    self.excel_app.DisplayAlerts = True
                    # 使用excel_utils提供的统一释放机制
                    from src.utils.excel_utils import release_excel_app
                    release_excel_app()
            except:
                pass
