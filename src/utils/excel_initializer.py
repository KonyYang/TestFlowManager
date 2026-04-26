"""
Excel表格初始化模块
提供初始化Excel模板表格的功能
"""

import os
import glob
import shutil
import time
from typing import Dict, Any
from src.core.logger import logger
from src.infrastructure.office.facade import OfficeFacade


def _prepare_template_copy(
    template_dir: str,
    target_folder: str,
    pattern: str,
    not_found_message: str,
    copy_success_message: str,
):
    """Resolve the source template and copy it into the target folder."""
    template_dir = os.path.abspath(template_dir)
    target_folder = os.path.abspath(target_folder)

    logger.info(f"使用模板目录: {template_dir}")
    logger.info(f"目标文件夹: {target_folder}")

    files = glob.glob(os.path.join(template_dir, pattern))
    if not files:
        logger.warning(not_found_message)
        return None

    logger.debug(f"找到模板文件: {files}")
    source_path = os.path.abspath(files[0])
    logger.debug(f"模板文件绝对路径: {source_path}")
    return template_dir, target_folder, source_path, copy_success_message


def _copy_template_to_target(source_path: str, target_folder: str, new_file_name: str) -> str | None:
    """Copy the selected template into the target folder and return the destination path."""
    dest_path = os.path.abspath(os.path.join(target_folder, new_file_name))
    logger.debug(f"目标文件绝对路径: {dest_path}")
    os.makedirs(target_folder, exist_ok=True)
    logger.info(f"准备复制文件到: {dest_path}")

    try:
        shutil.copy2(source_path, dest_path)
        if not os.path.exists(dest_path):
            logger.error(f"文件未成功复制！目标路径不存在: {dest_path}")
            return None
        return dest_path
    except Exception as e:
        logger.error(f"文件复制失败: {e}", exc_info=True)
        return None


def _write_customer_feedback_form(worksheet, application_data: Dict[str, Any]) -> None:
    """Populate the customer feedback worksheet with application data."""
    dl_number = application_data.get("DL", "")
    requested_by = application_data.get("requested_by", "")
    location = application_data.get("location", "")
    phone = application_data.get("phone", "")
    tests_to_be_performed = application_data.get("tests_to_be_performed", "")
    product_description = application_data.get("product_description", "")
    start_test_date = application_data.get("start_test_date", "")
    report_date = application_data.get("report_date", "")

    worksheet.Range("C7").Value = requested_by
    worksheet.Range("E7").Value = "'" + phone
    worksheet.Range("I7").Value = location
    worksheet.Range("C9").Value = f"{product_description} {tests_to_be_performed}"
    worksheet.Range("I9").Value = dl_number
    worksheet.Range("C11").Value = start_test_date
    worksheet.Range("E11").Value = report_date


def _populate_customer_feedback_form(dest_path: str, application_data: Dict[str, Any]) -> bool:
    """Open the copied workbook via OfficeFacade, update it, then save and release."""
    excel_session = None
    workbook = None

    try:
        excel_session = OfficeFacade().create_session("excel")
        runtime_handle = excel_session.acquire()
        excel_app = runtime_handle.application
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

        try:
            workbook = excel_app.Workbooks.Open(dest_path)
        except Exception as e:
            logger.error(f"无法打开 Excel 文件: {dest_path}，错误详情: {e}")
            return False

        if not workbook:
            logger.error(f"未能加载工作簿: {dest_path}")
            return False

        sheet_names = [sheet.Name for sheet in workbook.Sheets]
        logger.debug(f"当前工作簿包含的工作表: {sheet_names}")

        if "Customer Feedback Form" not in sheet_names:
            logger.error("未找到名为 'Customer Feedback Form' 的工作表")
            return False

        try:
            worksheet = workbook.Sheets("Customer Feedback Form")
        except Exception as e:
            logger.error(f"获取工作表失败: {e}")
            return False

        _write_customer_feedback_form(worksheet, application_data)
        workbook.Save()
        logger.info("✅ 客户反馈表已成功初始化")
        return True
    except Exception as e:
        logger.error(f"初始化客户反馈表时出错: {e}", exc_info=True)
        return False
    finally:
        try:
            if workbook:
                workbook.Close(SaveChanges=False)
        except Exception as e:
            logger.warning(f"关闭Excel工作簿时出错: {e}")
        try:
            if excel_session is not None:
                excel_session.release()
        except Exception as e:
            logger.warning(f"释放Excel session时出错: {e}")


def _write_fee_evaluation_form(worksheet, application_data: Dict[str, Any]) -> None:
    """Populate the fee evaluation worksheet with application data."""
    dl_number = application_data.get("DL", "")
    requested_by = application_data.get("requested_by", "")
    location = application_data.get("location", "")
    tests_to_be_performed = application_data.get("tests_to_be_performed", "")
    product_description = application_data.get("product_description", "")

    worksheet.Range("D2").Value = dl_number
    worksheet.Range("G2").Value = f"{product_description} {tests_to_be_performed}"
    worksheet.Range("D3").Value = requested_by
    worksheet.Range("G3").Value = location


def _populate_fee_evaluation_form(dest_path: str, application_data: Dict[str, Any]) -> bool:
    """Open the copied fee workbook via OfficeFacade, update it, then save and release."""
    excel_session = None
    workbook = None

    try:
        excel_session = OfficeFacade().create_session("excel")
        runtime_handle = excel_session.acquire()
        excel_app = runtime_handle.application
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

        try:
            workbook = excel_app.Workbooks.Open(dest_path)
        except Exception as e:
            logger.error(f"无法打开 Excel 文件: {dest_path}，错误详情: {e}")
            return False

        if not workbook:
            logger.error(f"未能加载工作簿: {dest_path}")
            return False

        sheet_names = [sheet.Name for sheet in workbook.Sheets]
        logger.debug(f"当前工作簿包含的工作表: {sheet_names}")

        try:
            worksheet = workbook.Sheets(1)
            logger.info(f"使用第一个工作表: {worksheet.Name}")
        except Exception as e:
            logger.error(f"获取第一个工作表失败: {e}")
            return False

        _write_fee_evaluation_form(worksheet, application_data)
        logger.info("数据已成功写入费用评估表")
        workbook.Save()
        logger.info("✅ 费用评估表已成功初始化")
        return True
    except Exception as e:
        logger.error(f"初始化费用评估表时出错: {e}", exc_info=True)
        return False
    finally:
        try:
            if workbook:
                workbook.Close(SaveChanges=False)
        except Exception as e:
            logger.warning(f"关闭Excel工作簿时出错: {e}")
        try:
            if excel_session is not None:
                excel_session.release()
        except Exception as e:
            logger.warning(f"释放Excel session时出错: {e}")


def initialize_customer_feedback_form(template_dir: str, target_folder: str, new_file_name: str, 
                                      application_data: Dict[str, Any]) -> bool:
    """
    初始化客户反馈表（Customer Feedback Form）

    Args:
        template_dir: 模板文件目录路径
        target_folder: 目标文件夹路径
        new_file_name: 新文件名
        application_data: 应用数据字典

    Returns:
        初始化是否成功
    """
    try:
        logger.info(f"正在查找 'E-4243*.xlsx' 模板文件: {template_dir}")
        prepared = _prepare_template_copy(
            template_dir,
            target_folder,
            "E-4243*.xlsx",
            "未找到以 'E-4243' 开头的 Excel 模板文件",
            "客户反馈表已成功复制至",
        )
        if prepared is None:
            return False

        _, target_folder, source_path, copy_success_message = prepared
        dest_path = _copy_template_to_target(source_path, target_folder, new_file_name)
        if dest_path is None:
            return False
        logger.info(f"{copy_success_message}: {dest_path}")

        time.sleep(0.5)
        return _populate_customer_feedback_form(dest_path, application_data)

    except Exception as e:
        logger.error(f"初始化客户反馈表时出错: {e}", exc_info=True)
        return False


def initialize_fee_evaluation_form(template_dir: str, target_folder: str, new_file_name: str, 
                                   application_data: Dict[str, Any]) -> bool:
    """
    初始化费用评估表（Fee Evaluation Form）

    Args:
        template_dir: 模板文件目录路径
        target_folder: 目标文件夹路径
        new_file_name: 新文件名
        application_data: 应用数据字典

    Returns:
        初始化是否成功
    """
    try:
        logger.info(f"正在查找 'Fee Evaluation' 类型的模板文件: {template_dir}")
        prepared = _prepare_template_copy(
            template_dir,
            target_folder,
            "*Fee Evaluation*.xls*",
            "未找到与 'Fee Evaluation' 匹配的模板文件",
            "费用评估表已成功复制至",
        )
        if prepared is None:
            return False

        _, target_folder, source_path, copy_success_message = prepared
        dest_path = _copy_template_to_target(source_path, target_folder, new_file_name)
        if dest_path is None:
            return False
        logger.info(f"{copy_success_message}: {dest_path}")

        time.sleep(0.5)
        return _populate_fee_evaluation_form(dest_path, application_data)

    except Exception as e:
        logger.error(f"初始化费用评估表时出错: {e}", exc_info=True)
        return False
