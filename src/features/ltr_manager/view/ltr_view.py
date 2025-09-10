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
        # 存储当前显示的数据，用于编辑功能
        self.current_data = {}
        self.editable_items = {}

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
        result_frame = ttk.LabelFrame(self.main_frame, text="LTR信息编辑", padding="10")
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

        # 设置列宽
        self.result_tree.column("标签", width=200, anchor=tk.W)
        self.result_tree.column("申请编号或更新内容", width=200, anchor=tk.W)
        self.result_tree.column("已有编号内容", width=200, anchor=tk.W)
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

        # 操作按钮区域
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.save_button = ttk.Button(
            button_frame,
            text="保存修改",
            command=self._on_save_clicked
        )
        self.save_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.reset_button = ttk.Button(
            button_frame,
            text="重置",
            command=self._on_reset_clicked
        )
        self.reset_button.pack(side=tk.RIGHT)

        # 配置主框架网格
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        # 绑定双击事件用于编辑
        self.result_tree.bind("<Double-1>", self._on_item_double_click)

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

    def _on_item_double_click(self, event):
        """处理双击项目事件，允许编辑"""
        item = self.result_tree.identify('item', event.x, event.y)
        column = self.result_tree.identify('column', event.x, event.y)

        # 只允许编辑第2列（申请编号或更新内容）
        if column == "#2" and item:
            self._edit_item(item)

    def _edit_item(self, item_id):
        """编辑指定项目"""
        # 获取项目数据
        values = self.result_tree.item(item_id, 'values')
        label = values[0]
        current_value = values[1]

        # 创建一个顶层窗口用于编辑
        edit_window = tk.Toplevel(self.main_frame)
        edit_window.title(f"编辑 {label}")
        edit_window.geometry("400x150")
        edit_window.transient(self.main_frame)
        edit_window.grab_set()

        # 居中显示
        edit_window.geometry("+%d+%d" % (edit_window.winfo_screenwidth()/2 - 200,
                                         edit_window.winfo_screenheight()/2 - 75))

        # 创建编辑控件
        ttk.Label(edit_window, text=f"编辑 {label}:").pack(pady=10)

        entry = ttk.Entry(edit_window, width=50)
        entry.insert(0, current_value)
        entry.pack(pady=5)
        entry.select_range(0, tk.END)
        entry.focus()

        # 保存按钮
        def save_edit():
            new_value = entry.get()
            # 更新Treeview中的值
            values = list(self.result_tree.item(item_id, 'values'))
            values[1] = new_value
            self.result_tree.item(item_id, values=values)
            edit_window.destroy()

        # 按钮框架
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="保存", command=save_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)

        # 绑定回车键保存
        entry.bind('<Return>', lambda e: save_edit())
        entry.bind('<Escape>', lambda e: edit_window.destroy())

    def _on_save_clicked(self):
        """处理保存按钮点击事件"""
        # 收集所有编辑后的数据
        updated_data = {}
        for item_id in self.result_tree.get_children():
            values = self.result_tree.item(item_id, 'values')
            label = values[0]
            new_value = values[1]
            updated_data[label] = new_value

        # 调用控制器保存数据
        if self.controller:
            success = self.controller.save_ltr_data(updated_data)
            if success:
                messagebox.showinfo("保存成功", "LTR信息已保存")
            else:
                messagebox.showerror("保存失败", "保存LTR信息时发生错误")
        else:
            messagebox.showerror("系统错误", "控制器未设置")

    def _on_reset_clicked(self):
        """处理重置按钮点击事件"""
        # 重置为原始数据
        self.display_ltr_info(self.current_data)

    def display_ltr_info(self, info: Dict[str, Any]) -> None:
        """
        显示LTR信息

        Args:
            info: LTR信息字典
        """
        # 保存当前数据
        self.current_data = info.copy()

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
            # 第二列默认为空，用户可以编辑
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

    def update_comparison_data(self, new_data: Dict[str, Any], existing_data: Dict[str, Any]) -> None:
        """
        更新比较数据，在第三列显示已有信息，并用颜色区分不同类型

        Args:
            new_data: 新的数据（申请编号或更新内容）
            existing_data: 已有数据（已有编号内容）
        """
        # 保存当前数据
        self.current_data = existing_data.copy()

        # 清空现有数据
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 根据标签分类显示不同颜色
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
        all_keys = set(new_data.keys()) | set(existing_data.keys())
        for key in sorted(all_keys):
            tag = tag_mapping.get(key, "")
            new_value = new_data.get(key, "")
            existing_value = existing_data.get(key, "")

            self.result_tree.insert(
                "",
                tk.END,
                values=(key, new_value, existing_value),
                tags=(tag,)
            )
