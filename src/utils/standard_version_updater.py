"""
标准版本更新工具模块
提供从外部标准文件中获取最新版本号并更新测试方法的功能
"""

import re
import os
from src.core.config_manager import config_manager
from src.core.logger import logger


def extract_core_method(method: str) -> str:
    """
    从测试方法字符串中提取核心方法标识（如 364-xx 部分）

    Args:
        method (str): 完整的测试方法字符串

    Returns:
        str: 提取到的核心方法标识，如果未找到则返回空字符串
    """
    if not method:
        return ""
    
    # 使用正则表达式匹配 364-后跟两位数字的部分
    pattern = r"364-\d{2}"
    match = re.search(pattern, method, re.IGNORECASE)
    
    if match:
        return match.group(0)
    return ""


def extract_version_letter(method: str) -> str:
    """
    从测试方法字符串中提取版本字母

    Args:
        method (str): 完整的测试方法字符串

    Returns:
        str: 版本字母，如果未找到则返回空字符串
    """
    if not method:
        return ""
    
    # 查找核心方法标识后可能存在的版本字母
    core_method = extract_core_method(method)
    if core_method:
        # 在完整方法中查找核心方法标识的位置
        pos = method.find(core_method)
        if pos != -1:
            # 从核心方法标识后开始查找版本字母
            start_pos = pos + len(core_method)
            # 查找后面的字母
            for i in range(start_pos, len(method)):
                if method[i].isalpha():
                    return method[i]
    return ""


def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本字母

    Args:
        version1 (str): 第一个版本字母
        version2 (str): 第二个版本字母

    Returns:
        int: 如果version1 > version2返回1，相等返回0，小于返回-1
    """
    if version1 == version2:
        return 0
    elif version1 > version2:
        return 1
    else:
        return -1


def load_standard_data(file_path: str) -> dict:
    """
    从外部Excel文件加载标准数据

    Args:
        file_path (str): 标准文件路径

    Returns:
        dict: 标准数据字典，格式为 {core_method: full_standard}
    """
    standards = {}
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"标准文件不存在: {file_path}")
            return standards
            
        # 根据文件扩展名选择合适的解析器
        if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
            standards = _load_excel_standards(file_path)
        else:
            logger.warning(f"不支持的标准文件格式: {file_path}")
            
    except Exception as e:
        logger.error(f"加载标准文件时出错: {e}")
        
    return standards


def _load_excel_standards(file_path: str) -> dict:
    """
    从Excel文件加载标准数据

    Args:
        file_path (str): Excel文件路径

    Returns:
        dict: 标准数据字典
    """
    standards = {}
    
    try:
        import pandas as pd
        
        # 从配置中获取工作表名称
        sheet_name = config_manager.get("standard_files.standard_version_sheet_name", "认可标准")
        
        # 读取Excel文件中的指定工作表
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # 从第3行开始遍历（索引为2），第2列（索引为1）是文件编号列
        for index in range(2, len(df)):  # 从第3行开始（索引2）
            if len(df.columns) > 1 and index < len(df):
                file_number = df.iloc[index, 1]  # 第2列是文件编号
                if pd.notna(file_number):
                    file_number_str = str(file_number).strip()
                    # 提取核心方法标识
                    core_method = extract_core_method(file_number_str)
                    if core_method:
                        # 只存储核心标准号，而不是完整单元格内容
                        standards[core_method] = file_number_str
                        
    except Exception as e:
        logger.error(f"解析Excel标准文件时出错: {e}")
        
    return standards


def extract_standard_identifier(full_standard: str) -> str:
    """
    从完整标准号中提取标准标识符（如从"ANSI/EIA-364-18B-2007"提取"EIA-364-18B"）
    
    Args:
        full_standard (str): 完整的标准号字符串
        
    Returns:
        str: 提取的标准标识符
    """
    # 查找核心方法标识
    core_method = extract_core_method(full_standard)
    if not core_method:
        return full_standard
    
    # 查找版本字母（如果存在）
    version_letter = extract_version_letter(full_standard)
    
    # 查找"EIA"的位置
    eia_pos = full_standard.find("EIA")
    if eia_pos == -1:
        # 如果找不到"EIA"，使用核心方法标识的位置
        eia_pos = full_standard.find(core_method)
    
    # 如果没有版本字母，则返回到年份部分之前的部分
    if not version_letter:
        # 查找年份部分的位置（最后一个"-"之前的部分）
        last_hyphen_pos = full_standard.rfind("-")
        if eia_pos != -1 and last_hyphen_pos != -1 and last_hyphen_pos > eia_pos:
            # 特殊处理：如果标准号中包含年份信息，则保留年份
            # 例如："ANSI/EIA-364-110-2006" 应该提取为 "EIA-364-110-2006"
            return full_standard[eia_pos:]  # 返回从EIA开始的完整部分
        # 如果找不到明确的年份部分，返回从EIA开始的部分
        if eia_pos != -1:
            return full_standard[eia_pos:]
        return full_standard
    else:
        # 有版本字母，返回"EIA-364-XXY"格式的部分（不包含年份）
        # 找到版本字母结束的位置
        method_pos = full_standard.find(core_method)
        version_start = method_pos + len(core_method)
        version_end = version_start
        # 查找版本字母结束的位置
        for i in range(version_start, len(full_standard)):
            if full_standard[i].isalpha():
                # 找到版本字母后，继续查找直到非字母字符
                version_end = i + 1
                while version_end < len(full_standard) and full_standard[version_end].isalpha():
                    version_end += 1
                break
                
        # 返回从"EIA"开始到版本字母结束的部分
        if eia_pos != -1 and version_end > version_start:
            return full_standard[eia_pos:version_end]
    
    return full_standard


def update_test_method_versions(matrix_data: list) -> dict:
    """
    更新矩阵数据中的测试方法版本号

    Args:
        matrix_data (list): 矩阵数据，二维列表形式

    Returns:
        dict: 更新结果，包含更新数量和更新详情
    """
    updated_count = 0
    update_details = []
    
    try:
        # 获取测试标准文件路径
        logger.info("尝试从配置管理器获取标准文件路径")
        standard_file_path = config_manager.get("standard_files.standard_version_info_file")
        logger.info(f"从配置管理器获取到的标准文件路径: {standard_file_path}")
        
        # 获取工作表名称
        sheet_name = config_manager.get("standard_files.standard_version_sheet_name", "认可标准")
        logger.info(f"使用的Sheet名称: {sheet_name}")
        
        if not standard_file_path:
            logger.warning("未配置标准文件路径")
            # 再次尝试获取，确保没有遗漏
            standard_file_path = config_manager.get("standard_files.standard_version_info_file")
            logger.info(f"再次尝试获取标准文件路径: {standard_file_path}")
            if not standard_file_path:
                return {"updated_count": 0, "details": []}
            
        # 加载标准数据
        logger.info(f"尝试加载标准数据文件: {standard_file_path}")
        standards = load_standard_data(standard_file_path)
        logger.info(f"加载到的标准数据数量: {len(standards)}")
        
        if not standards:
            logger.warning("未加载到任何标准数据")
            return {"updated_count": 0, "details": []}
            
        # 查找"Test Method"列
        if len(matrix_data) == 0:
            logger.warning("矩阵数据为空")
            return {"updated_count": 0, "details": []}
            
        # 假设第一行是表头
        header_row = matrix_data[0]
        test_method_col_index = -1
        
        for i, header in enumerate(header_row):
            if header == "Test Method":
                test_method_col_index = i
                break
                
        if test_method_col_index == -1:
            logger.warning("未找到'Test Method'列")
            return {"updated_count": 0, "details": []}
            
        logger.info(f"找到'Test Method'列，索引为: {test_method_col_index}")
        logger.info(f"矩阵数据总行数: {len(matrix_data)}")
        
        # 打印C列的所有内容供调试
        c_column_contents = []
        for row_index in range(1, len(matrix_data)):
            row = matrix_data[row_index]
            if len(row) > test_method_col_index:
                c_column_contents.append((row_index, row[test_method_col_index]))
        
        logger.info(f"C列(Test Method列)内容: {c_column_contents}")
        logger.info(f"标准文件路径: {standard_file_path}")
            
        # 遍历数据行（从第2行开始，索引为1）
        for row_index in range(1, len(matrix_data)):
            row = matrix_data[row_index]
            
            # 确保行有足够的列
            if len(row) <= test_method_col_index:
                continue
                
            test_method = row[test_method_col_index].strip()
            
            # 跳过空行
            if not test_method:
                continue
                
            # 提取核心方法标识
            core_method = extract_core_method(test_method)
            if not core_method:
                continue
                
            logger.debug(f"处理第{row_index}行，测试方法: {test_method}，核心标识: {core_method}")
                
            # 查找匹配的标准
            if core_method in standards:
                full_standard = standards[core_method]
                
                # 从完整标准号中提取标准标识符
                standard_identifier = extract_standard_identifier(full_standard)
                
                # 检查是否需要更新版本
                current_version = extract_version_letter(test_method)
                standard_version = extract_version_letter(standard_identifier)
                
                # 如果标准文件中的版本更高，或者当前没有版本号，则更新
                should_update = False
                update_reason = ""
                
                # 当前无版本，标准有版本，需要更新
                if not current_version and standard_version:
                    should_update = True
                    update_reason = "补充版本号"
                # 两者都有版本，比较版本高低
                elif current_version and standard_version:
                    version_comparison = compare_versions(standard_version, current_version)
                    if version_comparison > 0:
                        # 标准版本更高，需要更新（升级）
                        should_update = True
                        update_reason = "升级版本"
                    elif version_comparison < 0:
                        # 当前版本更高，需要更新（降级）
                        should_update = True
                        update_reason = "降级版本"
                    # 如果版本相同，则不更新 (version_comparison == 0)
                # 当前有版本号，标准无版本号
                elif current_version and not standard_version:
                    # 检查特殊情况：如果标准文件中包含年份信息，则需要替换为完整标准号
                    if "-" in full_standard and full_standard.count("-") >= 3:
                        should_update = True
                        update_reason = "补充完整标准号"
                # 当前无版本号，标准也无版本号
                elif not current_version and not standard_version:
                    # 检查标准文件中是否包含额外信息（如年份）
                    if "-" in full_standard and full_standard.count("-") >= 3:
                        should_update = True
                        update_reason = "补充完整标准号"
                
                if should_update:
                    # 更新测试方法
                    if update_reason == "补充完整标准号":
                        # 特殊情况：使用完整标准号（包含年份）
                        updated_method = extract_standard_identifier(full_standard)
                    else:
                        # 一般情况：使用提取的标准标识符
                        updated_method = standard_identifier
                    
                    # 空格替换为短横线
                    updated_method = updated_method.replace(" ", "-")
                    
                    # 记录更新详情
                    update_details.append({
                        "row": row_index,
                        "old_method": test_method,
                        "new_method": updated_method,
                        "reason": update_reason
                    })
                    
                    matrix_data[row_index][test_method_col_index] = updated_method
                    updated_count += 1
                    logger.info(f"第{row_index}行测试方法更新成功: {test_method} -> {updated_method}")
                else:
                    # 版本相同或其他不需要更新的情况
                    if current_version and standard_version and current_version == standard_version:
                        logger.debug(f"第{row_index}行无需更新，当前版本与标准版本相同: {current_version}")
                    else:
                        logger.debug(f"第{row_index}行无需更新，当前版本已是最新或标准无更高版本")
            else:
                logger.debug(f"第{row_index}行未找到匹配标准，核心标识: {core_method}")
                    
    except Exception as e:
        logger.error(f"更新测试方法版本时出错: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
    logger.info(f"总共更新了 {updated_count} 行测试方法")
    return {"updated_count": updated_count, "details": update_details}


def _extract_version_symbol(full_standard: str, base_method: str) -> str:
    """
    从完整标准编号中提取版本符号

    Args:
        full_standard (str): 完整的标准编号
        base_method (str): 基础方法标识

    Returns:
        str: 版本符号，如果未找到则返回空字符串
    """
    try:
        # 查找基础方法在完整标准中的位置
        method_pos = full_standard.find(base_method)
        if method_pos == -1:
            return ""
            
        # 版本号开始位置
        version_start = method_pos + len(base_method)
        
        # 从版本号开始位置查找第一个字母
        for i in range(version_start, len(full_standard)):
            char = full_standard[i]
            if char.isalpha():
                return char
                
    except Exception as e:
        logger.error(f"提取版本符号时出错: {e}")
        
    return ""


# 示例用法
if __name__ == "__main__":
    # 示例数据
    matrix_data = [
        ["Test Items", "Section", "Test Method", "Condition", "Requirement"],
        ["", "", "EIA-364-01", "", ""],
        ["", "", "EIA-364-10", "", ""]
    ]
    
    # 更新版本号
    result = update_test_method_versions(matrix_data)
    print(f"成功更新 {result['updated_count']} 行")
    print("更新后的数据:")
    for row in matrix_data:
        print(row)