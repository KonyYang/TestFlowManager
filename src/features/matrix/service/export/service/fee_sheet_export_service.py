"""
费用表导出服务
提供生成费用表的业务逻辑服务（COM 操作 + 数据编排）
"""

import os
import time
from typing import Dict, Any, List, Optional

from src.core.logger import logger
from src.domain.project.output_paths import OutputPathResolver
from src.core.project_context import ProjectContext
from src.domain.project.project_document_context import ProjectDocumentContext
from src.infrastructure.office.facade import OfficeFacade
from src.infrastructure.office.session import OfficeSession
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from src.features.matrix.service.export.service.fee_sheet_path_resolver import (
    FeeSheetPathResolver,
)
from src.features.matrix.service.export.service.fee_sheet_anchor_helper import (
    FeeSheetAnchorHelper,
)


class FeeSheetExportService:
    """
    费用表导出服务类
    提供生成费用表的业务逻辑服务（COM + 编排）
    """

    def __init__(
        self,
        project_context: Optional[ProjectContext] = None,
        office_facade: Optional[OfficeFacade] = None,
    ):
        """初始化费用表导出服务"""
        self._path_resolver = FeeSheetPathResolver()
        self._anchor_helper = FeeSheetAnchorHelper()
        self._office_facade = office_facade or OfficeFacade()
        # 兼容性属性（外部代码可能直接访问）
        self.template_dir = self._path_resolver.template_dir
        self.output_dir = self._path_resolver.output_dir
        self.excel_app = None
        self.project_context = project_context

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        self.project_context = project_context

    def get_project_context(self) -> Optional[ProjectContext]:
        return self.project_context

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """委托到 PathResolver（兼容性保留）"""
        return FeeSheetPathResolver.sanitize_filename(filename)

    # =========================================================================
    # Matrix 数据提取
    # =========================================================================

    def _get_group_tests_from_matrix(
        self, matrix_data_structure: MatrixDataStructure
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        从 Matrix 数据结构获取每个组别的测试项目信息。
        """
        if matrix_data_structure is None:
            return {}

        all_groups = matrix_data_structure.get_all_groups()
        group_tests_info = {}

        for group in all_groups:
            group_step_data = matrix_data_structure.get_group_steps(group)
            tests_list = []
            for step in group_step_data:
                test_info = {
                    "step_num": step.get("StepNumber", ""),
                    "test": step.get("Test", ""),
                    "test_method": step.get("TestMethod", ""),
                    "condition": step.get("Condition", ""),
                    "requirement": step.get("Requirement", ""),
                    "remark": step.get("StepDescription", ""),
                }
                tests_list.append(test_info)

            group_tests_info[group] = tests_list

        return group_tests_info

    # =========================================================================
    # Excel 数据填充 (COM 操作)
    # =========================================================================

    def _fill_group_tests_data(
        self, worksheet, group_tests_info: Dict[str, List[Dict[str, Any]]]
    ) -> bool:
        """
        填充测试组别数据到 Excel 表格中。
        :param worksheet: Excel 工作表对象
        :param group_tests_info: 包含每个组别测试项目信息的字典
        :return: 是否成功填充
        """
        try:
            anchor = self._anchor_helper.find_sample_preparation_anchor(worksheet)
            if not anchor:
                logger.warning("未找到 'Sample preparation (if needed)' 行，无法按要求填充组别数据")
                return False

            base_row, template_row, template_col = anchor
            template_cell_value = worksheet.Cells(template_row, template_col).Value
            if template_cell_value not in (None, ""):
                logger.warning(f"第{template_row}行第{template_col}列不是空白模板单元格，无法按要求复制行")
                return False

            logger.debug(f"找到基础行 (第{base_row}行) 和模板行 (第{template_row}行)")

            used_range = worksheet.UsedRange
            total_rows = used_range.Rows.Count

            original_heights = {}
            for row in range(13, min(total_rows + 1, 50)):
                try:
                    original_heights[row] = worksheet.Rows(row).Height
                except Exception:
                    continue

            current_row = 6

            for group_idx, (group_name, tests_list) in enumerate(group_tests_info.items()):
                logger.info(f"正在填充组别: {group_name}")

                if not tests_list:
                    continue

                all_tests = tests_list
                num_tests = len(all_tests)
                max_cols = used_range.Columns.Count

                if group_idx == 0:
                    worksheet.Cells(current_row, 3).Value = (
                        all_tests[0].get("test", "") if all_tests else ""
                    )

                    if num_tests > 1:
                        for i in range(num_tests - 1):
                            insert_position = current_row + 1 + i
                            row_to_insert = worksheet.Rows(insert_position)

                            source_range_6th = worksheet.Range(
                                worksheet.Cells(template_row, 1),
                                worksheet.Cells(template_row, max_cols),
                            )
                            source_range_6th.Copy()

                            row_to_insert.Insert()

                            if i + 1 < len(all_tests):
                                worksheet.Cells(insert_position, 3).Value = all_tests[
                                    i + 1
                                ].get("test", "")
                                logger.debug(
                                    f"  在第{insert_position}行C列插入新行并填入测试项目: "
                                    f"{all_tests[i + 1].get('test', '')}"
                                )

                    group_range = worksheet.Range(
                        worksheet.Cells(base_row, 1),
                        worksheet.Cells(current_row + num_tests - 1, 1),
                    )
                    group_range.Merge()
                    worksheet.Cells(base_row, 1).Value = group_name
                    logger.debug(
                        f"  合并A列第{base_row}行到第{current_row + num_tests - 1}行，"
                        f"并填入组别名称: {group_name}"
                    )

                    current_row = current_row + num_tests

                else:
                    new_group_start = current_row

                    source_range_5th = worksheet.Range(
                        worksheet.Cells(base_row, 1),
                        worksheet.Cells(base_row, max_cols),
                    )
                    source_range_5th.Copy()

                    row_to_insert = worksheet.Rows(new_group_start)
                    row_to_insert.Insert()

                    for i in range(num_tests):
                        insert_position = new_group_start + 1 + i
                        row_to_insert = worksheet.Rows(insert_position)

                        source_range_6th = worksheet.Range(
                            worksheet.Cells(template_row, 1),
                            worksheet.Cells(template_row, max_cols),
                        )
                        source_range_6th.Copy()

                        row_to_insert.Insert()

                        if i < len(all_tests):
                            worksheet.Cells(insert_position, 3).Value = all_tests[i].get(
                                "test", ""
                            )
                            logger.debug(
                                f"  在第{insert_position}行插入新行并填入测试项目: "
                                f"{all_tests[i].get('test', '')}"
                            )

                    actual_end_row = new_group_start + num_tests

                    group_range = worksheet.Range(
                        worksheet.Cells(new_group_start, 1),
                        worksheet.Cells(actual_end_row, 1),
                    )
                    group_range.Merge()
                    worksheet.Cells(new_group_start, 1).Value = group_name
                    logger.debug(
                        f"  合并A列第{new_group_start}行到第{actual_end_row}行，"
                        f"并填入组别名称: {group_name}"
                    )

                    current_row = actual_end_row + 1

                logger.debug(f"  组别 {group_name} 填充完成，测试数: {num_tests}")

            for row, height in original_heights.items():
                try:
                    worksheet.Rows(row).Height = height
                except Exception:
                    continue

            if current_row > 6:
                try:
                    auto_fit_range = worksheet.Range(
                        worksheet.Cells(6, 1),
                        worksheet.Cells(current_row - 1, max_cols),
                    )
                    auto_fit_range.EntireRow.AutoFit()
                    logger.info(f"已设置第6行到第{current_row - 1}行的自适应行高")
                except Exception as e:
                    logger.warning(f"设置自适应行高时出错: {e}")

            logger.info("测试组别数据填充完成")
            return True

        except Exception as e:
            logger.error(f"填充测试组别数据时出错: {e}", exc_info=True)
            return False

    # =========================================================================
    # 主导出入口
    # =========================================================================

    def export_fee_sheet(
        self,
        matrix_data_structure: MatrixDataStructure,
        dl_number: str = "DL-UNKNOWN",
        requested_by: str = "",
        location: str = "",
        product_description: str = "",
        tests_to_be_performed: str = "",
    ) -> tuple:
        """
        导出费用表。

        :param matrix_data_structure: Matrix 数据结构
        :param dl_number: DL 编号
        :param requested_by: 申请人
        :param location: 地点
        :param product_description: 产品描述
        :param tests_to_be_performed: 测试项目
        :return: (是否成功, 输出文件路径)
        """
        try:
            logger.info("开始导出费用表")
            document_context = ProjectDocumentContext.from_project_context(
                self.get_project_context()
            )
            project_context = document_context.project_context
            current_project = (
                project_context.project_path if project_context else None
            )

            if dl_number == "DL-UNKNOWN" and document_context.dl_number:
                dl_number = document_context.dl_number
            if not requested_by:
                requested_by = document_context.get_field("requested_by", "")
            if not location:
                location = document_context.get_field("location", "")
            if not product_description:
                product_description = document_context.get_field(
                    "product_description", ""
                )
            if not tests_to_be_performed:
                tests_to_be_performed = document_context.get_field(
                    "tests_to_be_performed", ""
                )

            # ---- 输出路径解析 ----
            output_path, output_dir, use_existing_file = (
                self._resolve_output_path(
                    current_project, dl_number, product_description, tests_to_be_performed
                )
            )

            os.makedirs(output_dir, exist_ok=True)

            # ---- 获取测试项目信息 ----
            group_tests_info = self._get_group_tests_from_matrix(matrix_data_structure)

            logger.info(f"正在处理费用表文件: {output_path}")

            if not use_existing_file:
                templates = self._path_resolver.find_fee_sheet_templates()
                if not templates:
                    logger.error("未找到费用表模板文件")
                    return (False, None)

                import shutil
                shutil.copy2(templates[0], output_path)
                logger.info(f"已复制模板文件到: {output_path}")

            # ✅ 使用 with_excel_workbook 管理整个生命周期
            def _fill_excel_data(workbook):
                ws = workbook.Sheets(1)
                self.excel_app = workbook.Application

                if use_existing_file:
                    existing_anchor = self._anchor_helper.find_sample_preparation_anchor(ws)
                    if not existing_anchor:
                        logger.warning(
                            "现有费用表不包含标准模板主体结构，"
                            "将使用标准模板重建后再填充"
                        )
                        raise ValueError("NEED_REBUILD")

                success = self._fill_group_tests_data(ws, group_tests_info)

                if not success:
                    logger.warning(f"填充测试组别数据失败: {output_path}")
                    return False

                if not use_existing_file:
                    if dl_number:
                        ws.Range("D2").Value = dl_number
                    if product_description or tests_to_be_performed:
                        combined_desc = (
                            f"{product_description} {tests_to_be_performed}".strip()
                        )
                        ws.Range("G2").Value = combined_desc
                    if requested_by:
                        ws.Range("D3").Value = requested_by
                    if location:
                        ws.Range("G3").Value = location

                    logger.info(
                        f"基本信息和测试组别数据已填充到: {output_path}，格式已保留"
                    )
                else:
                    logger.info(
                        f"使用现有费用表文件: {output_path}，已填充测试组别数据"
                    )

                return True

            try:
                self._office_facade.with_excel_workbook(
                    output_path,
                    _fill_excel_data,
                    read_only=False,
                    save=True,
                )
            except ValueError as e:
                if str(e) == "NEED_REBUILD":
                    # 需要重建文件
                    rebuilt = self._path_resolver.rebuild_from_template(output_path)
                    if not rebuilt:
                        return (False, None)

                    # 重新填充
                    def _fill_after_rebuild(workbook):
                        ws = workbook.Sheets(1)
                        self.excel_app = workbook.Application
                        success = self._fill_group_tests_data(ws, group_tests_info)
                        if not success:
                            return False
                        return True

                    self._office_facade.with_excel_workbook(
                        output_path,
                        _fill_after_rebuild,
                        read_only=False,
                        save=True,
                    )
                else:
                    raise

            logger.info("费用表导出完成！")
            return (True, output_path)

        except Exception as e:
            logger.error(f"导出费用表时出错: {e}", exc_info=True)
            return (False, None)

    # =========================================================================
    # 输出路径解析 (私有编排方法)
    # =========================================================================

    def _resolve_output_path(
        self, current_project, dl_number, product_description, tests_to_be_performed
    ) -> tuple:
        """
        解析费用表的输出路径。

        Returns:
            (output_path, output_dir, use_existing_file) 元组
        """
        resolver = self._path_resolver

        if current_project and os.path.exists(current_project):
            logger.info(f"检测到已打开项目: {current_project}")
            logger.info(f"使用项目名称作为 DL 编号: {dl_number}")

            found_folder_info = resolver.find_fee_sheet_folder_and_file(
                current_project, dl_number
            )

            if found_folder_info:
                folder_path, fee_sheet_path = found_folder_info
                if fee_sheet_path:
                    logger.info(f"找到已存在的费用表文件: {fee_sheet_path}")
                    folder_name = os.path.basename(folder_path)
                    if folder_name.startswith(dl_number):
                        product_description = folder_name[len(dl_number):].strip()
                    return (fee_sheet_path, folder_path, True)

                else:
                    logger.info(
                        f"在子文件夹 {folder_path} 中未找到费用表文件，将生成新文件"
                    )
                    output_dir = folder_path
                    folder_name = os.path.basename(folder_path)
                    fee_sheet_filename = f"{folder_name} Testing Fee Evaluation.xls"
                    output_path = os.path.abspath(os.path.join(output_dir, fee_sheet_filename))
                    logger.debug(f"目标文件绝对路径: {output_path}")

                    if folder_name.startswith(dl_number):
                        product_description = folder_name[len(dl_number):].strip()
                    return (output_path, output_dir, False)

            else:
                logger.info("未找到包含 DL 编号的子文件夹，将创建新文件夹并生成新文件")

                project_subfolder_name = (
                    f"{dl_number} {product_description} {tests_to_be_performed}".strip()
                )
                project_subfolder_name = resolver.sanitize_filename(project_subfolder_name)

                output_dir = os.path.abspath(os.path.join(current_project, project_subfolder_name))
                logger.debug(f"目标文件夹绝对路径: {output_dir}")

                os.makedirs(output_dir, exist_ok=True)

                project_subfolder_name = (
                    f"{dl_number} {product_description} {tests_to_be_performed}".strip()
                )
                project_subfolder_name = resolver.sanitize_filename(project_subfolder_name)
                fee_sheet_filename = f"{project_subfolder_name} Testing Fee Evaluation.xls"
                output_path = os.path.abspath(os.path.join(output_dir, fee_sheet_filename))
                logger.debug(f"目标文件绝对路径: {output_path}")

                return (output_path, output_dir, False)

        else:
            logger.info("未检测到打开的项目，使用默认输出路径")
            os.makedirs(self.output_dir, exist_ok=True)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            templates = resolver.find_fee_sheet_templates()
            if not templates:
                raise RuntimeError("未找到费用表模板文件")

            template_path = templates[0]
            file_name = os.path.basename(template_path)
            name_part, ext = os.path.splitext(file_name)
            output_file_name = f"{dl_number}_{name_part}_FeeSheet_{timestamp}{ext}"
            output_path = os.path.join(self.output_dir, output_file_name)
            logger.info(f"费用表将保存到默认路径: {output_path}")

            return (output_path, self.output_dir, False)


