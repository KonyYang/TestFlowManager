"""
文档内容编辑工具模块
提供便捷的文档内容编辑接口，供其他模块调用
"""

from typing import Dict, List, Optional
from PyQt5.QtWidgets import QWidget
from src.features.document_parser.service.body_content_service import BodyContentService
from src.features.document_parser.view.body_content_dialog import BodyContentDialog


class DocumentContentEditor:
    """
    文档内容编辑工具类
    提供便捷的文档内容编辑接口
    """
    
    def __init__(self):
        """初始化文档内容编辑工具"""
        self.body_content_service = BodyContentService()
    
    def edit_document_content(self, file_path: str, parent: Optional[QWidget] = None) -> bool:
        """
        编辑文档内容
        
        Args:
            file_path: Word文档路径
            parent: 父窗口组件
            
        Returns:
            是否成功编辑
        """
        try:
            # 查找文档中的特定段落
            paragraphs_info = self.body_content_service.find_body_paragraphs(file_path)
            
            # 显示正文内容编辑对话框
            dialog = BodyContentDialog(file_path, paragraphs_info, parent)
            
            # 显示对话框并等待用户操作
            result = dialog.exec_()
            
            return result == dialog.Accepted
            
        except Exception as e:
            from src.core.logger import logger
            logger.error(f"编辑文档内容时出错: {e}")
            return False
    
    def get_available_categories(self) -> List[str]:
        """
        获取可用的段落类别
        
        Returns:
            段落类别列表
        """
        return ["PURPOSE", "CONCLUSIONS", "SAMPLE DESCRIPTION"]
    
    def update_document_paragraphs(self, file_path: str, updates: Dict[str, str]) -> bool:
        """
        批量更新文档段落内容
        
        Args:
            file_path: Word文档路径
            updates: 更新内容字典，键为段落类别，值为新内容
            
        Returns:
            是否成功更新
        """
        try:
            return self.body_content_service.update_body_content(file_path, updates)
        except Exception as e:
            from src.core.logger import logger
            logger.error(f"更新文档段落时出错: {e}")
            return False
    
    def get_predefined_descriptions(self, category: str) -> List[str]:
        """
        获取预定义描述内容
        
        Args:
            category: 描述类别
            
        Returns:
            预定义描述内容列表
        """
        return self.body_content_service.get_predefined_descriptions(category)
    
    def add_predefined_description(self, category: str, description: str) -> bool:
        """
        添加预定义描述内容
        
        Args:
            category: 描述类别
            description: 描述内容
            
        Returns:
            是否成功添加
        """
        return self.body_content_service.add_predefined_description(category, description)