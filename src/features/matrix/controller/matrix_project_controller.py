"""
Matrix项目控制器
负责在LTR项目环境中管理和控制Matrix功能
"""

from src.features.matrix.controller.matrix_controller import MatrixController
from src.features.matrix.view.matrix_dialog import MatrixDialog
from src.core.logger import logger


class MatrixProjectController:
    """
    Matrix项目控制器
    在LTR项目环境中管理和控制Matrix功能
    """

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
        logger.info(f"Setting LTR integration service: {ltr_integration_service is not None}")
        if ltr_integration_service:
            logger.info(f"LTR integration service project data file path: {getattr(ltr_integration_service, 'project_data_file_path', 'Not available')}")
        self.ltr_integration_service = ltr_integration_service
        # 同时设置到Matrix控制器中
        self.matrix_controller.set_ltr_integration_service(ltr_integration_service)

    def open_matrix_dialog(self):
        """
        打开Matrix对话框
        
        Returns:
            bool: 是否成功打开
        """
        try:
            logger.info("Opening Matrix dialog")
            
            # 如果有LTR项目数据，先初始化Matrix
            if self.ltr_integration_service and self.ltr_integration_service.is_project_loaded():
                logger.debug("Initializing Matrix with LTR data")
                self.matrix_controller.initialize_with_ltr_data()
            
            # 显示Matrix对话框
            logger.debug("Showing Matrix dialog")
            self.matrix_controller.show_matrix_dialog()
            logger.info("Matrix dialog opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open matrix dialog: {e}", exc_info=True)
            return False

    def get_available_spec_files(self):
        """
        获取可用的规格文件列表
        
        Returns:
            list: 规格文件路径列表
        """
        if not self.ltr_integration_service:
            return []
            
        return self.ltr_integration_service.get_specification_files()

    def import_spec_file(self, file_path, page_number=None, keyword=None):
        """
        导入规格文件
        
        Args:
            file_path (str): 文件路径
            page_number (int, optional): 页码
            keyword (str, optional): 关键词
            
        Returns:
            dict: 导入结果
        """
        try:
            result = self.matrix_controller.import_from_spec(file_path, page_number, keyword)
            return result
        except Exception as e:
            logger.error(f"Failed to import spec file: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_standard_versions(self):
        """
        更新标准版本号
        
        Returns:
            dict: 更新结果
        """
        try:
            result = self.matrix_controller.service.update_standard_versions()
            return result
        except Exception as e:
            logger.error(f"Failed to update standard versions: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def export_matrix_to_excel(self, file_path):
        """
        导出Matrix到Excel
        
        Args:
            file_path (str): 导出文件路径
            
        Returns:
            dict: 导出结果
        """
        try:
            result = self.matrix_controller.export_to_excel(file_path)
            return result
        except Exception as e:
            logger.error(f"Failed to export matrix to Excel: {e}")
            return {
                "success": False,
                "error": str(e)
            }