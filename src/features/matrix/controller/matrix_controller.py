# src/features/matrix/controller/matrix_controller.py
from src.features.matrix.service.matrix_service import MatrixService
from src.features.matrix.view.matrix_dialog import MatrixDialog


class MatrixController:
    """Matrix控制器 - Controller层"""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        self.service = MatrixService()

    def show_matrix_dialog(self):
        """显示Matrix编辑对话框 - Controller层协调"""
        dialog = MatrixDialog(self.parent_view, self.service)
        dialog.exec_()

    def get_matrix_data(self):
        """获取Matrix数据 - Controller层数据提供"""
        return self.service.data_model

    def export_to_excel(self, file_path):
        """导出到Excel - Controller层业务流程"""
        return self.service.export_to_excel(file_path)

    def import_from_excel(self, file_path):
        """从Excel导入数据 - Controller层业务流程"""
        return self.service.import_from_excel(file_path)

    def import_from_spec(self, file_path):
        """从Spec导入数据 - Controller层业务流程"""
        return self.service.import_from_spec(file_path)
        
    def merge_or_split_cells(self, table_widget):
        """合并或拆分单元格 - Controller层业务流程"""
        return self.service.merge_or_split_cells(table_widget)
        
    def can_undo_cell_operation(self):
        """检查是否可以撤销单元格操作 - Controller层业务流程"""
        return self.service.can_undo_cell_operation()
        
    def can_redo_cell_operation(self):
        """检查是否可以重做单元格操作 - Controller层业务流程"""
        return self.service.can_redo_cell_operation()
        
    def undo_cell_operation(self):
        """撤销单元格操作 - Controller层业务流程"""
        return self.service.undo_cell_operation()
        
    def redo_cell_operation(self):
        """重做单元格操作 - Controller层业务流程"""
        return self.service.redo_cell_operation()

    def show_test_group_selector(self):
        """显示测试组选择器 - Controller层协调"""
        # 这个方法可以直接通过View层调用对话框，不需要额外的业务逻辑
        pass