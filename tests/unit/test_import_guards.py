"""
导入规范守卫测试
确保不会引入新的循环依赖和反模式

注意：此测试不依赖任何项目 fixture，可以独立运行
"""
import ast
import sys
from pathlib import Path

# 确保 src 在路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


class TestImportGuards:
    """导入规范守卫"""
    
    SRC_ROOT = Path(__file__).parent.parent.parent / "src"
    
    def test_no_wildcard_imports(self):
        """禁止通配符导入"""
        violations = []
        
        for py_file in self.SRC_ROOT.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == '*':
                            violations.append(
                                f"{py_file.relative_to(self.SRC_ROOT)}:"
                                f"{node.lineno}: from {node.module} import *"
                            )
        
        assert not violations, (
            f"发现 {len(violations)} 处通配符导入:\n" + 
            "\n".join(violations)
        )
    
    def test_no_deep_import_chains(self):
        """限制导入链深度（警告级别）"""
        from tools.detect_circular_imports import ImportAnalyzer
        
        analyzer = ImportAnalyzer(str(project_root))
        analyzer.analyze_directory("src")
        risks = analyzer.find_risky_patterns()
        
        deep_chains = [r for r in risks if r['type'] == 'deep_chain']
        
        # 允许一定数量的深层链，但不应过多
        # 当前基线：63个（修复LTR循环后从64降至63）
        # 目标：持续优化，最终降至 < 50
        assert len(deep_chains) < 70, (
            f"深层导入链过多: {len(deep_chains)} 个（当前基线 63，目标 < 50）\n"
            f"前 10 个: {[c['module'] for c in deep_chains[:10]]}"
        )
    
    def test_no_circular_dependencies(self):
        """禁止循环依赖"""
        from tools.detect_circular_imports import ImportAnalyzer
        
        analyzer = ImportAnalyzer(str(project_root))
        analyzer.analyze_directory("src")
        cycles = analyzer.detect_cycles()
        
        assert not cycles, (
            f"发现 {len(cycles)} 个循环依赖:\n" +
            "\n".join([f"  循环 {i+1}: {' -> '.join(cycle)}" 
                      for i, cycle in enumerate(cycles)])
        )
    
    def test_type_checking_usage_in_services(self):
        """Service 模块应使用 TYPE_CHECKING 隔离 UI 导入"""
        warnings = []
        
        for py_file in self.SRC_ROOT.rglob("*.py"):
            # 只检查 service 和 core 模块
            if 'service' not in str(py_file) and 'core' not in str(py_file):
                continue
            
            # 跳过测试文件
            if py_file.name.startswith("test_"):
                continue
            
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 如果导入了 PyQt 但没有使用 TYPE_CHECKING，发出警告
            if ('from PyQt5' in content or 'from PySide2' in content):
                if 'TYPE_CHECKING' not in content:
                    warnings.append(str(py_file.relative_to(self.SRC_ROOT)))
        
        # 这只是警告，不强制失败
        if warnings:
            print(f"\n⚠️  建议在这些非 UI 模块中使用 TYPE_CHECKING:\n" + 
                  "\n".join(f"  - {v}" for v in warnings[:10]))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
