"""
测试方法默认值处理模块
处理特定测试项目的默认测试方法分配
"""

from src.core import logger


class TestMethodDefaults:
    """处理测试方法默认值的类"""
    
    # 定义测试项目到默认测试方法的映射
    DEFAULT_TEST_METHODS = {
        "examination": "EIA-364-18"
    }
    
    @classmethod
    def get_default_test_method(cls, test_item: str) -> str:
        """
        根据测试项目获取默认测试方法
        
        Args:
            test_item: 测试项目名称
            
        Returns:
            默认测试方法，如果没有定义则返回None
        """
        if not test_item:
            return None
            
        test_item_lower = test_item.lower().strip()
        
        # 遍历默认测试方法映射
        for key, default_method in cls.DEFAULT_TEST_METHODS.items():
            if key in test_item_lower:
                logger.debug(f"为测试项目'{test_item}'找到默认测试方法: {default_method}")
                return default_method
                
        logger.debug(f"测试项目'{test_item}'没有定义默认测试方法")
        return None
        
    @classmethod
    def should_apply_default(cls, test_item: str, current_method: str) -> bool:
        """
        判断是否应该应用默认测试方法
        
        Args:
            test_item: 测试项目名称
            current_method: 当前测试方法值
            
        Returns:
            是否应该应用默认测试方法
        """
        # 只有当测试项目匹配且当前测试方法为空时才应用默认值
        return (cls.get_default_test_method(test_item) is not None and 
                (not current_method or not current_method.strip()))