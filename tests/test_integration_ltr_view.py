"""
LTR编号查询界面测试模块
用于测试LTR编号查询界面的显示效果
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features.ltr_manager.view.ltr_viewer_dialog import LTRNumberCheckerView


class MockLTRViewerController:
    """
    模拟LTR控制器
    用于测试界面功能
    """

    def handle_search_ltr_number(self, dl_number: str) -> bool:
        """
        模拟处理搜索LTR编号的请求

        Args:
            dl_number: 要搜索的DL编号

        Returns:
            是否成功处理
        """
        print(f"模拟搜索DL编号: {dl_number}")
        # 模拟成功找到编号
        return True

    def save_ltr_data(self, data: dict) -> bool:
        """
        模拟保存LTR数据

        Args:
            data: 要保存的数据

        Returns:
            是否保存成功
        """
        print(f"模拟保存数据: {data}")
        # 模拟保存成功
        messagebox.showinfo("模拟保存", f"数据已保存:\n{data}")
        return True


def create_test_window():
    """
    创建测试窗口
    """
    # 创建主窗口
    root = tk.Tk()
    root.title("LTR编号查询界面测试")
    root.geometry("1000x700")

    # 创建LTR编号查询视图
    ltr_view = LTRNumberCheckerView(root)

    # 创建模拟控制器
    mock_controller = MockLTRViewerController()
    ltr_view.set_controller(mock_controller)

    # 将视图添加到主窗口
    main_frame = ltr_view.get_main_frame()
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 创建测试按钮框架
    test_frame = ttk.Frame(root)
    test_frame.pack(fill=tk.X, padx=10, pady=5)

    # 添加测试按钮
    def show_sample_data():
        """显示示例数据"""
        ltr_view.show_sample_data()
        messagebox.showinfo("提示", "示例数据已加载")

    def test_comparison_view():
        """测试对比视图"""
        new_data = {
            "DL": "DL-2025-001",
            "Project Type": "新产品测试",
            "Description P/N": "产品型号XYZ-123",
            "Test Item": "电气安全测试",
            "Test Type": "型式试验",
            "Requested by": "张三",
            "Location": "实验室A",
            "Project Leader": "李四",
        }

        existing_data = {
            "DL": "DL-2025-001",
            "Project Type": "旧产品测试",
            "Description P/N": "产品型号XYZ-123",
            "Test Item": "电气安全测试",
            "Test Type": "型式试验",
            "Requested by": "王五",
            "Location": "实验室A",
            "Project Leader": "赵六",
            "Test Result": "通过",
            "Finish Test Date": "2025-09-20"
        }

        ltr_view.update_comparison_data(new_data, existing_data)
        messagebox.showinfo("提示", "对比数据已加载\n可以双击第二列进行编辑")

    ttk.Button(test_frame, text="加载示例数据", command=show_sample_data).pack(side=tk.LEFT, padx=5)
    ttk.Button(test_frame, text="测试对比视图", command=test_comparison_view).pack(side=tk.LEFT, padx=5)

    # 设置窗口关闭事件
    def on_closing():
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    return root


def run_test():
    """
    运行测试
    """
    print("启动LTR编号查询界面测试...")
    print("窗口将在几秒钟内显示")
    print("功能说明:")
    print("1. 点击'加载示例数据'按钮可以加载示例数据")
    print("2. 点击'测试对比视图'按钮可以查看新旧数据对比")
    print("3. 双击第二列('申请编号或更新内容')可以编辑数据")
    print("4. 使用'保存修改'按钮可以保存编辑后的数据")
    print("5. 使用'重置'按钮可以恢复原始数据")
    print("关闭窗口以结束测试")

    try:
        # 创建测试窗口
        root = create_test_window()

        # 运行主循环
        root.mainloop()

        print("测试结束")

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_test()
