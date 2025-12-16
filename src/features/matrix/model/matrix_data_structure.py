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
        self._is_parsed = False  # 添加解析状态标志
        
    def __str__(self):
        return f"MatrixDataStructure(dl_number={self.dl_number}, project_data_file_path={self.project_data_file_path})"
    
    # ==================== 数据解析与结构化方法 ====================
    
    def parse_matrix_to_structure(self, matrix_data: List[List[str]]) -> List[str]:
        """
        将Matrix原始数据解析并重构为结构化字典数据
        
        Args:
            matrix_data: 原始Matrix数据
            
        Returns:
            警告信息列表
        """
        # 检查是否已经解析过，避免重复解析
        if self._is_parsed:
            logger.debug("Matrix数据已解析过，跳过重复解析")
            return []
            
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
            
            # 查找样本大小行索引
            sample_size_row_index = find_sample_size_row(matrix_data)
            
            # 重构组步骤信息
            self._restructure_group_steps(matrix_data, sample_size_row_index)
            
            # 验证步骤序列
            all_steps = {}
            for group_name in self.group_steps.keys():
                all_steps[group_name] = self.group_steps[group_name]
                
            # 验证步骤序列
            for group_name, steps in all_steps.items():
                is_valid, group_warnings = validate_step_sequence(steps, group_name)
                warnings.extend(group_warnings)
            
            # 收集样本大小
            sample_size_warnings = self._collect_sample_sizes(matrix_data, sample_size_row_index)
            warnings.extend(sample_size_warnings)
            
            # 标记为已解析
            self._is_parsed = True
            
        except Exception as e:
            logger.error(f"Error extracting test data: {e}")
            warnings.append(f"数据提取过程中发生错误: {e}")
            
        return warnings

    # ==================== 内部辅助方法 ====================
    
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

    # 该方法已被新的 _restructure_group_steps 方法替代
    # 保留空实现以防止其他地方调用时报错
    def _extract_test_items(self, matrix_data: List[List[str]], sample_size_row_index: int) -> None:
        """
        从Matrix数据中提取测试项（已废弃）
        
        Args:
            matrix_data: Matrix数据
            sample_size_row_index: 样本大小行索引
        """
        pass

    def _restructure_group_steps(self, matrix_data: List[List[str]], sample_size_row_index: int) -> None:
        """
        重构各测试组别的步骤内容信息
        
        功能包括：
        1. 对每组内的步骤按键（步骤号，数值）升序排序
        2. 处理包含"Initial"和"After test"关键字的步骤，根据规则重新赋值StepDescription和requirement
        
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
            
            # 检查是否遇到"Sample"行，如果是则停止提取组别步骤
            first_col_value = row[0] if len(row) > 0 else ""
            if first_col_value.lower().startswith("sample"):
                # 遇到Sample行，停止提取组别步骤
                break
            
            # 安全地提取当前行视为一个一行多列的列表，第一列作为测试项，如果行为空则使用空字符串
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
                            
        # 对每组内的步骤按键（步骤号，数值）升序排序，并处理Initial/After test逻辑
        for group_name in self.group_steps.keys():
            # 按步骤号排序
            self.group_steps[group_name].sort(key=lambda x: int(x['StepNumber']))
            
            # 处理包含Initial和After test的步骤
            self._process_initial_after_test_steps(group_name)

    def _process_initial_after_test_steps(self, group_name: str) -> None:
        """
        处理组内包含"Initial"和"After test"关键字的步骤
        
        根据需求，处理以下三种情况：
        1. 只有一个步骤包含Initial和After test：提取中间内容作为Initial requirement
        2. 两个步骤：第一个为Initial，第二个为Final
        3. 多个步骤：第一个为Initial，最后一个为Final，中间为After + 前一个步骤描述
        
        注意：只有当多个测试项的"Test"关键字相同时才会被组合在一起处理
        
        Args:
            group_name: 组别名称
        """
        group_steps = self.group_steps[group_name]
        # logger.info(f"开始处理组 '{group_name}' 中包含 'Initial' 和 'After test' 的步骤")
        
        # 按Test关键字分组，只处理相同Test关键字的步骤
        test_groups = {}
        for i, step in enumerate(group_steps):
            requirement = step.get("Requirement", "")
            test_item = step.get("Test", "")
            # 规范化文本以忽略大小写和多余符号
            normalized_req = normalize_text(requirement).lower()
            
            if "initial" in normalized_req and "after test" in normalized_req:
                if test_item not in test_groups:
                    test_groups[test_item] = []
                test_groups[test_item].append(i)
                # logger.debug(f"找到同时包含 'Initial' 和 'After test' 的步骤，索引: {i}, Test: {test_item}, Requirement: {requirement}")
        
        # 分别处理每个Test组
        for test_item, combined_steps in test_groups.items():
            # 如果没有同时包含Initial和After test的步骤，直接跳过
            if not combined_steps:
                # logger.info(f"组 '{group_name}' 中Test '{test_item}' 未找到同时包含 'Initial' 和 'After test' 的步骤")
                continue
                
            # 获取第一个步骤的requirement并拆分
            first_step_index = combined_steps[0]
            requirement = group_steps[first_step_index].get("Requirement", "")
            # logger.info(f"第一个步骤的Requirement: {requirement}")
            
            # 使用正则表达式查找"Initial"和"After test"（忽略大小写）
            initial_pattern = re.compile(r'(initial[\s:]*)', re.IGNORECASE)
            after_test_pattern = re.compile(r'(after\s*test[\s:]*)', re.IGNORECASE)
            
            # 查找Initial的位置
            initial_match = initial_pattern.search(requirement)
            # 查找After test的位置
            after_test_match = after_test_pattern.search(requirement)
            
            initial_requirement = ""
            after_test_requirement = ""
            
            if initial_match and after_test_match:
                # 确保Initial在After test之前
                if initial_match.start() < after_test_match.start():
                    # 提取Initial部分的requirement（Initial和After test之间）
                    initial_start = initial_match.end()
                    initial_end = after_test_match.start()
                    initial_requirement = requirement[initial_start:initial_end].strip()
                    # 提取":"和";"之间的内容
                    initial_requirement = self._extract_between_separators(initial_requirement, ":", ";")
                    
                    # 提取After test部分的requirement（After test之后的内容）
                    after_test_start = after_test_match.end()
                    after_test_requirement = requirement[after_test_start:].strip()
                    # 提取"After test:"到结尾的内容
                    after_test_requirement = self._extract_from_colon_to_end(after_test_requirement)
                    
                    # logger.info(f"Initial requirement: '{initial_requirement}'")
                    # logger.info(f"After test requirement: '{after_test_requirement}'")
            else:
                logger.warning("Could not find both Initial and After test in requirement text")
                continue
                
            # 根据步骤数量处理不同情况
            step_count = len(combined_steps)
            
            if step_count == 1:
                # 情况1：只有一个步骤
                step = group_steps[combined_steps[0]]
                step["Requirement"] = initial_requirement
                step["StepDescription"] = "Initial " + test_item
                # logger.info(f"处理单一步骤，索引: {combined_steps[0]}, 描述更新为: {step['StepDescription']}, 要求: {step['Requirement']}")
                
            elif step_count == 2:
                # 情况2：两个步骤
                # 第一个步骤 - Initial
                step1 = group_steps[combined_steps[0]]
                step1["Requirement"] = initial_requirement
                step1["StepDescription"] = "Initial " + test_item
                # logger.info(f"处理第一个步骤，索引: {combined_steps[0]}, 描述更新为: {step1['StepDescription']}, 要求: {step1['Requirement']}")
                
                # 第二个步骤 - Final
                step2 = group_steps[combined_steps[1]]
                step2["Requirement"] = after_test_requirement
                step2["StepDescription"] = "Final " + test_item
                # logger.info(f"处理第二个步骤，索引: {combined_steps[1]}, 描述更新为: {step2['StepDescription']}, 要求: {step2['Requirement']}")
                
            else:
                # 情况3：多个步骤
                # 第一个步骤 - Initial
                first_step = group_steps[combined_steps[0]]
                first_step["Requirement"] = initial_requirement
                first_step["StepDescription"] = "Initial " + test_item
                # logger.info(f"处理第一个步骤，索引: {combined_steps[0]}, 描述更新为: {first_step['StepDescription']}, 要求: {first_step['Requirement']}")
                
                # 最后一个步骤 - Final
                last_step = group_steps[combined_steps[-1]]
                last_step["Requirement"] = after_test_requirement
                last_step["StepDescription"] = "Final " + test_item
                # logger.info(f"处理最后一个步骤，索引: {combined_steps[-1]}, 描述更新为: {last_step['StepDescription']}, 要求: {last_step['Requirement']}")
                
                # 中间步骤 - After + 前一个步骤的描述
                for i in range(1, len(combined_steps) - 1):
                    step_index = combined_steps[i]
                    step = group_steps[step_index]
                    step["Requirement"] = after_test_requirement
                    
                    # 获取前一个步骤的描述（在整个group_steps中的前一个步骤，而不是在combined_steps中的前一个）
                    prev_step_index = step_index - 1
                    if prev_step_index >= 0:
                        prev_step_description = group_steps[prev_step_index].get("StepDescription", 
                                                                               group_steps[prev_step_index].get("Test", ""))
                    else:
                        # 如果没有前一个步骤，则使用默认值
                        prev_step_description = test_item
                    step["StepDescription"] = "After " + prev_step_description
                    # logger.info(f"处理第{i+1}个步骤，索引: {step_index}, 描述更新为: {step['StepDescription']}, 要求: {step['Requirement']}")

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

    def _extract_between_separators(self, text: str, start_sep: str, end_sep: str) -> str:
        """
        提取两个分隔符之间的内容
        
        Args:
            text: 原始文本
            start_sep: 起始分隔符
            end_sep: 结束分隔符
            
        Returns:
            提取出的内容
        """
        # 查找起始分隔符
        start_pos = text.find(start_sep)
        # 查找结束分隔符
        end_pos = text.find(end_sep)
        
        if start_pos != -1 and end_pos != -1:
            # 如果两个分隔符都存在，且起始分隔符在结束分隔符之前
            if start_pos < end_pos:
                # 提取两个分隔符之间的内容
                result = text[start_pos + len(start_sep):end_pos]
                return result.strip()
            else:
                # 如果起始分隔符在结束分隔符之后，只提取到结束分隔符之前的内容
                result = text[:end_pos]
                return result.strip()
        elif start_pos != -1:
            # 如果只有起始分隔符存在，提取其后所有内容
            result = text[start_pos + len(start_sep):]
            return result.strip()
        elif end_pos != -1:
            # 如果只有结束分隔符存在，提取到结束分隔符之前的内容
            result = text[:end_pos]
            return result.strip()
        else:
            # 如果两个分隔符都不存在，返回原文本
            return text.strip()

    def _extract_from_colon_to_end(self, text: str) -> str:
        """
        提取从冒号(:)到文本结尾的内容，并清理多余空格
        
        Args:
            text: 原始文本
            
        Returns:
            提取并清理后的内容
        """
        # 查找冒号位置
        colon_pos = text.find(':')
        if colon_pos != -1:
            # 如果找到冒号，提取其后内容
            result = text[colon_pos + 1:].strip()
        else:
            # 如果没找到冒号，返回原文本并清理
            result = text.strip()
            
        # 清理多余的空格和换行符
        result = " ".join(result.split())
        return result

    # ==================== 数据访问方法 ====================
    
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
    
    def get_test_data_for_export(self, group_name: str, filter_func=None) -> Dict[str, Any]:
        """
        获取用于导出的测试数据
        
        Args:
            group_name: 组别名称
            filter_func: 过滤函数，接受一个step字典作为参数，返回布尔值决定是否包含该步骤
                        如果为None则返回所有测试数据
            
        Returns:
            包含step_dict、sample_size和column_index的字典
        """
        if group_name not in self.group_steps:
            return {}
            
        # 构造step_dict，键为步骤号，值为步骤描述
        step_dict = {}
        for step in self.group_steps[group_name]:
            # 如果提供了过滤函数，则使用它来决定是否包含该步骤
            if filter_func and not filter_func(step):
                continue
            
            step_number = step.get("StepNumber", "")
            step_description = step.get("StepDescription", step.get("Test", ""))
            if step_number:
                step_dict[step_number] = step_description
                
        return {
            "step_dict": step_dict,
            "sample_size": self.group_sample_sizes.get(group_name, ""),
            "column_index": self.group_col_indices.get(group_name, -1)
        }