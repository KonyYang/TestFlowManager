"""
标准版本更新工具模块
提供从外部标准文件中获取最新版本号并更新测试方法的功能
"""

import re
import os
import sys
from src.core.config_manager import config_manager
from src.core.logger import logger


class VersionComparator:
    """
    版本号比较器（纯逻辑，无外部依赖）
    
    负责从测试方法字符串中提取核心方法标识、版本字母，
    并进行版本比较和标准标识符提取。
    """
    
    @staticmethod
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
    
    @staticmethod
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
        core_method = VersionComparator.extract_core_method(method)
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
    
    @staticmethod
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
    
    @staticmethod
    def extract_standard_identifier(full_standard: str) -> str:
        """
        从完整标准号中提取标准标识符（如从"ANSI/EIA-364-18B-2007"提取"EIA-364-18B"）
        
        Args:
            full_standard (str): 完整的标准号字符串
            
        Returns:
            str: 提取的标准标识符
        """
        # 查找核心方法标识
        core_method = VersionComparator.extract_core_method(full_standard)
        if not core_method:
            return full_standard
        
        # 查找版本字母（如果存在）
        version_letter = VersionComparator.extract_version_letter(full_standard)
        
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


def extract_core_method(method: str) -> str:
    """
    从测试方法字符串中提取核心方法标识（如 364-xx 部分）
    
    注意：此函数为向后兼容保留，委托给 VersionComparator

    Args:
        method (str): 完整的测试方法字符串

    Returns:
        str: 提取到的核心方法标识，如果未找到则返回空字符串
    """
    return VersionComparator.extract_core_method(method)


def extract_version_letter(method: str) -> str:
    """
    从测试方法字符串中提取版本字母
    
    注意：此函数为向后兼容保留，委托给 VersionComparator

    Args:
        method (str): 完整的测试方法字符串

    Returns:
        str: 版本字母，如果未找到则返回空字符串
    """
    return VersionComparator.extract_version_letter(method)


def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本字母
    
    注意：此函数为向后兼容保留，委托给 VersionComparator

    Args:
        version1 (str): 第一个版本字母
        version2 (str): 第二个版本字母

    Returns:
        int: 如果version1 > version2返回1，相等返回0，小于返回-1
    """
    return VersionComparator.compare_versions(version1, version2)


def extract_standard_identifier(full_standard: str) -> str:
    """
    从完整标准号中提取标准标识符（如从"ANSI/EIA-364-18B-2007"提取"EIA-364-18B"）
    
    注意：此函数为向后兼容保留，委托给 VersionComparator
    
    Args:
        full_standard (str): 完整的标准号字符串
        
    Returns:
        str: 提取的标准标识符
    """
    return VersionComparator.extract_standard_identifier(full_standard)


def is_network_path(file_path: str) -> bool:
    """
    判断文件路径是否为网络路径（UNC路径）

    Args:
        file_path (str): 文件路径

    Returns:
        bool: 如果是网络路径返回True，否则返回False
    """
    # 检查是否为UNC路径（以\\开头）
    if file_path.startswith("\\\\"):
        return True
    
    # 检查是否为映射的网络驱动器（如Z:\path）
    # 通过检查驱动器根目录是否存在来判断
    if os.path.isabs(file_path):
        drive = os.path.splitdrive(file_path)[0]
        if drive:
            # 检查驱动器根目录是否存在
            try:
                drive_root = drive + "\\"
                if os.path.exists(drive_root):
                    # 尝试列出驱动器根目录的内容
                    os.listdir(drive_root)
                else:
                    return True  # 驱动器根目录不存在，可能是网络驱动器
            except (OSError, IOError):
                # 无法访问驱动器根目录，很可能是网络驱动器断开连接
                return True
    return False


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
            # 检查是否为网络路径且可能断开连接
            if is_network_path(file_path):
                logger.warning(f"网络路径文件不存在，可能是网络连接断开: {file_path}")
                return standards, False, True  # 返回标志，表示是网络路径且连接可能断开
            else:
                logger.warning(f"标准文件不存在: {file_path}")
                return standards, False, False  # 返回标志，表示文件不存在
            
        # 根据文件扩展名选择合适的解析器
        if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
            standards = _load_excel_standards(file_path)
        else:
            logger.warning(f"不支持的标准文件格式: {file_path}")
            
    except Exception as e:
        logger.error(f"加载标准文件时出错: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        
    return standards, True, False


def _load_excel_standards(file_path: str) -> dict:
    """
    从Excel文件加载标准数据

    Args:
        file_path (str): Excel文件路径

        dict: 标准数据字典
    """
    standards = {}
    
    try:
        # 在函数内部导入pandas，避免在PyInstaller打包的可执行文件中出现初始化冲突
        # 使用try-except块处理导入问题
        try:
            import pandas as pd
        except ImportError as e:
            logger.error(f"无法导入pandas库: {e}")
            return standards
        except RuntimeError as e:
            if "CPU dispatcher tracer already initlized" in str(e):
                logger.warning("检测到NumPy初始化冲突，尝试重新导入")
                try:
                    # 尝试重新导入
                    import importlib
                    import sys
                    # 清理可能存在的模块
                    modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith('numpy') or mod.startswith('pandas')]
                    for mod in modules_to_remove:
                        if mod in sys.modules:
                            del sys.modules[mod]
                    # 重新导入
                    import pandas as pd
                except Exception as reimport_error:
                    logger.error(f"重新导入pandas库失败: {reimport_error}")
                    # 尝试使用xlrd直接读取Excel文件作为备选方案
                    try:
                        logger.info("尝试使用xlrd作为备选方案读取Excel文件")
                        import xlrd
                        standards = _load_excel_with_xlrd(file_path)
                        return standards
                    except Exception as xlrd_error:
                        logger.error(f"使用xlrd读取Excel文件失败: {xlrd_error}")
                    return standards
            else:
                logger.error(f"导入pandas库时出现运行时错误: {e}")
                return standards
        except Exception as general_error:
            logger.error(f"导入pandas时出现未知错误: {general_error}")
            return standards
            
        # 从配置中获取工作表名称
        sheet_name = config_manager.get_standard_file("standard_version_sheet_name", "认可标准")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"标准文件不存在: {file_path}")
            return standards
            
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
        
        logger.info(f"总共加载了 {len(standards)} 个标准")
                        
    except Exception as e:
        logger.error(f"解析Excel标准文件时出错: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        
    return standards


def _load_excel_with_xlrd(file_path: str) -> dict:
    """
    使用xlrd库加载Excel文件作为备选方案

    Args:
        file_path (str): Excel文件路径

    Returns:
        dict: 标准数据字典
    """
    standards = {}
    try:
        import xlrd
        # 从配置中获取工作表名称
        sheet_name = config_manager.get_standard_file("standard_version_sheet_name", "认可标准")
        
        # 打开工作簿
        workbook = xlrd.open_workbook(file_path)
        # 获取工作表
        worksheet = workbook.sheet_by_name(sheet_name)
        
        # 从第3行开始遍历（索引为2），第2列（索引为1）是文件编号列
        for row_index in range(2, worksheet.nrows):
            # 获取第2列（索引为1）的值
            cell_value = worksheet.cell_value(row_index, 1)
            if cell_value:
                file_number_str = str(cell_value).strip()
                # 提取核心方法标识
                core_method = extract_core_method(file_number_str)
                if core_method:
                    # 只存储核心标准号，而不是完整单元格内容
                    standards[core_method] = file_number_str
        
        logger.info(f"使用xlrd总共加载了 {len(standards)} 个标准")
    except Exception as e:
        logger.error(f"使用xlrd解析Excel标准文件时出错: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        
    return standards



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
    file_exists = True  # 标记文件是否存在
    is_network_disconnect = False  # 标记是否为网络断开
    
    try:
        # 获取测试标准文件路径
        standard_file_path = config_manager.get_standard_file("standard_version_info_file")
        
        # 检查是否在可执行文件环境中，如果是，则尝试使用相对路径降级
        if getattr(sys, 'frozen', False):
            if standard_file_path and not os.path.exists(standard_file_path):
                exe_dir = os.path.dirname(sys.executable)
                # 使用 basename 提取文件名，避免绝对路径导致 join 无效
                filename = os.path.basename(standard_file_path)
                candidate = os.path.join(exe_dir, filename)
                if os.path.exists(candidate):
                    standard_file_path = candidate
                    logger.info(f"在exe目录下找到标准文件: {candidate}")
                else:
                    logger.warning(f"exe目录下也未找到标准文件: {candidate}")
        
        if not standard_file_path:
            # 再次尝试获取，确保没有遗漏
            standard_file_path = config_manager.get_standard_file("standard_version_info_file")
            if not standard_file_path:
                return {"updated_count": 0, "details": [], "file_exists": False, "file_path": standard_file_path}
            
        # 加载标准数据
        standards, file_exists, is_network_disconnect = load_standard_data(standard_file_path)
        
        if not file_exists:
            return {
                "updated_count": 0, 
                "details": [], 
                "file_exists": False, 
                "file_path": standard_file_path,
                "is_network_disconnect": is_network_disconnect
            }
            
        if not standards:
            return {"updated_count": 0, "details": [], "file_exists": True, "standards_loaded": False}
            
        # 查找"Test Method"列
        if len(matrix_data) == 0:
            return {"updated_count": 0, "details": []}
            
        # 假设第一行是表头
        header_row = matrix_data[0]
        test_method_col_index = -1
        
        for i, header in enumerate(header_row):
            if header == "Test Method":
                test_method_col_index = i
                break
                
        if test_method_col_index == -1:
            return {"updated_count": 0, "details": []}
            
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
                
                # 当前无版本，标准有版本，需要更新
                if not current_version and standard_version:
                    should_update = True
                # 两者都有版本，比较版本高低
                elif current_version and standard_version:
                    version_comparison = compare_versions(standard_version, current_version)
                    if version_comparison > 0:
                        # 标准版本更高，需要更新（升级）
                        should_update = True
                    elif version_comparison < 0:
                        # 当前版本更高，需要更新（降级）
                        should_update = True
                # 当前有版本号，标准无版本号
                elif current_version and not standard_version:
                    # 检查特殊情况：如果标准文件中包含年份信息，则需要替换为完整标准号
                    if "-" in full_standard and full_standard.count("-") >= 3:
                        should_update = True
                # 当前无版本号，标准也无版本号
                elif not current_version and not standard_version:
                    # 检查标准文件中是否包含额外信息（如年份）
                    if "-" in full_standard and full_standard.count("-") >= 3:
                        should_update = True
                
                if should_update:
                    # 更新测试方法
                    if "-" in full_standard and full_standard.count("-") >= 3:
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
                        "new_method": updated_method
                    })
                    
                    matrix_data[row_index][test_method_col_index] = updated_method
                    updated_count += 1
    except Exception as e:
        logger.error(f"更新测试方法版本时出错: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
    return {
        "updated_count": updated_count, 
        "details": update_details, 
        "file_exists": file_exists,
        "is_network_disconnect": is_network_disconnect
    }



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
    logger.info(f"成功更新 {result['updated_count']} 行")
    logger.info("更新后的数据:")
    for row in matrix_data:
        logger.info(row)
