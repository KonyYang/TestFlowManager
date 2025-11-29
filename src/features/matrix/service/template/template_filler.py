"""
模板填充服务模块
专门处理Matrix表格中的Condition和Requirement模板填充
"""

from src.core import logger
from src.utils.template_data import get_condition_requirement_templates, get_template_aliases


class TemplateFiller:
    """处理模板填充的类"""
    
    def __init__(self):
        """初始化模板填充器"""
        self.templates = get_condition_requirement_templates()
        self.aliases = get_template_aliases()
    
    def fill_condition_requirement_templates(self, data_model, row_index, test_item, 
                                          condition_col_index, requirement_col_index):
        """
        根据测试项目填充Condition和Requirement模板数据
        
        Args:
            data_model: 数据模型
            row_index: 行索引
            test_item: 测试项目名称
            condition_col_index: Condition列索引
            requirement_col_index: Requirement列索引
            
        Returns:
            bool: 是否成功填充
        """
        logger.debug(f"开始为第{row_index}行填充模板数据，Test Item: '{test_item}'")
        
        # 查找匹配的模板
        condition, requirement = self._find_template_match(test_item)
        if condition and requirement:
            # 填充Condition列
            if condition_col_index < len(data_model.rows[row_index]):
                data_model.rows[row_index][condition_col_index] = condition
                logger.debug(f"为第{row_index}行填充Condition: '{condition}'")
            else:
                logger.warning(f"Condition列索引超出范围，无法填充第{row_index}行")
                return False
            
            # 填充Requirement列
            if requirement_col_index < len(data_model.rows[row_index]):
                data_model.rows[row_index][requirement_col_index] = requirement
                logger.debug(f"为第{row_index}行填充Requirement: '{requirement}'")
            else:
                logger.warning(f"Requirement列索引超出范围，无法填充第{row_index}行")
                return False
            
            logger.debug(f"为第{row_index}行填充模板数据完成: {test_item} -> ({condition}, {requirement})")
            return True
        else:
            logger.debug(f"未找到第{row_index}行Test Item '{test_item}' 的匹配模板")
            return False
    
    def _find_template_match(self, test_item):
        """
        根据测试项目查找匹配的模板数据
        
        Args:
            test_item: 测试项目名称
            
        Returns:
            tuple: (condition, requirement) 或 (None, None)
        """
        test_item_lower = test_item.lower().strip()
        logger.debug(f"查找模板匹配: '{test_item}' (标准化为: '{test_item_lower}')")
        
        # 直接匹配
        for key, (condition, requirement) in self.templates.items():
            if key.lower() == test_item_lower:
                logger.debug(f"直接匹配成功: '{test_item}' -> '{key}'")
                return condition, requirement
        
        # 别名匹配
        for main_key, alias_list in self.aliases.items():
            if main_key in self.templates:
                for alias in alias_list:
                    if alias.lower() in test_item_lower or test_item_lower in alias.lower():
                        logger.debug(f"别名匹配成功: '{test_item}' -> '{main_key}' (通过别名: '{alias}')")
                        return self.templates[main_key]
        
        # 模糊匹配
        for key, (condition, requirement) in self.templates.items():
            if key.lower() in test_item_lower or test_item_lower in key.lower():
                logger.debug(f"模糊匹配成功: '{test_item}' -> '{key}'")
                return condition, requirement
        
        logger.debug(f"未找到匹配的模板: '{test_item}'")
        return None, None