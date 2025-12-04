import re

# 当前使用的EIA正则表达式
eia_pattern = r'EIA\s*[-\s]?\s*364\s*[-\s]?\s*(?=.*\d)[A-Z0-9]+'

test_cases = [
    "EIA 364-TP23",
    "EIA 364 TP 23", 
    "EIA-364-27D"
]

print("测试当前正则表达式:")
print(f"使用的正则表达式: {eia_pattern}")

for test_case in test_cases:
    match = re.search(eia_pattern, test_case, re.IGNORECASE)
    if match:
        print(f"✓ '{test_case}' 匹配成功: {match.group()}")
    else:
        print(f"✗ '{test_case}' 匹配失败")

print("\n分析问题...")

# 分析"EIA 364 TP 23"为什么匹配失败
# 问题在于正向先行断言(?=.*\d)检查的是整个匹配文本中是否有数字
# 但在实际匹配中，[A-Z0-9]+只匹配到"TP"，不包含数字，所以失败

print("\n尝试改进的正则表达式:")

# 改进的正则表达式 - 确保在标准标识符部分包含数字
improved_patterns = [
    r'EIA\s*[-\s]?\s*364\s*[-\s]?\s*[A-Z]*\d+[A-Z0-9]*',  # 数字必须在标识符中
    r'EIA\s*[-\s]?\s*364\s*[-\s]?\s*(?:[A-Z]*\d+[A-Z0-9]*|[A-Z]+\s*\d+)'  # 支持空格分隔的形式
]

for i, pattern in enumerate(improved_patterns, 1):
    print(f"\n测试改进模式 {i}: {pattern}")
    for test_case in test_cases:
        match = re.search(pattern, test_case, re.IGNORECASE)
        if match:
            print(f"✓ '{test_case}' 匹配成功: {match.group()}")
        else:
            print(f"✗ '{test_case}' 匹配失败")