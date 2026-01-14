"""
HeaderData 版本号递增功能测试
"""
import unittest
from src.features.report_wizard.model.header_data import HeaderData


class TestHeaderDataVersion(unittest.TestCase):
    """测试 HeaderData 版本号功能"""
    
    def test_default_version(self):
        """测试默认版本号"""
        header_data = HeaderData()
        self.assertEqual(header_data.version, "A")
    
    def test_from_json_default_version(self):
        """测试从JSON加载时的默认版本号"""
        json_data = {}
        header_data = HeaderData. from_json(json_data)
        self.assertEqual(header_data.version, "A")
    
    def test_increment_version_simple(self):
        """测试简单的版本号递增"""
        header_data = HeaderData(version="A")
        header_data.increment_version()
        self.assertEqual(header_data.version, "B")
        
        header_data.increment_version()
        self.assertEqual(header_data.version, "C")
    
    def test_increment_version_sequence(self):
        """测试版本号序列递增"""
        header_data = HeaderData()
        
        # 测试 A -> B -> C -> ... -> Z
        expected_sequence = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 
                           'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 
                           'U', 'V', 'W', 'X', 'Y', 'Z']
        
        for expected in expected_sequence:
            self.assertEqual(header_data.version, expected)
            header_data.increment_version()
    
    def test_increment_version_multicharacter(self):
        """测试多字符版本号递增"""
        header_data = HeaderData()
        
        # 递增到 'AA'
        for _ in range(26):  # A to Z
            header_data.increment_version()
        
        self.assertEqual(header_data.version, "AA")
        
        header_data.increment_version()
        self.assertEqual(header_data.version, "AB")
        
        header_data.increment_version()
        self.assertEqual(header_data.version, "AC")
    
    def test_increment_version_complex_sequence(self):
        """测试复杂版本号序列"""
        header_data = HeaderData(version="Z")
        header_data.increment_version()
        self.assertEqual(header_data.version, "AA")
        
        header_data.increment_version()
        self.assertEqual(header_data.version, "AB")
        
        header_data.increment_version()
        self.assertEqual(header_data.version, "AC")
        
        # 从 'AZ' 递增到 'BA'
        header_data.version = "AZ"
        header_data.increment_version()
        self.assertEqual(header_data.version, "BA")
        
        # 从 'ZZ' 递增到 'AAA'
        header_data.version = "ZZ"
        header_data.increment_version()
        self.assertEqual(header_data.version, "AAA")


if __name__ == '__main__':
    unittest.main()