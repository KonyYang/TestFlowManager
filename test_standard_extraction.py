import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.utils.standard_version_updater import extract_standard_identifier, extract_core_method, extract_version_letter

def test_extract_standard_identifier():
    """测试 extract_standard_identifier 函数"""
    print("测试 extract_standard_identifier 函数:")
    
    # 测试用例 1: 带版本号的标准
    test1 = "ANSI/EIA-364-18B-2007"
    result1 = extract_standard_identifier(test1)
    print(f"测试1: '{test1}' -> '{result1}' (期望: 'EIA-364-18B')")
    
    # 测试用例 2: 不带版本号但有年份的标准
    test2 = "ANSI/EIA-364-110-2006"
    result2 = extract_standard_identifier(test2)
    print(f"测试2: '{test2}' -> '{result2}' (期望: 'EIA-364-110-2006')")
    
    # 测试用例 3: 只有基本标准号
    test3 = "EIA-364-20F"
    result3 = extract_standard_identifier(test3)
    print(f"测试3: '{test3}' -> '{result3}' (期望: 'EIA-364-20F')")
    
    # 测试用例 4: 带前缀但无年份的标准
    test4 = "ANSI/EIA-364-18B"
    result4 = extract_standard_identifier(test4)
    print(f"测试4: '{test4}' -> '{result4}' (期望: 'EIA-364-18B')")
    
    # 测试用例 5: 不带前缀的标准
    test5 = "EIA-364-18B-2007"
    result5 = extract_standard_identifier(test5)
    print(f"测试5: '{test5}' -> '{result5}' (期望: 'EIA-364-18B')")

def test_extract_core_method():
    """测试 extract_core_method 函数"""
    print("\n测试 extract_core_method 函数:")
    
    test_cases = [
        "ANSI/EIA-364-18B-2007",
        "EIA-364-18B",
        "EIA-364-110-2006",
        "ANSI/EIA-364-20F-2019"
    ]
    
    for test in test_cases:
        result = extract_core_method(test)
        print(f"'{test}' -> '{result}'")

def test_extract_version_letter():
    """测试 extract_version_letter 函数"""
    print("\n测试 extract_version_letter 函数:")
    
    test_cases = [
        "ANSI/EIA-364-18B-2007",
        "EIA-364-18B",
        "EIA-364-110-2006",
        "ANSI/EIA-364-20F-2019"
    ]
    
    for test in test_cases:
        result = extract_version_letter(test)
        print(f"'{test}' -> '{result}'")

if __name__ == "__main__":
    test_extract_core_method()
    test_extract_version_letter()
    test_extract_standard_identifier()