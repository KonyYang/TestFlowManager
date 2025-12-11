from typing import Dict, List, Any, Set, Tuple
from src.core.logger import logger
import re
from src.utils.string_utils import normalize_text
from src.features.matrix.utils.matrix_text_utils import clean_step_numbers, clean_group_name
from src.features.matrix.utils.matrix_validation_utils import validate_step_sequence
from src.features.matrix.utils.matrix_parsing_utils import find_sample_size_row

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
    
    def _update_initial_after_test_steps(self, group_steps: List[Dict[str, Any]]) -> None:
        """
        更新包含 "Initial" 和 "After test" 的步骤
        
        Args:
            group_steps: 组内的步骤列表
        """
        logger.info("开始处理包含 'Initial' 和 'After test' 的步骤")
        
        # 查找包含Initial或After test的步骤
        initial_steps = []
        after_test_steps = []
        
        for i, step in enumerate(group_steps):
            requirement = step.get("Requirement", "")
            # 规范化文本以忽略大小写和多余符号
            normalized_req = normalize_text(requirement).lower()
            
            # 检查是否包含initial（忽略大小写）
            if "initial" in normalized_req and "after test" not in normalized_req:
                initial_steps.append(i)
                logger.debug(f"找到包含 'Initial' 的步骤，索引: {i}, Requirement: {requirement}")
                
            # 检查是否包含after test（忽略大小写）
            if "after test" in normalized_req and "initial" not in normalized_req:
                after_test_steps.append(i)
                logger.debug(f"找到包含 'After test' 的步骤，索引: {i}, Requirement: {requirement}")
                
        # 查找同时包含Initial和After test的步骤
        combined_steps = []
        for i, step in enumerate(group_steps):
            requirement = step.get("Requirement", "")
            # 规范化文本以忽略大小写和多余符号
            normalized_req = normalize_text(requirement).lower()
            
            if "initial" in normalized_req and "after test" in normalized_req:
                combined_steps.append(i)
                logger.debug(f"找到同时包含 'Initial' 和 'After test' 的步骤，索引: {i}, Requirement: {requirement}")

        logger.info(f"Initial步骤索引: {initial_steps}")
        logger.info(f"After test步骤索引: {after_test_steps}")
        logger.info(f"组合步骤索引: {combined_steps}")
        
        # 如果既没有initial也没有after test，直接返回
        if not initial_steps and not after_test_steps and not combined_steps:
            logger.info("未找到包含 'Initial' 或 'After test' 的步骤")
            return
            
        # 处理只有initial或只有after test的情况
        if initial_steps and not after_test_steps and not combined_steps:
            # 只有initial的情况 - 只处理第一个initial步骤
            # 使用正则表达式查找"Initial"（忽略大小写）
            initial_pattern = re.compile(r'(initial[:\s]*)', re.IGNORECASE)
            
            first_initial_index = initial_steps[0]
            step = group_steps[first_initial_index]
            requirement = step.get("Requirement", "")
            # 查找Initial的位置
            initial_match = initial_pattern.search(requirement)
            initial_requirement = ""
            
            if initial_match:
                # 提取Initial部分的requirement
                initial_start = initial_match.end()
                initial_requirement = requirement[initial_start:].strip()
                # 清理多余的空格和换行符
                initial_requirement = " ".join(initial_requirement.split())
                # 更新Requirement字段
                step["Requirement"] = initial_requirement
                
            original_description = step.get("StepDescription", step.get("Test", ""))
            step["StepDescription"] = "Initial " + original_description
            logger.info(f"处理仅有 'Initial' 的情况，步骤索引: {first_initial_index}, 描述更新为: {step['StepDescription']}")
            return
            
        if after_test_steps and not initial_steps and not combined_steps:
            # 只有after test的情况 - 处理所有after test步骤，参考组合步骤中处理after步骤的逻辑
            # 使用正则表达式查找"After test"（忽略大小写）
            after_test_pattern = re.compile(r'(after\s*test[:\s]*)', re.IGNORECASE)
            
            for i, step_index in enumerate(after_test_steps):
                step = group_steps[step_index]
                requirement = step.get("Requirement", "")
                # 查找After test的位置
                after_test_match = after_test_pattern.search(requirement)
                after_test_requirement = ""
                
                if after_test_match:
                    # 提取After test部分的requirement
                    after_test_start = after_test_match.end()
                    after_test_requirement = requirement[after_test_start:].strip()
                    # 清理多余的空格和换行符
                    after_test_requirement = " ".join(after_test_requirement.split())
                    # 更新Requirement字段
                    step["Requirement"] = after_test_requirement
                    
                if i == len(after_test_steps) - 1:
                    # 最后一个步骤 - Final
                    original_description = step.get("StepDescription", step.get("Test", ""))
                    step["StepDescription"] = "Final " + original_description
                    logger.info(f"处理最后一个 'After test' 步骤，步骤索引: {step_index}, 描述更新为: {step['StepDescription']}")
                else:
                    # 中间步骤 - 获取前一个步骤的描述
                    prev_step_index = step_index - 1
                    if prev_step_index >= 0:
                        prev_step_description = group_steps[prev_step_index].get("StepDescription", 
                                                                               group_steps[prev_step_index].get("Test", ""))
                    else:
                        prev_step_description = "Unknown"
                        
                    step["StepDescription"] = "After " + prev_step_description
                    logger.info(f"处理第{i}个 'After test' 步骤，步骤索引: {step_index}, 描述更新为: {step['StepDescription']}")
            return
            
        # 处理同时包含Initial和After test的步骤
        if combined_steps:
            # 获取第一个步骤的requirement并拆分
            first_step_index = combined_steps[0]
            requirement = group_steps[first_step_index].get("Requirement", "")
            logger.info(f"第一个步骤的Requirement: {requirement}")
            
            # 使用正则表达式查找"Initial"和"After test"（忽略大小写）
            initial_pattern = re.compile(r'(initial[:\s]*)', re.IGNORECASE)
            after_test_pattern = re.compile(r'(after\s*test[:\s]*)', re.IGNORECASE)
            
            # 查找Initial的位置
            initial_match = initial_pattern.search(requirement)
            # 查找After test的位置
            after_test_match = after_test_pattern.search(requirement)
            
            initial_requirement = ""
            after_test_requirement = ""
            
            if initial_match and after_test_match:
                # 确保Initial在After test之前
                if initial_match.start() < after_test_match.start():
                    # 提取Initial部分的requirement
                    initial_start = initial_match.end()
                    initial_end = after_test_match.start()
                    initial_requirement = requirement[initial_start:initial_end].strip()
                    
                    # 提取After test部分的requirement
                    after_test_start = after_test_match.end()
                    after_test_requirement = requirement[after_test_start:].strip()
                    
                    # 清理多余的空格和换行符
                    initial_requirement = " ".join(initial_requirement.split())
                    after_test_requirement = " ".join(after_test_requirement.split())
                    
                    logger.info(f"Initial requirement: '{initial_requirement}'")
                    logger.info(f"After test requirement: '{after_test_requirement}'")
                else:
                    logger.warning("Initial should come before After test in requirement text")
                    return
            else:
                logger.warning("Could not find both Initial and After test in requirement text")
                return
                
            # 遍历这些步骤并进行修改
            for i, step_index in enumerate(combined_steps):
                step = group_steps[step_index]
                step_num = int(step["StepNumber"])
                
                if i == 0:
                    # 第一个步骤 - Initial
                    original_description = step.get("StepDescription", step.get("Test", ""))
                    step["StepDescription"] = "Initial " + original_description
                    step["Requirement"] = initial_requirement
                    logger.info(f"更新第{i}个步骤({step_index})为Initial步骤，描述: {step['StepDescription']}, 要求: {step['Requirement']}")
                elif i == len(combined_steps) - 1:
                    # 最后一个步骤 - After test
                    original_description = step.get("StepDescription", step.get("Test", ""))
                    step["StepDescription"] = "Final " + original_description
                    step["Requirement"] = after_test_requirement
                    logger.info(f"更新第{i}个步骤({step_index})为Final步骤，描述: {step['StepDescription']}, 要求: {step['Requirement']}")
                else:
                    # 中间步骤 - 获取前一个步骤的描述
                    prev_step_index = step_index - 1
                    if prev_step_index >= 0:
                        prev_step_description = group_steps[prev_step_index].get("StepDescription", 
                                                                               group_steps[prev_step_index].get("Test", ""))
                    else:
                        prev_step_description = "Unknown"
                        
                    step["StepDescription"] = "After " + prev_step_description
                    step["Requirement"] = after_test_requirement
                    logger.info(f"更新第{i}个步骤({step_index})为After步骤，描述: {step['StepDescription']}, 要求: {step['Requirement']}")

    def _extract_group_columns(self, header_row: List[str]) -> None:
        """
        从表头行中提取组别列信息
        
        Args:
            header_row: 表头行数据
        """
        # 从第6列开始查找组别列（"1", "2", "3", ...），直到遇到"Notes"列
        start_col_index = 5  # 第6列（F列）开始
        
        # 查找所有组别列
        for col_index in range(start_col_index, len(header_row)):
            col_header = header_row[col_index] if col_index < len(header_row) else ""
            if col_header.lower() in ["notes"]:
                # 遇到Notes列，停止查找
                break
                
            # 清理组别名称
            cleaned_group_name = clean_group_name(col_header)
            
            # 检查是否为有效组别列（数字或字母）
            if cleaned_group_name and (cleaned_group_name.isdigit() or cleaned_group_name.isalnum()):
                self.group_col_indices[cleaned_group_name] = col_index
                self.group_steps[cleaned_group_name] = []

    def _process_sample_size(self, matrix_data: List[List[str]]) -> int:
        """
        处理样本大小行
        
        Args:
            matrix_data: Matrix数据
            
        Returns:
            样本大小行索引
        """
        # 查找Sample size行索引
        sample_size_row_index = find_sample_size_row(matrix_data)
        return sample_size_row_index

    def _extract_test_items(self, matrix_data: List[List[str]], sample_size_row_index: int) -> None:
        """
        从Matrix数据中提取测试项
        
        Args:
            matrix_data: Matrix数据
            sample_size_row_index: 样本大小行索引
        """
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
                        step_numbers = clean_step_numbers(group_step)
                        
                        # 添加测试项目信息
                        for step_number in step_numbers:
                            step_info = {
                                "StepNumber": step_number,
                                "Test": test_item,
                                "TestMethod": row[2] if len(row) > 2 else "",
                                "Condition": row[3] if len(row) > 3 else "",
                                "Requirement": row[4] if len(row) > 4 else "",
                                "StepDescription": test_item  # 默认值为test_item
                            }
                            self.group_steps[group_name].append(step_info)

    def _validate_and_sort_steps(self) -> List[str]:
        """
        验证并排序步骤
        
        Returns:
            警告信息列表
        """
        warnings = []
        
        # 对每组内的步骤按键（步骤号，数值）升序排序
        all_steps = {}  # 用于验证连续性
        for group_name in self.group_steps.keys():
            self.group_steps[group_name].sort(key=lambda x: int(x['StepNumber']))
            
            # 更新包含Initial和After test的步骤
            self._update_initial_after_test_steps(self.group_steps[group_name])
            
            # 收集所有步骤信息用于验证
            all_steps[group_name] = self.group_steps[group_name]
        
        # 验证步骤序列
        for group_name, steps in all_steps.items():
            is_valid, group_warnings = validate_step_sequence(steps, group_name)
            warnings.extend(group_warnings)
            
        return warnings

    def _collect_sample_sizes(self, matrix_data: List[List[str]], sample_size_row_index: int) -> List[str]:
        """
        收集样本大小信息
        
        Args:
            matrix_data: Matrix数据
            sample_size_row_index: 样本大小行索引
            
        Returns:
            警告信息列表
        """
        warnings = []
        
        # 如果找到了Sample size行，则收集各组别的样品数量
        if sample_size_row_index != -1 and sample_size_row_index < len(matrix_data):
            sample_size_row = matrix_data[sample_size_row_index]
            for group_name, col_index in self.group_col_indices.items():
                if col_index < len(sample_size_row):
                    sample_size = sample_size_row[col_index]
                    self.group_sample_sizes[group_name] = sample_size
        elif len(matrix_data) >= 3:  # 至少要有3行才能检查倒数第三行
            # 如果没有找到Sample size行，添加警告信息
            warnings.append("未找到样品数量行（应包含'sample'关键字且位于表格末尾几行），请检查数据格式")
            
        return warnings

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
            
            # 提取组别列
            self._extract_group_columns(header_row)
            
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
            
            # 处理样本大小
            sample_size_row_index = self._process_sample_size(matrix_data)
            
            # 提取测试项
            self._extract_test_items(matrix_data, sample_size_row_index)
            
            # 验证并排序步骤
            validation_warnings = self._validate_and_sort_steps()
            warnings.extend(validation_warnings)
            
            # 收集样本大小
            sample_size_warnings = self._collect_sample_sizes(matrix_data, sample_size_row_index)
            warnings.extend(sample_size_warnings)
            
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

    def get_all_groups(self):
        """
        获取所有组别名称
        
        Returns:
            list: 所有组别名称列表
        """
        return list(self.group_steps.keys())
    
    def get_test_data_for_export(self, group_name: str) -> Dict[str, Any]:
        """
        获取用于导出的测试数据
        
        Args:
            group_name: 组别名称
            
        Returns:
            包含step_dict、sample_size和column_index的字典
        """
        if group_name not in self.group_steps:
            return {}
            
        # 构造step_dict，键为步骤号，值为步骤描述
        step_dict = {}
        for step in self.group_steps[group_name]:
            step_number = step.get("StepNumber", "")
            step_description = step.get("StepDescription", step.get("Test", ""))
            if step_number:
                step_dict[step_number] = step_description
                
        return {
            "step_dict": step_dict,
            "sample_size": self.group_sample_sizes.get(group_name, ""),
            "column_index": self.group_col_indices.get(group_name, -1)
        }

    def extract_llcr_groups_and_steps(self) -> Dict[str, int]:
        """
        提取包含"LLCR"的组别及对应的步骤数量
        
        Returns:
            Dict[str, int]: 键为组别名称，值为该组别包含的步骤数量
        """
        llcr_groups = {}
        
        # 遍历所有组别
        for group_name in self.get_all_groups():
            steps = self.get_group_steps(group_name)
            
            # 检查该组别中是否包含任何与LLCR相关的步骤
            llcr_step_count = 0
            for step in steps:
                # 检查Test、TestMethod、Requirement等字段是否包含LLCR
                if any("LLCR" in str(step.get(field, "")) for field in ["Test", "TestMethod", "Requirement", "StepDescription"]):
                    llcr_step_count += 1
                    
            # 如果该组别包含LLCR相关步骤，则添加到结果中
            if llcr_step_count > 0:
                llcr_groups[group_name] = llcr_step_count
                
        return llcr_groups
    
    def print_llcr_groups_info(self):
        """
        打印包含LLCR的组别信息
        """
        llcr_groups = self.extract_llcr_groups_and_steps()
        
        if not llcr_groups:
            print("未找到包含LLCR的组别")
            return
            
        print("包含LLCR的组别信息:")
        print("-" * 30)
        for group_name, step_count in llcr_groups.items():
            print(f"组别 {group_name}: {step_count} 个LLCR步骤")
        print("-" * 30)
        print(f"总共找到 {len(llcr_groups)} 个包含LLCR的组别")

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