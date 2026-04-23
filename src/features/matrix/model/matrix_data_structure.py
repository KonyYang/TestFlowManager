from typing import Dict, List, Any, Set, Tuple
from src.core.logger import logger
from src.features.matrix.utils.matrix_text_utils import clean_group_name
from src.features.matrix.utils.matrix_validation_utils import validate_step_sequence
from src.features.matrix.utils.matrix_parsing_utils import find_sample_size_row
from src.features.matrix.model.matrix_group_step_restructure_service import (
    MatrixGroupStepRestructureService,
)

class MatrixDataStructure:
    """
    统一的数据结构类，用于存储Matrix中提取的重要信息
    
    职责：
    - 状态容器（group_steps / group_sample_sizes / group_col_indices / LLCR/CR 需求）
    - parse_matrix_to_structure() 编排入口
    - _extract_group_columns() 列提取
    - _collect_sample_sizes() 样本大小收集
    - 公共 query 方法
    """
    
    def __init__(self):
        self.group_steps: Dict[str, List[Dict[str, Any]]] = {}
        self.group_sample_sizes: Dict[str, str] = {}
        self.group_col_indices: Dict[str, int] = {}
        self.dl_number: str = "DL-UNKNOWN"
        self.project_data_file_path: str = None
        self._is_parsed = False  # 添加解析状态标志
        self.llcr_requirements = []  # 添加LLCR需求列表
        self.cr_requirements = []    # 添加CR需求列表
        self._restructure_service = MatrixGroupStepRestructureService()
        
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
            
            # 重构组步骤信息 — 委托给重构服务
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

    def _restructure_group_steps(self, matrix_data: List[List[str]], sample_size_row_index: int) -> None:
        """
        重构各测试组别的步骤内容信息 — 委托给 MatrixGroupStepRestructureService

        Args:
            matrix_data: Matrix数据
            sample_size_row_index: 样本大小行索引
        """
        result = self._restructure_service.restructure_group_steps(
            matrix_data, self.group_col_indices, sample_size_row_index
        )
        self.group_steps = result["group_steps"]
        self.llcr_requirements = result["llcr_requirements"]
        self.cr_requirements = result["cr_requirements"]

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
    
    def get_llcr_requirements(self) -> List[str]:
        """
        获取所有LLCR测试项的Requirement内容
        
        Returns:
            list: LLCR需求列表
        """
        return self.llcr_requirements

    def get_cr_requirements(self) -> List[str]:
        """
        获取所有CR测试项的Requirement内容
        
        Returns:
            list: CR需求列表
        """
        return self.cr_requirements
