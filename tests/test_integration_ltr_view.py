"""
LTR编号查询界面测试模块
用于测试LTR编号查询界面的显示效果
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features.ltr_manager.view.ltr_view import LTRNumberCheckerView


class MockLTRController:
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


def create_test_window():
    """
    创建测试窗口
    """
    # 创建主窗口
    root = tk.Tk()
    root.title("LTR编号查询界面测试")
    root.geometry("800x600")

    # 创建LTR编号查询视图
    ltr_view = LTRNumberCheckerView(root)

    # 创建模拟控制器
    mock_controller = MockLTRController()
    ltr_view.set_controller(mock_controller)

    # 将视图添加到主窗口
    main_frame = ltr_view.get_main_frame()
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 显示示例数据
    ltr_view.show_sample_data()

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
