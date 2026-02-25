"""
Excel表格初始化模块
提供初始化Excel模板表格的功能
"""

import os
import glob
import shutil
from typing import Dict, Any
from src.core.logger import logger
from src.utils.excel_utils import get_shared_excel_app, release_excel_app


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
        # 确保输入路径为绝对路径
        template_dir = os.path.abspath(template_dir)
        target_folder = os.path.abspath(target_folder)

        logger.info(f"使用模板目录: {template_dir}")
        logger.info(f"目标文件夹: {target_folder}")

        # 查找模板文件
        logger.info(f"正在查找 'E-4243*.xlsx' 模板文件: {template_dir}")
        files = glob.glob(os.path.join(template_dir, "E-4243*.xlsx"))

        if not files:
            logger.warning("未找到以 'E-4243' 开头的 Excel 模板文件")
            return False

        logger.debug(f"找到模板文件: {files}")
        source_path = os.path.abspath(files[0])
        logger.debug(f"模板文件绝对路径: {source_path}")

        # 构建目标路径
        dest_path = os.path.abspath(os.path.join(target_folder, new_file_name))
        logger.debug(f"目标文件绝对路径: {dest_path}")

        # 确保目标路径存在
        os.makedirs(target_folder, exist_ok=True)

        logger.info(f"准备复制文件到: {dest_path}")

        try:
            shutil.copy2(source_path, dest_path)

            if not os.path.exists(dest_path):
                logger.error(f"文件未成功复制！目标路径不存在: {dest_path}")
                return False

            logger.info(f"客户反馈表已成功复制至: {dest_path}")

        except Exception as e:
            logger.error(f"文件复制失败: {e}", exc_info=True)
            return False

        # 等待片刻让系统准备好文件
        import time
        time.sleep(0.5)

        # 初始化 Excel 应用程序
        excel_app = get_shared_excel_app()
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

        try:
            wb = excel_app.Workbooks.Open(dest_path)
        except Exception as e:
            logger.error(f"无法打开 Excel 文件: {dest_path}，错误详情: {e}")
            return False

        if not wb:
            logger.error(f"未能加载工作簿: {dest_path}")
            return False

        # 列出所有工作表用于调试
        sheet_names = [sheet.Name for sheet in wb.Sheets]
        logger.debug(f"当前工作簿包含的工作表: {sheet_names}")

        # 检查目标工作表是否存在
        if "Customer Feedback Form" not in sheet_names:
            logger.error("未找到名为 'Customer Feedback Form' 的工作表")
            wb.Close(SaveChanges=False)
            release_excel_app()
            return False

        # 获取工作表
        try:
            ws = wb.Sheets("Customer Feedback Form")
        except Exception as e:
            logger.error(f"获取工作表失败: {e}")
            wb.Close(SaveChanges=False)
            release_excel_app()
            return False

        # 获取数据
        dl_number = application_data.get("DL", "")
        project_type = application_data.get("project_type", "")
        requested_by = application_data.get("requested_by", "")
        location = application_data.get("location", "")
        phone = application_data.get("phone", "")
        tests_to_be_performed = application_data.get("tests_to_be_performed", "")
        product_description = application_data.get("product_description", "")
        start_test_date = application_data.get("start_test_date", "")
        report_date = application_data.get("report_date", "")

        # 数据传输
        ws.Range("C7").Value = requested_by
        ws.Range("E7").Value = "'" + phone
        ws.Range("I7").Value = location
        ws.Range("C9").Value = f"{product_description} {tests_to_be_performed}"
        ws.Range("I9").Value = dl_number
        ws.Range("C11").Value = start_test_date
        ws.Range("E11").Value = report_date

        # 保存并关闭
        wb.Save()
        wb.Close(SaveChanges=False)
        release_excel_app()

        logger.info("✅ 客户反馈表已成功初始化")
        return True

    except Exception as e:
        logger.error(f"初始化客户反馈表时出错: {e}", exc_info=True)
        if 'wb' in locals():
            try:
                wb.Close(SaveChanges=False)
            except:
                pass
        if 'excel_app' in locals():
            release_excel_app()
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
        # 确保输入路径为绝对路径
        template_dir = os.path.abspath(template_dir)
        target_folder = os.path.abspath(target_folder)

        logger.info(f"使用模板目录: {template_dir}")
        logger.info(f"目标文件夹: {target_folder}")

        # 查找模板文件
        logger.info(f"正在查找 'Fee Evaluation' 类型的模板文件: {template_dir}")
        files = glob.glob(os.path.join(template_dir, "*Fee Evaluation*.xls*"))

        if not files:
            logger.warning("未找到与 'Fee Evaluation' 匹配的模板文件")
            return False

        logger.debug(f"找到模板文件: {files}")
        source_path = os.path.abspath(files[0])
        logger.debug(f"模板文件绝对路径: {source_path}")

        # 构建目标路径
        dest_path = os.path.abspath(os.path.join(target_folder, new_file_name))
        logger.debug(f"目标文件绝对路径: {dest_path}")

        # 确保目标路径存在
        os.makedirs(target_folder, exist_ok=True)

        logger.info(f"准备复制文件到: {dest_path}")

        try:
            shutil.copy2(source_path, dest_path)
            if not os.path.exists(dest_path):
                logger.error(f"文件未成功复制！目标路径不存在: {dest_path}")
                return False
            logger.info(f"费用评估表已成功复制至: {dest_path}")
        except Exception as e:
            logger.error(f"文件复制失败: {e}", exc_info=True)
            return False

        # 等待片刻让系统准备好文件
        import time
        time.sleep(0.5)

        # 初始化 Excel 应用程序
        excel_app = get_shared_excel_app()
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

        try:
            wb = excel_app.Workbooks.Open(dest_path)
        except Exception as e:
            logger.error(f"无法打开 Excel 文件: {dest_path}，错误详情: {e}")
            return False

        if not wb:
            logger.error(f"未能加载工作簿: {dest_path}")
            return False

        # 列出所有工作表用于调试
        sheet_names = [sheet.Name for sheet in wb.Sheets]
        logger.debug(f"当前工作簿包含的工作表: {sheet_names}")

        # 直接使用第一个工作表（与费用表生成逻辑保持一致）
        try:
            ws = wb.Sheets(1)
            logger.info(f"使用第一个工作表: {ws.Name}")
        except Exception as e:
            logger.error(f"获取第一个工作表失败: {e}")
            wb.Close(SaveChanges=False)
            release_excel_app()
            return False


        # 提取数据
        dl_number = application_data.get("DL", "")
        requested_by = application_data.get("requested_by", "")
        location = application_data.get("location", "")
        tests_to_be_performed = application_data.get("tests_to_be_performed", "")
        product_description = application_data.get("product_description", "")

        # 数据传输
        try:
            # 示例映射关系（请根据实际需求调整）
            ws.Range("D2").Value = dl_number
            ws.Range("G2").Value = f"{product_description} {tests_to_be_performed}"
            ws.Range("D3").Value = requested_by
            ws.Range("G3").Value = location

            logger.info("数据已成功写入费用评估表")
        except Exception as e:
            logger.error(f"写入 Excel 数据时出错: {e}", exc_info=True)
            wb.Close(SaveChanges=False)
            release_excel_app()
            return False

        # 保存并关闭
        wb.Save()
        wb.Close(SaveChanges=False)
        release_excel_app()

        logger.info("✅ 费用评估表已成功初始化")
        return True

    except Exception as e:
        logger.error(f"初始化费用评估表时出错: {e}", exc_info=True)
        if 'wb' in locals():
            try:
                wb.Close(SaveChanges=False)
            except:
                pass
        if 'excel_app' in locals():
            try:
                release_excel_app()
            except:
                pass
        return False