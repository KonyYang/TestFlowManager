# src/features/matrix/controller/matrix_controller.py
from src.features.matrix.service.matrix_service import MatrixService
from src.features.matrix.view.matrix_dialog import MatrixDialog
from src.core.logger import logger


class MatrixController:
    """Matrix控制器 - Controller层"""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        self.service = MatrixService()
        # 添加对LTR项目集成服务的支持
        self.ltr_integration_service = None
        # 添加对LTR编号的跟踪
        self.ltr_number = None

    def show_matrix_dialog(self):
        """显示Matrix编辑对话框 - Controller层协调"""
        try:
            logger.info("Creating MatrixDialog instance")
            dialog = MatrixDialog(self.parent_view, self.service, self.ltr_number)
            logger.debug("MatrixDialog instance created successfully")
            logger.info("Executing MatrixDialog")
            dialog.exec_()
            logger.info("MatrixDialog execution completed")
        except Exception as e:
            logger.error(f"Error showing matrix dialog: {e}", exc_info=True)
            raise

    def get_matrix_data(self):
        """获取Matrix数据 - Controller层数据提供"""
        return self.service.data_model

    def export_to_excel(self, file_path, export_type="matrix_excel"):
        """导出到Excel - Controller层业务流程"""
        return self.service.export_to_excel(file_path, export_type)

    def import_from_excel(self, file_path):
        """从Excel导入数据 - Controller层业务流程"""
        return self.service.import_from_excel(file_path)

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """从Spec导入数据 - Controller层业务流程"""
        return self.service.import_from_spec(file_path, page_number, keyword)
        
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
        
    def set_ltr_integration_service(self, ltr_integration_service):
        """
        设置LTR项目集成服务
        
        Args:
            ltr_integration_service: LTR项目集成服务实例
        """
        # 只在服务实例发生变化时才进行设置
        if self.ltr_integration_service != ltr_integration_service:
            logger.info(f"MatrixController: Setting LTR integration service: {ltr_integration_service is not None}")
            if ltr_integration_service:
                logger.info(f"MatrixController: LTR integration service project data file path: {getattr(ltr_integration_service, 'project_data_file_path', 'Not available')}")
            self.ltr_integration_service = ltr_integration_service
        else:
            logger.debug("MatrixController: LTR integration service unchanged, skipping update")
        
    def initialize_with_ltr_data(self):
        """
        使用LTR项目数据初始化Matrix
        
        Returns:
            bool: 是否成功初始化
        """
        if not self.ltr_integration_service or not self.ltr_integration_service.is_project_loaded():
            return False
            
        # 获取LTR数据
        ltr_data = self.ltr_integration_service.get_ltr_data()
        if not ltr_data:
            return False
            
        # 初始化Matrix
        self.service.initialize_matrix()
        
        # 可以在这里根据LTR数据预填充Matrix的一些字段
        # 例如设置测试项目类型等信息
        test_info = self.ltr_integration_service.get_test_info()
        # 这里可以根据需要进行预填充操作
        
        return True
        
    def set_ltr_number(self, ltr_number):
        """
        设置LTR编号
        
        Args:
            ltr_number (str): LTR编号
        """
        self.ltr_number = ltr_number