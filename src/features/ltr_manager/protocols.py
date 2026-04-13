"""
LTR 模块协议定义 - 用于解耦 controller 和 dialog
"""
from typing import Protocol, Dict, Any


class LTREditorControllerProtocol(Protocol):
    """LTR 编辑器控制器协议
    
    用于打破 ltr_editor_controller 和 ltr_editor_dialog 之间的循环依赖
    """
    
    def update_ltr_data(self, dl_number: str, modified_data: Dict[str, Any] = None, parent=None) -> bool:
        """
        更新 LTR 数据
        
        Args:
            dl_number: DL 编号
            modified_data: 修改后的数据
            parent: 父窗口
            
        Returns:
            是否成功更新
        """
        ...
