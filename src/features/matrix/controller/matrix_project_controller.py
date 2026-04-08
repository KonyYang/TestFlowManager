"""
Matrix项目控制器
负责在LTR项目环境中管理和控制Matrix功能
"""

from src.features.matrix.controller.matrix_controller import MatrixController
from src.core.logger import logger


class MatrixProjectController:
    """
    Matrix项目控制器
    
    在LTR项目环境中管理和控制Matrix功能，作为Matrix核心功能与LTR项目环境之间的桥梁。
    负责协调LTR项目数据与Matrix功能的集成，提供项目级别的Matrix功能接口。
    该控制器内部使用MatrixController来执行具体的功能操作。"""

    def __init__(self, parent_view=None):
        """
        初始化Matrix项目控制器
        
        Args:
            parent_view: 父视图组件
        """
        self.parent_view = parent_view
        self.matrix_controller = MatrixController(parent_view)
        self.ltr_integration_service = None

    def set_ltr_integration_service(self, ltr_integration_service):
        """
        设置LTR项目集成服务
        
        Args:
            ltr_integration_service: LTR项目集成服务实例
        """
        # 只在服务实例发生变化时才进行设置
        if self.ltr_integration_service != ltr_integration_service:
            logger.info(f"Setting LTR integration service: {ltr_integration_service is not None}")
            if ltr_integration_service:
                logger.info(f"LTR integration service project data file path: {getattr(ltr_integration_service, 'project_data_file_path', 'Not available')}")
            self.ltr_integration_service = ltr_integration_service
            # 同时设置到Matrix控制器中
            self.matrix_controller.set_ltr_integration_service(ltr_integration_service)
            # 设置LTR数据到Matrix服务中
            if ltr_integration_service and ltr_integration_service.current_ltr_data:
                from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
                ltr_data = LTRApplicationData.from_dict(ltr_integration_service.current_ltr_data)
                self.matrix_controller.service.set_ltr_data(ltr_data)
        else:
            logger.debug("LTR integration service unchanged, skipping update")
            
    def open_matrix_workspace(self):
        """
        打开Matrix工作区入口

        Returns:
            bool: 是否成功打开
        """
        try:
            logger.info("Opening Matrix workspace entry")
            
            # 如果有LTR项目数据，先初始化Matrix
            if self.ltr_integration_service and self.ltr_integration_service.is_project_loaded():
                logger.debug("Initializing Matrix with LTR data")
                self.matrix_controller.initialize_with_ltr_data()
            
            logger.debug("Showing Matrix workspace entry")
            success = self.matrix_controller.activate_matrix_workspace()
            logger.info("Matrix workspace entry opened successfully")
            return bool(success)
            
        except Exception as e:
            logger.error(f"Failed to open matrix dialog: {e}", exc_info=True)
            return False
