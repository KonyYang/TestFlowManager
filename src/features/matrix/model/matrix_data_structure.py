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
            
            # 从第6列开始查找组别列（"1", "2", "3", ...），直到遇到"Remark"或"Notes"列
            start_col_index = 5  # 第6列（F列）开始
            
            # 查找所有组别列
            for col_index in range(start_col_index, len(header_row)):
                col_header = header_row[col_index] if col_index < len(header_row) else ""
                if col_header.lower() in ["remark", "notes"]:
                    # 遇到Remark或Notes列，停止查找
                    break
                    
                # 检查是否为组别列（数字）
                if col_header.isdigit():
                    self.group_col_indices[col_header] = col_index
                    self.group_steps[col_header] = []
                    logger.info(f"发现组别列: {col_header} (列索引: {col_index})")
            
            logger.info(f"共找到 {len(self.group_col_indices)} 个组别列: {list(self.group_col_indices.keys())}")
            
            # 遍历所有行，提取每个组别的测试项
            sample_size_row_index = -1
            for row_idx, row in enumerate(matrix_data):
                # 跳过表头行
                if row_idx == 0:
                    continue
                
                # 检查是否为Sample size行
                first_col_value = row[0] if len(row) > 0 else ""
                if first_col_value.lower() == "sample size":
                    sample_size_row_index = row_idx
                    logger.info("遇到Sample size行，记录行索引")
                    # 不在这里break，继续处理完所有行
                
                test_item = row[0] if len(row) > 0 else ""
                
                # 遍历所有组别列
                for group_name, col_index in self.group_col_indices.items():
                    if col_index < len(row):
                        group_step = row[col_index]
                        
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
                                
                                logger.debug(f"向组别{group_name}添加测试项: {test_item}, 步骤号: {step_number}")
            
            # 对每组内的步骤按键（步骤号，数值）升序排序
            all_steps = {}  # 用于验证连续性
            for group_name in self.group_steps.keys():
                self.group_steps[group_name].sort(key=lambda x: int(x['StepNumber']))
                logger.info(f"组别 {group_name} 的步骤已按步骤号排序")
                
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
                        logger.info(f"组别 {group_name} 的样品数量: {sample_size}")
            
        except Exception as e:
            logger.error(f"Error extracting test data: {e}")
            warnings.append(f"数据提取过程中发生错误: {e}")
            
        return warnings
            
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