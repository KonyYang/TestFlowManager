"""简单测试 - 验证pytest框架是否正常工作"""
import pytest


class TestSimple:
    """简单测试类"""
    
    def test_simple_pass(self):
        """测试简单通过"""
        assert True
    
    def test_simple_math(self):
        """测试简单数学运算"""
        assert 1 + 1 == 2
    
    def test_string_operations(self):
        """测试字符串操作"""
        assert "hello".upper() == "HELLO"
    
    def test_list_operations(self):
        """测试列表操作"""
        my_list = [1, 2, 3]
        assert len(my_list) == 3
        assert 2 in my_list
