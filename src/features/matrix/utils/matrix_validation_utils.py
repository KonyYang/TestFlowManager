"""
Matrix验证工具模块
提供Matrix数据处理中常用的数据验证函数
"""

from typing import List, Dict, Any, Tuple


def validate_step_sequence(steps: List[Dict[str, Any]], group_name: str) -> Tuple[bool, List[str]]:
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