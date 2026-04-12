"""
启动性能监控工具
测量各个模块的导入时间,找出性能瓶颈
"""
import time
import sys
from pathlib import Path

def measure_import(name, import_func):
    """测量单个导入的时间"""
    start = time.time()
    try:
        import_func()
        elapsed = time.time() - start
        print(f"✅ {name:50s} {elapsed:.3f}s")
        return elapsed, True
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {name:50s} {elapsed:.3f}s (错误: {e})")
        return elapsed, False

def main():
    print("="*80)
    print("TestFlowManager 启动性能分析")
    print("="*80)
    print()
    
    total_time = 0
    results = []
    
    # 1. 核心模块
    print("📦 核心模块加载:")
    print("-"*80)
    
    t, ok = measure_import("配置管理器", lambda: __import__('src.core.config_manager', fromlist=['config_manager']))
    total_time += t
    results.append(("配置管理器", t, ok))
    
    t, ok = measure_import("日志系统", lambda: __import__('src.core.logger', fromlist=['logger']))
    total_time += t
    results.append(("日志系统", t, ok))
    
    t, ok = measure_import("事件分发器", lambda: __import__('src.core.event_dispatcher', fromlist=['event_dispatcher']))
    total_time += t
    results.append(("事件分发器", t, ok))
    
    print()
    
    # 2. 主窗口UI
    print("🖼️  主窗口UI加载:")
    print("-"*80)
    
    t, ok = measure_import("主窗口UI", lambda: __import__('src.features.main_window.view.main_window_ui', fromlist=['MainWindow']))
    total_time += t
    results.append(("主窗口UI", t, ok))
    
    print()
    
    # 3. 控制器(懒加载测试)
    print("🎮 控制器加载(首次访问):")
    print("-"*80)
    
    try:
        from src.features.main_window.view.main_window_ui import MainWindow
        
        # 模拟首次访问各个控制器
        t, ok = measure_import("客户报告控制器", 
            lambda: getattr(MainWindow(None), 'customer_report_controller', None))
        total_time += t
        results.append(("客户报告控制器", t, ok))
        
        t, ok = measure_import("报告向导控制器", 
            lambda: getattr(MainWindow(None), 'report_wizard_controller', None))
        total_time += t
        results.append(("报告向导控制器", t, ok))
        
        t, ok = measure_import("文档解析控制器", 
            lambda: getattr(MainWindow(None), 'document_parser_controller', None))
        total_time += t
        results.append(("文档解析控制器", t, ok))
        
    except Exception as e:
        print(f"⚠️  控制器测试跳过: {e}")
    
    print()
    
    # 4. Matrix组件
    print("📊 Matrix组件加载:")
    print("-"*80)
    
    t, ok = measure_import("Matrix项目控制器", 
        lambda: __import__('src.features.matrix.controller.matrix_project_controller', fromlist=['MatrixProjectController']))
    total_time += t
    results.append(("Matrix项目控制器", t, ok))
    
    print()
    
    # 5. 服务层
    print("⚙️  服务层加载:")
    print("-"*80)
    
    t, ok = measure_import("Matrix服务", 
        lambda: __import__('src.features.matrix.service.matrix_service', fromlist=['MatrixService']))
    total_time += t
    results.append(("Matrix服务", t, ok))
    
    print()
    
    # 汇总报告
    print("="*80)
    print("性能汇总报告")
    print("="*80)
    print()
    
    # 按耗时排序
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
    
    print(f"{'模块名称':<40s} {'耗时(秒)':>10s} {'占比':>8s} {'状态':>6s}")
    print("-"*80)
    
    for name, elapsed, ok in sorted_results:
        percentage = (elapsed / total_time * 100) if total_time > 0 else 0
        status = "✅" if ok else "❌"
        bar = "█" * int(percentage / 2)
        print(f"{name:<40s} {elapsed:>10.3f}s {percentage:>7.1f}% {status:>4s} {bar}")
    
    print("-"*80)
    print(f"{'总计':<40s} {total_time:>10.3f}s {'100.0%':>8s}")
    print()
    
    # 性能评估
    print("="*80)
    print("性能评估")
    print("="*80)
    
    if total_time < 0.5:
        print("🎉 优秀! 启动时间 < 0.5秒")
    elif total_time < 1.0:
        print("👍 良好! 启动时间 < 1.0秒")
    elif total_time < 2.0:
        print("⚠️  一般。启动时间 < 2.0秒,建议优化")
    else:
        print("🔴 较慢。启动时间 > 2.0秒,需要立即优化")
    
    print()
    
    # Top 3 慢模块
    top3 = sorted_results[:3]
    print("Top 3 最慢模块:")
    for i, (name, elapsed, _) in enumerate(top3, 1):
        print(f"  {i}. {name}: {elapsed:.3f}s ({elapsed/total_time*100:.1f}%)")
    
    print()
    print("="*80)
    
    return total_time

if __name__ == "__main__":
    # 添加到Python路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    startup_time = main()
    
    # 如果太慢,给出警告
    if startup_time > 1.0:
        print("\n💡 优化建议:")
        print("  1. 检查是否有不必要的顶层导入")
        print("  2. 考虑使用懒加载延迟初始化重型组件")
        print("  3. 运行 python -m compileall src/ 生成字节码缓存")
        sys.exit(1)
