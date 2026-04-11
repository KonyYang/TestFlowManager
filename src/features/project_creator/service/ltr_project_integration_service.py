"""
LTR项目与Matrix模块集成服务
负责在项目创建完成后加载LTR信息并提供给Matrix模块使用
"""

import os
import json
from src.core.logger import logger


class LTRProjectIntegrationService:
    """
    LTR项目与Matrix模块集成服务
    """
    
    def __init__(self):
        self.current_ltr_data = None
        self.current_ltr_path = None
        self.project_json_path = None
    
    def load_ltr_project(self, project_path):
        """
        加载LTR项目数据
        
        Args:
            project_path (str): 项目路径
            
        Returns:
            dict: LTR项目数据
        """
        try:
            logger.info(f"Loading LTR project from path: {project_path}")
            # 查找项目中的JSON文件
            json_files = [f for f in os.listdir(project_path) if f.endswith('.json')]
            logger.info(f"Found JSON files: {json_files}")
            
            if not json_files:
                logger.warning(f"No JSON file found in project path: {project_path}")
                return None
                
            # 假设只有一个JSON文件，或者使用第一个JSON文件
            json_file = json_files[0]
            json_path = os.path.join(project_path, json_file)
            logger.info(f"Using JSON file: {json_path}")
            
            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                ltr_data = json.load(f)
                
            self.current_ltr_data = ltr_data
            self.current_ltr_path = project_path
            self.project_json_path = json_path
            
            logger.info(f"Successfully loaded LTR project data from: {json_path}")
            logger.info(f"Project JSON path set to: {self.project_json_path}")
            return ltr_data
            
        except Exception as e:
            logger.error(f"Failed to load LTR project data: {e}")
            return None
    
    def get_ltr_data(self):
        """
        获取当前LTR数据
        
        Returns:
            dict: 当前LTR数据
        """
        return self.current_ltr_data
    
    def get_project_path(self):
        """
        获取当前项目路径
        
        Returns:
            str: 当前项目路径
        """
        return self.current_ltr_path

    def get_project_json_path(self):
        """获取项目 application_data.json 路径。"""
        return self.project_json_path
    
    def is_project_loaded(self):
        """
        检查是否有项目已加载
        
        Returns:
            bool: 是否有项目已加载
        """
        return self.current_ltr_data is not None and self.current_ltr_path is not None
    
    def get_specification_files(self):
        """
        获取项目中的规格文件列表
        
        Returns:
            list: 规格文件路径列表
        """
        if not self.is_project_loaded():
            return []
            
        project_path = self.current_ltr_path
        spec_files = []
        
        # 查找常见的规格文件类型
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.lower().endswith(('.doc', '.docx', '.pdf')):
                    spec_files.append(os.path.join(root, file))
                    
        return spec_files
    
    def get_test_info(self):
        """
        获取测试相关信息
        
        Returns:
            dict: 测试相关信息
        """
        if not self.is_project_loaded():
            return {}
            
        # 从LTR数据中提取测试相关信息
        test_info = {
            'project_type': self.current_ltr_data.get('project_type', ''),
            'sample_information': self.current_ltr_data.get('sample_information', ''),
            'tests_to_be_performed': self.current_ltr_data.get('tests_to_be_performed', ''),
            'test_type': self.current_ltr_data.get('test_type', ''),
            'applicable_specifications': self.current_ltr_data.get('applicable_specifications', '')
        }
        
        return test_info
