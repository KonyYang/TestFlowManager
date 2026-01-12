"""
报告更新模块数据模型
定义报告更新功能所需的数据结构
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReportUpdateConfig:
    """报告更新配置数据类"""
    # 基本配置
    base_directory: str = "D:\\OutFile"  # 默认基础目录
    project_directory: Optional[str] = None  # 当前项目目录
    selected_report_path: Optional[str] = None  # 选定的报告路径
    
    # 报告类型配置
    report_types: List[str] = field(default_factory=lambda: [
        "测试报告", "客户报告", "内部报告", "其他"
    ])
    
    # 设备列表更新配置
    equipment_list_path: Optional[str] = None  # 设备列表路径
    last_update_time: Optional[datetime] = None  # 最后更新时间
    update_history: List[Dict] = field(default_factory=list)  # 更新历史


class ReportUpdaterData:
    """报告更新功能的主要数据模型类"""
    
    def __init__(self):
        self.config = ReportUpdateConfig()
        self.current_project_path: Optional[str] = None
        self.available_reports: List[str] = []
        self.selected_report_type: Optional[str] = None
        self.is_project_loaded: bool = False
        
    def set_project_path(self, project_path: str) -> None:
        """设置当前项目路径"""
        self.current_project_path = project_path
        self.config.project_directory = project_path
        self.is_project_loaded = True
        
        # 尝试构建项目相关的报告目录
        if project_path:
            # 获取项目文件夹名称作为DL编号
            dl_number = os.path.basename(project_path)
            # 查找项目下的子文件夹，以DL编号开头的
            project_subfolder = os.path.join(project_path, dl_number)
            if os.path.exists(project_subfolder):
                self.config.base_directory = project_subfolder
            else:
                # 如果没有找到以DL编号命名的子文件夹，使用项目根目录
                self.config.base_directory = project_path
    
    def load_available_reports(self) -> List[str]:
        """加载可用的报告文件列表"""
        reports = []
        base_dir = self.config.project_directory if self.is_project_loaded else self.config.base_directory
        
        if os.path.exists(base_dir):
            for file in os.listdir(base_dir):
                if file.lower().endswith(('.docx', '.doc', '.pdf', '.xlsx', '.xls')):
                    reports.append(os.path.join(base_dir, file))
        
        self.available_reports = reports
        return reports
    
    def select_report(self, report_path: str) -> bool:
        """选择报告文件"""
        if os.path.exists(report_path):
            self.config.selected_report_path = report_path
            return True
        return False
    
    def get_current_directory(self) -> str:
        """获取当前使用的目录"""
        if self.is_project_loaded and self.config.project_directory:
            # 获取项目文件夹名称作为DL编号
            dl_number = os.path.basename(self.config.project_directory)
            # 查找项目下的子文件夹，以DL编号开头的
            project_subfolder = os.path.join(self.config.project_directory, dl_number)
            if os.path.exists(project_subfolder):
                return project_subfolder
            else:
                return self.config.project_directory
        else:
            return self.config.base_directory
    
    def update_equipment_list(self, equipment_data: List[Dict]) -> bool:
        """更新设备列表"""
        try:
            # 这里会实现具体的设备列表更新逻辑
            # 记录更新历史
            update_record = {
                "timestamp": datetime.now(),
                "action": "equipment_list_update",
                "data_size": len(equipment_data) if equipment_data else 0
            }
            self.config.update_history.append(update_record)
            self.config.last_update_time = datetime.now()
            return True
        except Exception as e:
            print(f"更新设备列表时出错: {e}")
            return False