"""
文档内容编辑工具模块
提供便捷的文档内容编辑接口，供其他模块调用
"""

from typing import Dict, List, Optional
from PyQt5.QtWidgets import QWidget
from src.features.content_editor.service.body_content_service import BodyContentService
from src.features.content_editor.view.body_content_dialog import BodyContentDialog


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
            # 显示正文内容编辑对话框
            dialog = BodyContentDialog(file_path, parent)
            
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
            # 使用update_multiple_sections_content方法更新多个段落
            success = True
            update_dict = {}
            
            for category, content in updates.items():
                if category == "PURPOSE":
                    update_dict["PURPOSE-CONCLUSIONS"] = content
                elif category == "CONCLUSIONS":
                    update_dict["CONCLUSIONS-SAMPLE DESCRIPTION"] = content
                elif category == "SAMPLE DESCRIPTION":
                    # 这种情况可能需要特殊处理
                    pass
            
            if update_dict:
                success = self.body_content_service.update_multiple_sections_content(file_path, update_dict)
            
            return success
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