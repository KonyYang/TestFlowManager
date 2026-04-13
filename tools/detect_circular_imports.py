"""
循环依赖检测工具
扫描项目中的潜在循环导入风险
"""
import os
import sys
import ast
from collections import defaultdict
from pathlib import Path


class ImportAnalyzer:
    """导入关系分析器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.import_graph = defaultdict(set)
        self.risk_patterns = []
        
    def analyze_directory(self, target_dir: str = "src"):
        """分析指定目录的导入关系"""
        src_path = self.project_root / target_dir
        
        for py_file in src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            module_path = self._file_to_module(py_file)
            imports = self._extract_imports(py_file)
            
            for imported_module in imports:
                self.import_graph[module_path].add(imported_module)
                
        return self.import_graph
    
    def detect_cycles(self):
        """检测循环依赖"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.import_graph.get(node, set()):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path)
                    if cycle:
                        cycles.append(cycle)
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            path.pop()
            rec_stack.discard(node)
            return None
        
        for node in list(self.import_graph.keys()):
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def find_risky_patterns(self):
        """识别高风险模式"""
        risks = []
        
        # 模式 1: 双向导入
        for module_a, imports_a in self.import_graph.items():
            for module_b in imports_a:
                if module_a in self.import_graph.get(module_b, set()):
                    risks.append({
                        'type': 'bidirectional',
                        'modules': [module_a, module_b],
                        'severity': 'high'
                    })
        
        # 模式 2: 深层导入链（> 5层）
        for module, imports in self.import_graph.items():
            chain_length = self._get_import_chain_length(module)
            if chain_length > 5:
                risks.append({
                    'type': 'deep_chain',
                    'module': module,
                    'length': chain_length,
                    'severity': 'medium'
                })
        
        # 模式 3: 过度导入（单个文件导入 > 20个模块）
        for module, imports in self.import_graph.items():
            if len(imports) > 20:
                risks.append({
                    'type': 'excessive_imports',
                    'module': module,
                    'count': len(imports),
                    'severity': 'low'
                })
        
        return risks
    
    def _file_to_module(self, file_path: Path) -> str:
        """将文件路径转换为模块路径"""
        rel_path = file_path.relative_to(self.project_root)
        module_path = str(rel_path).replace(os.sep, '.').replace('.py', '')
        return module_path
    
    def _extract_imports(self, file_path: Path) -> set:
        """提取文件中的所有导入"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('src.'):
                            imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('src.'):
                        imports.add(node.module)
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
        
        return imports
    
    def _get_import_chain_length(self, module: str, visited=None) -> int:
        """计算导入链长度"""
        if visited is None:
            visited = set()
        
        if module in visited:
            return 0
        
        visited.add(module)
        max_length = 0
        
        for imported in self.import_graph.get(module, set()):
            length = self._get_import_chain_length(imported, visited)
            max_length = max(max_length, length)
        
        visited.discard(module)
        return max_length + 1
    
    def generate_report(self, output_file: str = "import_analysis_report.txt"):
        """生成分析报告"""
        cycles = self.detect_cycles()
        risks = self.find_risky_patterns()
        
        report_lines = [
            "=" * 80,
            "TestFlowManager 循环依赖检测报告",
            "=" * 80,
            "",
            f"项目根目录: {self.project_root}",
            f"分析的模块数: {len(self.import_graph)}",
            "",
            "-" * 80,
            "1. 循环依赖检测结果",
            "-" * 80,
        ]
        
        if cycles:
            report_lines.append(f"发现 {len(cycles)} 个循环依赖:\n")
            for i, cycle in enumerate(cycles, 1):
                report_lines.append(f"  循环 {i}: {' -> '.join(cycle)}")
        else:
            report_lines.append("✅ 未发现循环依赖")
        
        report_lines.extend([
            "",
            "-" * 80,
            "2. 高风险模式检测",
            "-" * 80,
        ])
        
        if risks:
            high_risks = [r for r in risks if r['severity'] == 'high']
            medium_risks = [r for r in risks if r['severity'] == 'medium']
            low_risks = [r for r in risks if r['severity'] == 'low']
            
            if high_risks:
                report_lines.append(f"\n🔴 高风险 ({len(high_risks)}):")
                for risk in high_risks:
                    if risk['type'] == 'bidirectional':
                        report_lines.append(
                            f"  - 双向导入: {risk['modules'][0]} <-> {risk['modules'][1]}"
                        )
            
            if medium_risks:
                report_lines.append(f"\n🟡 中风险 ({len(medium_risks)}):")
                for risk in medium_risks:
                    if risk['type'] == 'deep_chain':
                        report_lines.append(
                            f"  - 深层导入链: {risk['module']} (深度={risk['length']})"
                        )
            
            if low_risks:
                report_lines.append(f"\n🟢 低风险 ({len(low_risks)}):")
                for risk in low_risks:
                    if risk['type'] == 'excessive_imports':
                        report_lines.append(
                            f"  - 过度导入: {risk['module']} ({risk['count']}个导入)"
                        )
        else:
            report_lines.append("✅ 未发现高风险模式")
        
        report_lines.extend([
            "",
            "-" * 80,
            "3. 建议",
            "-" * 80,
        ])
        
        if not cycles and not risks:
            report_lines.append("✅ 项目导入结构良好，无需立即修复")
        else:
            report_lines.append("建议优先处理高风险问题，参考 docs/tasks/001-fix-circular-imports.md")
        
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # 使用 utf-8 编码输出到控制台
        import sys
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        print(report_content)
        return report_content


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    analyzer = ImportAnalyzer(str(project_root))
    
    print("开始分析导入关系...")
    analyzer.analyze_directory("src")
    
    print("\n生成报告...")
    analyzer.generate_report("docs/import_analysis_report.txt")
    
    print("\n✅ 分析完成，报告已保存到 docs/import_analysis_report.txt")
