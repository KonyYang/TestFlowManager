"""
LTR视图模块
提供LTR相关的用户界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from src.core.logger import logger


class LTRNumberCheckerView:
    """
    LTR编号查询界面
    提供用户界面用于查询和显示LTR编号信息
    """

    def __init__(self, parent=None):
        """
        初始化LTR编号查询界面

        Args:
            parent: 父级窗口
        """
        self.parent = parent
        self.controller = None
        self.setup_ui()
        self.setup_styles()
        self.sample_data = self._get_sample_data()

    def set_controller(self, controller) -> None:
        """
        设置控制器

        Args:
            controller: LTR控制器实例
        """
        self.controller = controller

    def setup_ui(self) -> None:
        """设置用户界面"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.parent if self.parent else tk.Tk())
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            self.main_frame,
            text="LTR编号查询",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(10, 20))

        # 输入区域
        input_frame = ttk.LabelFrame(self.main_frame, text="查询条件", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # DL编号输入
        dl_frame = ttk.Frame(input_frame)
        dl_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dl_frame, text="DL编号:").pack(side=tk.LEFT)
        self.dl_entry = ttk.Entry(dl_frame, width=30)
        self.dl_entry.pack(side=tk.LEFT, padx=(10, 0))

        # 查询按钮
        self.search_button = ttk.Button(
            dl_frame,
            text="查看指定编号",
            command=self._on_search_clicked
        )
        self.search_button.pack(side=tk.RIGHT)

        # 结果显示区域
        result_frame = ttk.LabelFrame(self.main_frame, text="已有编号内容", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 创建Treeview显示结果
        columns = ("标签", "申请编号或更新内容", "已有编号内容")
        self.result_tree = ttk.Treeview(
            result_frame,
            columns=columns,
            show="tree headings",
            height=15
        )

        # 设置列标题
        self.result_tree.heading("#0", text="")
        self.result_tree.heading("标签", text="标签")
        self.result_tree.heading("申请编号或更新内容", text="申请编号或更新内容")
        self.result_tree.heading("已有编号内容", text="已有编号内容")

        for col in columns:
            self.result_tree.column(col, width=200, anchor=tk.W)
        self.result_tree.column("#0", width=50, anchor=tk.W)

        # 添加滚动条
        scrollbar_v = ttk.Scrollbar(
            result_frame,
            orient=tk.VERTICAL,
            command=self.result_tree.yview
        )
        scrollbar_h = ttk.Scrollbar(
            result_frame,
            orient=tk.HORIZONTAL,
            command=self.result_tree.xview
        )
        self.result_tree.configure(
            yscrollcommand=scrollbar_v.set,
            xscrollcommand=scrollbar_h.set
        )

        # 布局
        self.result_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        # 配置主框架网格
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

    def setup_styles(self) -> None:
        """设置界面样式和颜色"""
        self.style = ttk.Style()

        # 定义颜色标签 - 只使用字体颜色
        self.result_tree.tag_configure("red", foreground="#8B0000")
        self.result_tree.tag_configure("blue", foreground="#00008B")
        self.result_tree.tag_configure("green", foreground="#006400")
        self.result_tree.tag_configure("orange", foreground="#FF8C00")
        self.result_tree.tag_configure("purple", foreground="#4B0082")
        self.result_tree.tag_configure("cyan", foreground="#008B8B")
        self.result_tree.tag_configure("pink", foreground="#8B008B")

    def _on_search_clicked(self) -> None:
        """处理查询按钮点击事件"""
        dl_number = self.dl_entry.get().strip()
        if not dl_number:
            messagebox.showwarning("输入错误", "请输入DL编号")
            return

        if self.controller:
            self.set_search_button_state(False)  # 禁用按钮防止重复点击
            success = self.controller.handle_search_ltr_number(dl_number)
            if not success:
                messagebox.showerror("查询失败", "未能找到指定的DL编号")
            self.set_search_button_state(True)  # 重新启用按钮
        else:
            messagebox.showerror("系统错误", "控制器未设置")
            self.set_search_button_state(True)

    def display_ltr_info(self, info: Dict[str, Any]) -> None:
        """
        显示LTR信息

        Args:
            info: LTR信息字典
        """
        # 清空现有数据
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 根据标签分类显示不同颜色 - 使用更简洁的方法
        color_categories = {
            "red": ["DL", "Project Type", "Description P/N", "Test Item", "Test Type",
                    "Requested by", "Location", "Project Leader", "Test Result",
                    "Failed item", "Sample deposition", "Sub-contract", "Test Fee",
                    "Remarks (PO)"],
            "blue": ["Phone", "E-mail of Requestor", "Product Description",
                     "Applicable Specifications", "Date Lab Received Samples",
                     "Estimated Completion Date"],
            "green": ["Start Test Date", "Finish Test Date", "Report Date"],
            "orange": ["Customer", "Department", "Priority"],
            "purple": ["Reference Documents", "Test Standards"],
            "cyan": ["Equipment Used", "Test Conditions"],
            "pink": ["Special Requirements", "Notes"]
        }

        # 创建标签到颜色的映射
        tag_mapping = {}
        for color, labels in color_categories.items():
            for label in labels:
                tag_mapping[label] = color

        # 添加数据
        for key, value in info.items():
            tag = tag_mapping.get(key, "")
            self.result_tree.insert(
                "",
                tk.END,
                values=(key, "", value if value else ""),
                tags=(tag,)
            )

    def _get_sample_data(self) -> Dict[str, Any]:
        """获取示例数据用于测试"""
        return {
            "DL": "DL-2025-001",
            "Project Type": "新产品测试",
            "Description P/N": "产品型号XYZ-123",
            "Test Item": "电气安全测试",
            "Test Type": "型式试验",
            "Requested by": "张三",
            "Location": "实验室A",
            "Project Leader": "李四",
            "Test Result": "通过",
            "Failed item": "",
            "Sample deposition": "样品库",
            "Sub-contract": "否",
            "Test Fee": "¥5000",
            "Remarks (PO)": "加急处理",
            "Phone": "138-0000-0000",
            "E-mail of Requestor": "zhangsan@company.com",
            "Product Description": "高性能电子设备",
            "Applicable Specifications": "GB 4943.1-2011",
            "Date Lab Received Samples": "2025-09-01",
            "Estimated Completion Date": "2025-09-30",
            "Start Test Date": "2025-09-05",
            "Finish Test Date": "2025-09-25",
            "Report Date": "2025-09-28"
        }

    def get_main_frame(self) -> ttk.Frame:
        """
        获取主框架

        Returns:
            主框架实例
        """
        return self.main_frame

    def set_search_button_state(self, enabled: bool) -> None:
        """
        设置查询按钮状态

        Args:
            enabled: 是否启用
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self.search_button.config(state=state)

    def show_sample_data(self) -> None:
        """显示示例数据用于测试"""
        self.display_ltr_info(self.sample_data)

    def set_dl_number(self, dl_number: str) -> None:
        """
        设置DL编号到输入框

        Args:
            dl_number: DL编号
        """
        self.dl_entry.delete(0, tk.END)
        self.dl_entry.insert(0, dl_number)



