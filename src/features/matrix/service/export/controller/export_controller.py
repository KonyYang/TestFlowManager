from src.features.matrix.service.export.service.matrix_editor_export_service import MatrixEditorExcelExportService
from src.features.matrix.service.export.service.test_status_export_service import TestStatusTableExportService
from src.core.logger import logger


class ExportController:
    """导出控制器 - Controller层"""

    def __init__(self, data_model, ltr_data=None):
        self.data_model = data_model
        self.ltr_data = ltr_data
        self.excel_export_service = MatrixEditorExcelExportService(data_model)
        self.test_status_export_service = TestStatusTableExportService(data_model, ltr_data)
        # 移除LTR数据的详细日志输出

    def export_by_type(self, file_path, export_type):
        """
        根据导出类型执行导出操作

        Args:
            file_path: 导出文件路径
            export_type: 导出类型

        Returns:
            bool: 是否导出成功
        """
        try:
            logger.debug(f"开始导出操作，类型: {export_type}，路径: {file_path}")

            # 添加调试信息
            try:
                # 直接访问MatrixData类的rows属性
                rows = self.data_model.rows
                headers = self.data_model.headers
                logger.debug(f"导出控制器数据概况 - 表头数量: {len(headers)}, 行数: {len(rows)}")
                if headers:
                    logger.debug(f"表头内容: {headers}")
                if rows:
                    logger.debug(f"导出控制器前3行:")
                    for i, row in enumerate(rows[:3]):
                        logger.debug(f"  第{i+1}行: {row}")
                    if len(rows) > 3:
                        logger.debug(f"  ... (还有{len(rows)-3}行)")
            except Exception as e:
                logger.error(f"获取导出控制器数据信息时出错: {e}")

            if export_type == "matrix_excel":
                # 移除调用matrix_excel导出服务的详细日志
                return self.excel_export_service.export_to_excel(file_path)
            elif export_type == "test_status":
                logger.debug("调用 test_status 导出服务")
                return self.test_status_export_service.export_to_excel(file_path)
            elif export_type in ["llcr", "cr", "mating_unmating", "ir_dwv"]:
                # 这些类型将使用相同的基础Excel导出服务，但可能有不同的处理逻辑
                logger.debug(f"调用基础Excel导出服务，类型: {export_type}")
                return self.excel_export_service.export_to_excel(file_path)
            else:
                logger.warning(f"不支持的导出类型: {export_type}")
                return False
        except Exception as e:
            logger.error(f"导出过程中出错: {e}", exc_info=True)
            return False

    def set_ltr_data(self, ltr_data):
        """
        设置LTR数据

        Args:
            ltr_data: LTR申请单数据
        """
        # 移除LTR数据的详细日志输出
        self.ltr_data = ltr_data
        # 更新TestStatusExportService中的ltr_data
        self.test_status_export_service = TestStatusTableExportService(self.data_model, ltr_data)

    def update_data_model(self, data_model):
        """
        更新数据模型

        Args:
            data_model: 新的数据模型
        """
        self.data_model = data_model
        # 重新创建MatrixEditorExcelExportService实例以确保使用最新的数据
        self.excel_export_service = MatrixEditorExcelExportService(data_model)
        # 重新创建TestStatusTableExportService实例以确保使用最新的数据
        self.test_status_export_service = TestStatusTableExportService(data_model, self.ltr_data)
