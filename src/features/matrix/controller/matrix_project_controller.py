"""
Matrix项目控制器
负责在LTR项目环境中管理和控制Matrix功能
"""

from src.features.matrix.controller.matrix_controller import MatrixController
from src.core.logger import logger


class MatrixProjectController:
    """
    Matrix项目控制器 - 项目/工作区入口控制器

    职责边界：
    - 项目/工作区入口方法
    - 高级Matrix打开和激活编排
    - 项目上下文和LTR集成传播（入口级别）
    - 外部模块进入Matrix时应调用的公共入口

    注意：该控制器内部使用MatrixController来执行具体的页面运行时操作，
    本身不处理表格操作、运行时编辑等页面级行为。
    """

    def __init__(self, parent_view=None, matrix_controller=None):
        """
        初始化Matrix项目控制器
        
        Args:
            parent_view: 父视图组件
        """
        self.parent_view = parent_view
        if matrix_controller is None:
            raise ValueError(
                "matrix_controller is required. Construct MatrixProjectController via "
                "MatrixSessionFactory or pass an explicit matrix_controller instance."
            )
        self.matrix_controller = matrix_controller
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
                project_json_path = (
                    ltr_integration_service.get_project_json_path()
                    if hasattr(ltr_integration_service, "get_project_json_path")
                    else getattr(ltr_integration_service, "project_json_path", "Not available")
                )
                logger.info(f"LTR integration service project JSON path: {project_json_path}")
            self.ltr_integration_service = ltr_integration_service
            # 同时设置到Matrix控制器中
            self.matrix_controller.set_ltr_integration_service(ltr_integration_service)
            # 设置LTR数据到Matrix服务中
            if ltr_integration_service and ltr_integration_service.current_ltr_data:
                from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
                ltr_data = LTRApplicationData.from_dict(ltr_integration_service.current_ltr_data)
                self.matrix_controller.set_ltr_data(ltr_data)
        else:
            logger.debug("LTR integration service unchanged, skipping update")
            
    def open_matrix_workspace(self):
        """
        打开Matrix工作区 - 唯一外部入口

        这是外部模块进入Matrix工作区的唯一公共入口点。
        负责项目/工作区级别的进入编排：
        1. 如有LTR项目数据，先初始化Matrix
        2. 委托运行时控制器执行实际的页面激活

        外部调用者应始终使用此方法，而非直接调用 MatrixController 的方法。

        Returns:
            bool: 是否成功打开
        """
        try:
            logger.info("Opening Matrix workspace entry")

            # Step 1: 如有LTR项目数据，先初始化Matrix（项目级编排决策）
            if self.ltr_integration_service and self.ltr_integration_service.is_project_loaded():
                logger.debug("Initializing Matrix with LTR data")
                self.matrix_controller.initialize_with_ltr_data()

            # Step 2: 委托运行时层执行页面激活（非项目级决策，纯执行）
            logger.debug("Delegating workspace activation to runtime controller")
            success = self.matrix_controller._activate_matrix_workspace_runtime()
            logger.info("Matrix workspace entry opened successfully")
            return bool(success)

        except Exception as e:
            logger.error(f"Failed to open matrix dialog: {e}", exc_info=True)
            return False
