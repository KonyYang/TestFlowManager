from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
import json
from src.core.config_manager import config_manager
from src.core.logger import logger
from src.utils.file_utils import ensure_directory_exists


class LTRDataManager:
    """LTR数据管理器类"""

    def __init__(self):
        """初始化LTR数据管理器"""
        pass

    def collect_application_data(self, form_data: Dict[str, Any], dl_number: Optional[str] = None, selected_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        收集LTR申请数据

        Args:
            form_data: 来自申请对话框的表单数据
            dl_number: DL编号（可选）
            selected_filename: 选中的申请单文件名（可选）

        Returns:
            完整的LTR申请数据字典
        """
        # 创建完整的数据字典
        application_data = form_data.copy()
        
        # 确保DL字段被正确设置
        if dl_number:
            application_data['DL'] = dl_number
        elif 'DL' not in application_data:
            application_data['DL'] = ''
        
        # 添加选中的申请单文件名
        application_data['selected_filename'] = selected_filename if selected_filename else ''
        
        # 添加一些额外的字段
        application_data['status'] = 'new'
        application_data['error'] = ''
        
        logger.info("成功收集LTR申请数据")
        return application_data

    def save_to_project_file(self, dl_number: str, application_data: Dict[str, Any]) -> bool:
        """
        将数据保存到指定DL对应项目根目录下的application_data.json文件

        Args:
            dl_number: DL编号
            application_data: LTR申请数据

        Returns:
            是否成功保存
        """
        try:
            if not dl_number:
                logger.warning("无法确定DL编号，无法定位项目根目录")
                return False

            # 确保application_data中的DL字段被正确设置
            application_data_copy = application_data.copy()
            application_data_copy['DL'] = dl_number

            # 获取项目根路径
            project_root = config_manager.get_path("default_project_path", "")
            if not project_root:
                project_root = "D:\\TestFlowManager\\Projects"

            # 构建项目根目录路径
            project_root_dir = os.path.join(project_root, dl_number)

            # 确保项目目录存在
            if not ensure_directory_exists(project_root_dir):
                logger.warning(f"无法创建项目根目录: {project_root_dir}")
                return False

            # 构建数据文件路径
            file_path = os.path.join(project_root_dir, "application_data.json")

            # 保存数据到JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(application_data_copy, f, ensure_ascii=False, indent=4)

            logger.info(f"申请数据已保存到: {file_path}")
            return True

        except Exception as e:
            logger.error(f"保存申请单数据到项目根目录失败: {e}", exc_info=True)
            return False


    def load_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        从JSON文件加载数据

        Args:
            file_path: JSON文件路径

        Returns:
            加载的数据字典，如果失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功从文件加载数据: {file_path}")
            return data
        except Exception as e:
            logger.error(f"从文件加载数据失败: {e}", exc_info=True)
            return None
