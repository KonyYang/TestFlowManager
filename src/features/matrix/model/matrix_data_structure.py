from typing import Dict, List, Any, Set, Tuple
from src.core.logger import logger
import re

class MatrixDataStructure:
    """
    统一的数据结构类，用于存储Matrix中提取的重要信息
    """
    
    def __init__(self):
        self.group_steps: Dict[str, List[Dict[str, Any]]] = {}
        self.group_sample_sizes: Dict[str, str] = {}
        self.group_col_indices: Dict[str, int] = {}
        self.dl_number: str = "DL-UNKNOWN"
        self.project_data_file_path: str = None
        
    def __str__(self):
        return f"MatrixDataStructure(dl_number={self.dl_number}, project_data_file_path={self.project_data_file_path})"
    
    def _clean_step_numbers(self, step_str: str) -> List[str]:
        """
        清理并提取步骤号，支持各种格式
        
        Args:
            step_str: 原始步骤字符串
            
        Returns:
            清理后的步骤号列表
        """
        if not step_str or not step_str.strip():
            return []
            
        # 保留数字、逗号、空格、星号、括号和字母
        # 先把中文逗号替换为英文逗号
        step_str = step_str.replace('，', ',')
        
        # 提取所有数字（支持带修饰符的数字，如1*、5(a)等）
        # 匹配模式: 数字后面可能跟星号、括号和字母
        pattern = r'(\d+)[*]?(?:$$[a-zA-Z]$$)?'
        matches = re.findall(pattern, step_str)
                
        return matches
    
    def _validate_step_sequence(self, steps: List[Dict[str, Any]], group_name: str) -> Tuple[bool, List[str]]:
        """
        验证步骤序列的有效性和连续性
        
        Args:
            steps: 步骤信息列表，包含StepNumber, Test等信息
            group_name: 组别名称
            
        Returns:
            (是否有效, 警告信息列表)
        """
        warnings = []
        if not steps:
            return True, warnings
            
        try:
            # 收集所有步骤号
            step_numbers = [int(step['StepNumber']) for step in steps]
            step_numbers.sort()
            
            # 检查重复（检查所有步骤号，而不仅仅是单个单元格内的）
            seen = set()
            duplicates = set()
            for step in step_numbers:
                if step in seen:
                    duplicates.add(str(step))
                else:
                    seen.add(step)
            
            if duplicates:
                warnings.append(f"组别 {group_name} 存在重复的步骤号: {', '.join(sorted(duplicates))}")
            
            # 检查连续性（可选警告）
            if step_numbers:
                expected = list(range(step_numbers[0], step_numbers[-1] + 1))
                missing = [str(x) for x in expected if x not in step_numbers]
                if missing:
                    warnings.append(f"组别 {group_name} 存在不连续的步骤号，缺少: {', '.join(missing)}")
                    
        except ValueError as e:
            warnings.append(f"组别 {group_name} 步骤号包含无效数字: {e}")
            
        return len(warnings) == 0, warnings
    
    def _clean_group_name(self, group_header: str) -> str:
        """
        清理组别名称，去除前后非数字或字母的符号，处理Group前缀
        
        Args:
            group_header: 原始组别表头
            
        Returns:
            清理后的组别名称
        """
        if not group_header or not group_header.strip():
            return ""
            
        # 去除前后空格
        cleaned = group_header.strip()
        
        # 如果以Group开头（不区分大小写），则去除Group前缀
        if cleaned.lower().startswith("group"):
            # 提取Group后的部分
            cleaned = cleaned[5:].strip()  # 去掉"Group"前缀（5个字符）
            
        # 去除前后的非字母数字字符
        # 使用正则表达式提取中间的字母数字组合
        match = re.search(r'[a-zA-Z0-9]+', cleaned)
        if match:
            cleaned = match.group(0)
            
        # 精简日志输出，移除详细的组别表头清理信息
        return cleaned
    
    def update_from_matrix(self, matrix_data: List[List[str]]) -> List[str]:
        """
        从Matrix数据中更新所有重要信息
        
        Args:
            matrix_data: Matrix数据
            
        Returns:
            警告信息列表
        """
        warnings = []
        
        try:
            # 获取表头行
            header_row = matrix_data[0] if matrix_data else []
            
            # 从第6列开始查找组别列（"1", "2", "3", ...），直到遇到"Notes"列
            start_col_index = 5  # 第6列（F列）开始
            
            # 查找所有组别列
            for col_index in range(start_col_index, len(header_row)):
                col_header = header_row[col_index] if col_index < len(header_row) else ""
                if col_header.lower() in ["notes"]:
                    # 遇到Notes列，停止查找
                    break
                    
                # 清理组别名称
                cleaned_group_name = self._clean_group_name(col_header)
                
                # 检查是否为有效组别列（数字或字母）
                if cleaned_group_name and (cleaned_group_name.isdigit() or cleaned_group_name.isalnum()):
                    self.group_col_indices[cleaned_group_name] = col_index
                    self.group_steps[cleaned_group_name] = []
                    
            
            logger.debug(f"共找到 {len(self.group_col_indices)} 个组别列")
            
            # 验证组别名称是否有重复
            group_names = list(self.group_col_indices.keys())
            seen_groups = set()
            duplicate_groups = set()
            for group_name in group_names:
                if group_name in seen_groups:
                    duplicate_groups.add(group_name)
                else:
                    seen_groups.add(group_name)
            
            if duplicate_groups:
                warnings.append(f"存在重复的组别名称: {', '.join(sorted(duplicate_groups))}")
            
            # 查找Sample size行索引
            sample_size_row_index = self._find_sample_size_row(matrix_data)
            
            # 遍历所有行，提取每个组别的测试项
            # 修改：在遇到"Sample"行时停止提取组别步骤
            for row_idx, row in enumerate(matrix_data):
                # 跳过表头行
                if row_idx == 0:
                    continue
                
                # 检查是否遇到"Sample"行，如果是则停止处理
                first_col_value = row[0] if len(row) > 0 else ""
                if first_col_value.lower().startswith("sample"):
                    # 遇到Sample行，停止提取组别步骤
                    break
                
                test_item = row[0] if len(row) > 0 else ""
                
                # 遍历所有组别列
                for group_name, col_index in self.group_col_indices.items():
                    # 获取原始列头用于查找
                    original_col_index = self.group_col_indices[group_name]
                    if original_col_index < len(row):
                        group_step = row[original_col_index]
                        
                        # 如果不是Sample size行且组别步骤不为空，则添加到对应组别中
                        if (row_idx != sample_size_row_index and 
                            group_step and group_step.strip()):
                            # 清理组别步骤数字 - 支持更复杂的格式
                            step_numbers = self._clean_step_numbers(group_step)
                            
                            # 添加测试项目信息
                            for step_number in step_numbers:
                                step_info = {
                                    "StepNumber": step_number,
                                    "Test": test_item,
                                    "TestMethod": row[2] if len(row) > 2 else "",
                                    "Condition": row[3] if len(row) > 3 else "",
                                    "Requirement": row[4] if len(row) > 4 else ""
                                }
                                self.group_steps[group_name].append(step_info)
                                
                                # 移除详细的测试项添加日志
            
            # 对每组内的步骤按键（步骤号，数值）升序排序
            all_steps = {}  # 用于验证连续性
            for group_name in self.group_steps.keys():
                self.group_steps[group_name].sort(key=lambda x: int(x['StepNumber']))
                # 移除详细的步骤排序日志
                
                # 收集所有步骤信息用于验证
                all_steps[group_name] = self.group_steps[group_name]
            
            # 验证步骤序列
            for group_name, steps in all_steps.items():
                is_valid, group_warnings = self._validate_step_sequence(steps, group_name)
                warnings.extend(group_warnings)
            
            # 如果找到了Sample size行，则收集各组别的样品数量
            if sample_size_row_index != -1 and sample_size_row_index < len(matrix_data):
                sample_size_row = matrix_data[sample_size_row_index]
                for group_name, col_index in self.group_col_indices.items():
                    if col_index < len(sample_size_row):
                        sample_size = sample_size_row[col_index]
                        self.group_sample_sizes[group_name] = sample_size
                        # 移除样品数量的详细日志
            elif len(matrix_data) >= 3:  # 至少要有3行才能检查倒数第三行
                # 如果没有找到Sample size行，添加警告信息
                warnings.append("未找到样品数量行（应包含'sample'关键字且位于表格末尾几行），请检查数据格式")
            
        except Exception as e:
            logger.error(f"Error extracting test data: {e}")
            warnings.append(f"数据提取过程中发生错误: {e}")
            
        return warnings

    def _find_sample_size_row(self, matrix_data: List[List[str]]) -> int:
        """
        查找Sample size行索引
        
        Args:
            matrix_data: Matrix数据
            
        Returns:
            Sample size行索引，如果未找到则返回-1
        """
        sample_size_row_index = -1
        
        # 优先查找严格匹配"sample size"的行
        for row_idx, row in enumerate(matrix_data):
            if row_idx == 0:  # 跳过表头行
                continue
            first_col_value = row[0] if len(row) > 0 else ""
            if first_col_value.lower() == "sample size":
                sample_size_row_index = row_idx
                # 移除找到严格匹配的Sample size行的详细日志
                return sample_size_row_index
        
        # 如果没有找到严格匹配的，查找包含"sample"关键字且位于末尾几行的行
        # 检查倒数第一、二、三行
        for i in range(1, min(4, len(matrix_data))):  # 检查最多前3行（倒数第1、2、3行）
            row_idx = len(matrix_data) - i
            if row_idx > 0 and row_idx < len(matrix_data):  # 确保不是表头行
                row = matrix_data[row_idx]
                first_col_value = row[0] if len(row) > 0 else ""
                # 检查是否包含"sample"关键字（不区分大小写）
                if "sample" in first_col_value.lower():
                    sample_size_row_index = row_idx
                    logger.info(f"找到包含'sample'关键字的行（倒数第{i}行），索引: {row_idx}")
                    return sample_size_row_index
        
        logger.info("未找到Sample size行")
        return sample_size_row_index
    
    def get_group_steps(self, group_name: str) -> List[Dict[str, Any]]:
        """
        获取指定组别的步骤信息
        
        Args:
            group_name: 组别名称
        
        Returns:
            步骤信息列表
        """
        return self.group_steps.get(group_name, [])
    
    def get_group_sample_size(self, group_name: str) -> str:
        """
        获取指定组别的样品数量
        
        Args:
            group_name: 组别名称
        
        Returns:
            样品数量字符串
        """
        return self.group_sample_sizes.get(group_name, "")
    
    def get_group_col_index(self, group_name: str) -> int:
        """
        获取指定组别的列索引
        
        Args:
            group_name: 组别名称
        
        Returns:
            列索引
        """
        return self.group_col_indices.get(group_name, -1)
    
    def print_debug_info(self) -> None:
        """
        打印调试信息，方便查看提取的数据
        """
        logger.info("=== Matrix Data Structure Debug Info ===")
        logger.info(f"Group Steps: {self.group_steps}")
        logger.info(f"Group Sample Sizes: {self.group_sample_sizes}")
        logger.info(f"Group Col Indices: {self.group_col_indices}")
        logger.info("=== End of Debug Info ===")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将数据结构转换为字典格式
        
        Returns:
            字典格式的数据
        """
        return {
            "group_steps": self.group_steps,
            "group_sample_sizes": self.group_sample_sizes,
            "group_col_indices": self.group_col_indices
        }