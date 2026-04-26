# src/features/ltr_manager/service/application_processing/ltr_number_generator.py
"""
LTR编号生成器模块（协调器版本）

负责编排 LTR 编号生成的完整流程，委托给子模块处理具体逻辑。
重构于 2026-04-24：从 542 行瘦身至约 200 行。
"""

import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from src.core.config_manager import config_manager
from src.core.logger import logger
from src.features.ltr_manager.service.ltr_base_service import LTRBaseService
from src.features.ltr_manager.service.ltr_editor_service import LTREditorService
from .ltr_scanner import LTRScanner
from .ltr_formatter import LTRFormatter
from .ltr_validator import LTRValidator


class LTRNumberGenerator:
    """LTR编号生成器类（协调器）
    
    职责：
    - 打开/关闭 Excel 文件
    - 根据 DL 类型路由到不同的处理分支
    - 协调 scanner/formatter/validator 完成业务逻辑
    """

    def __init__(self, parent=None):
        """初始化LTR编号生成器"""
        self.parent = parent
        self.excel_app = None
        self.workbook = None
        self.worksheet = None
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.ltr_service = LTRBaseService()
        
        # 初始化工具模块
        self.formatter = LTRFormatter(self.current_year, self.current_month)
        self.validator = LTRValidator(parent)

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
            
            # 验证格式
            if not self.validator.validate_dl_format(DL):
                if self.parent:
                    QMessageBox.warning(self.parent, "格式错误", f"不支持的DL编号格式: {DL}")
                return {
                    'executed_write': False,
                    'ltr_number': None,
                    'retry': True
                }
            
            # 根据DL值的不同情况处理
            if not DL or DL.strip() == "":
                # 情况1: 空号的情况
                return self._handle_empty_dl(data_columns)
            elif DL.strip().startswith(('W', 'w')):
                # 情况2: W开头的字符串
                logger.debug("处理 W 后缀编号: %s", DL)
                return self._handle_w_prefix_dl(DL.strip(), data_columns)
            elif self.formatter.validate_base_dl_format(DL.strip()):
                # 情况3: 基础编号
                return self._handle_base_dl(DL.strip(), data_columns)
            elif self.formatter.validate_base_with_suffix_format(DL.strip()):
                # 情况4: 基础号加后缀
                return self._handle_base_with_suffix_dl(DL.strip(), data_columns)
            else:
                # 不应该到达这里（validate_dl_format 已检查）
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
            logger.debug("获取 LTR 文件路径: %s", ltr_file_path)
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
                    logger.debug("尝试在目录查找 LTR 文件: %s", ltr_file_path)
                    
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
            self.excel_app.EnableEvents = False

            # 定位到当前年份工作表
            sheet_name = str(self.current_year)
            self.worksheet = self.ltr_service.navigate_to_year_sheet(self.workbook, sheet_name)

            if not self.worksheet:
                if self.parent:
                    QMessageBox.critical(self.parent, "错误", f"未找到{sheet_name}或{self.current_year - 1}工作表")
                return False
            else:
                logger.debug("成功定位到工作表: %s", self.worksheet.Name)

            logger.debug("LTR 文件打开成功")
            return True
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"打开LTR文件时发生错误: {str(e)}")
            return False

    def _handle_empty_dl(self, data_columns):
        """处理空DL编号的情况"""
        try:
            # 使用 Scanner 扫描已有编号
            scanner = LTRScanner(self.worksheet)
            found_numbers = scanner.scan_monthly_numbers(self.current_year, self.current_month)
            
            # 使用 Formatter 生成新编号
            ltr_number = self.formatter.format_monthly_number(found_numbers)
            
            # 使用 Scanner 查找目标行
            target_row = scanner.find_target_row()

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
            logger.debug("开始验证 W 前缀编号: %s", dl)
            # 验证W后缀格式
            is_valid = self.formatter.validate_w_prefix(dl)
            logger.debug("W 前缀编号格式验证结果: %s", is_valid)
            if not is_valid:
                logger.debug("W 前缀编号格式验证失败: %s", dl)
                if self.parent:
                    QMessageBox.warning(self.parent, "格式错误", f"W后缀编号格式无效，只能包含字母和数字: {dl}")
                else:
                    logger.debug("parent 为 None，无法显示警告对话框")
                return {
                    'executed_write': False,
                    'ltr_number': None
                }

            logger.debug("W 前缀编号格式验证通过: %s", dl)
            # 生成当月的基础编号
            scanner = LTRScanner(self.worksheet)
            found_numbers = scanner.scan_monthly_numbers(self.current_year, self.current_month)
            base_number = self.formatter.format_monthly_number(found_numbers)
            
            logger.debug("生成的基础编号: %s", base_number)
            # 添加后缀
            suffix = dl.upper()
            logger.debug("提取的后缀: %s", suffix)
            ltr_number = self.formatter.format_with_suffix(base_number, suffix)
            logger.debug("最终 LTR 编号: %s", ltr_number)
            
            target_row = scanner.find_target_row()

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
                
                # 使用 Scanner 提取行数据
                scanner = LTRScanner(target_worksheet)
                row_data = scanner.extract_row_data(target_row)
                
                if not self.validator.confirm_overwrite(dl, row_data):
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
            base_dl = self.formatter.extract_base_dl(dl)
            if not base_dl:
                if self.parent:
                    QMessageBox.critical(self.parent, "错误", "无法解析基础编号")
                return {
                    'executed_write': False,
                    'ltr_number': None
                }

            # 解析基础编号获取年份
            year = parse_result["year"]
            has_suffix = parse_result["has_suffix"]

            # 查找完整编号是否存在
            find_result = self.ltr_service.find_dl_number_in_workbook(self.workbook, year, has_suffix, dl)
            if find_result["success"]:
                # 完整编号存在，提取当前信息并让用户确认是否替换
                target_worksheet = find_result["worksheet"]
                target_row = find_result["row"]
                
                # 使用 Scanner 提取行数据
                scanner = LTRScanner(target_worksheet)
                row_data = scanner.extract_row_data(target_row)
                
                if not self.validator.confirm_overwrite(dl, row_data):
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
                    
                    # 使用 Scanner 提取行数据
                    scanner = LTRScanner(target_worksheet)
                    row_data = scanner.extract_row_data(target_row)
                    
                    if not self.validator.confirm_create_new(dl, base_dl, row_data):
                        return {
                            'executed_write': False,
                            'ltr_number': None
                        }

                    # 用户确认创建新编号
                    scanner_current = LTRScanner(self.worksheet)
                    target_row = scanner_current.find_target_row()
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
                    suffix = self.formatter.extract_suffix(dl, base_dl)
                    # 检查后缀是否是W开头的字符串
                    if self.formatter.validate_w_prefix(suffix):
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
                                
                                # 使用 Scanner 提取行数据
                                scanner = LTRScanner(target_worksheet)
                                row_data = scanner.extract_row_data(target_row)
                                
                                if self.validator.confirm_create_new(dl, base_with_w, row_data):
                                    # 用户确认创建新编号
                                    scanner_current = LTRScanner(self.worksheet)
                                    target_row = scanner_current.find_target_row()
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
                        # 不是W开头的后缀，提示用户
                        if self.parent:
                            QMessageBox.warning(self.parent, "警告", f"未找到基础编号 {base_dl}，无法生成关联编号")
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
        """更新现有数据"""
        try:
            editor_service = LTREditorService()
            update_result = editor_service.update_ltr_data(
                worksheet=worksheet,
                row=row,
                ltr_number=dl_number,
                data_columns=data_columns
            )
            
            if update_result["success"]:
                self._save_and_close()
                if self.parent:
                    QMessageBox.information(self.parent, "成功", f"成功更新编号 {dl_number} 的数据")
                return {
                    'executed_write': True,
                    'ltr_number': dl_number
                }
            else:
                if self.parent:
                    QMessageBox.critical(self.parent, "错误", f"更新数据失败: {update_result.get('error', '未知错误')}")
                return {
                    'executed_write': False,
                    'ltr_number': None
                }
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "错误", f"更新数据时发生错误: {str(e)}")
            return {
                'executed_write': False,
                'ltr_number': None
            }

    def _write_data_to_excel(self, ltr_number, row, data_columns, worksheet=None):
        """将数据写入Excel"""
        target_worksheet = worksheet or self.worksheet

        # 添加安全检查
        if not target_worksheet:
            raise RuntimeError("未指定有效的工作表")

        # 写入DL编号到D列
        cell_dl = target_worksheet.Cells(row, 4)
        cell_dl.Value = ltr_number
        # 清除字体格式
        try:
            cell_dl.Font.ColorIndex = 1  # 黑色
            cell_dl.Font.Strikethrough = False
        except Exception as e:
            logger.debug(f"清除单元格格式时出错: {e}")

        # 写入其他数据列
        if data_columns:
            for i, value in enumerate(data_columns):
                cell = target_worksheet.Cells(row, 5 + i)  # 从E列开始
                cell.Value = value
                # 清除字体格式
                try:
                    cell.Font.ColorIndex = 1  # 黑色
                    cell.Font.Strikethrough = False
                except Exception as e:
                    logger.debug(f"清除单元格格式时出错: {e}")

    def _save_and_close(self):
        """保存并关闭工作簿"""
        if self.workbook:
            self.workbook.Save()
            self.workbook.Close(SaveChanges=True)

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
