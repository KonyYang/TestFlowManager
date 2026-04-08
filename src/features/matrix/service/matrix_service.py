from src.features.matrix.model.matrix_data import MatrixData
from src.features.matrix.service.matrix_cell_service import MatrixCellService
from src.features.matrix.service.matrix_initializer import MatrixInitializer
from src.features.matrix.service.base.matrix_base_operation_service import MatrixBaseOperationService
from src.features.matrix.service.base.matrix_formatting_service import MatrixFormattingService
from src.features.matrix.service.export.controller.export_controller import ExportController
from src.features.matrix.service.export.model.export_data_model import ExportDataModel
from src.features.matrix.service.spec.matrix_spec_processing_service import MatrixSpecProcessingService
from src.features.matrix.service.processing.matrix_data_structure_service import MatrixDataStructureService
from src.core.logger import logger

# 全局单例实例
_matrix_service_instance = None


class MatrixService:
    """Matrix服务层 - Service层"""

    def __new__(cls):
        global _matrix_service_instance
        if _matrix_service_instance is None:
            _matrix_service_instance = super(MatrixService, cls).__new__(cls)
        return _matrix_service_instance

    def __init__(self):
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        self.data_model = MatrixData()
        self.cell_service = MatrixCellService()
        self.initializer = MatrixInitializer(self.data_model)
        
        # 创建基础操作服务
        self.base_operation_service = MatrixBaseOperationService(self.data_model)
        
        # 创建格式化服务
        self.formatting_service = MatrixFormattingService(self.cell_service)
        
        # 创建数据结构实例
        from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
        self.data_structure = MatrixDataStructure()
        
        # 创建导出控制器和数据模型
        self.export_data_model = ExportDataModel(self.data_model)
        self.export_controller = ExportController(self.data_model)
        
        # 创建数据结构服务
        self.data_structure_service = MatrixDataStructureService(self.data_model, self.data_structure)
        
        # 创建模板填充器实例
        from src.features.matrix.service.template.template_filler import TemplateFiller
        self.template_filler = TemplateFiller()
        
        # 创建规格书处理服务
        self.spec_processing_service = MatrixSpecProcessingService(self.data_model, self.template_filler)
        
        # 临时存储合并单元格信息
        self.merged_cells_info = []
        # 存储最近导入的规格书文件路径
        self.last_imported_spec_path = self.spec_processing_service.last_imported_spec_path
        # 添加项目控制器引用
        self.project_controller = None
        # 标记为已初始化
        self._initialized = True

    def add_column(self, column_name="", position=None):
        """添加新列 - Service层业务逻辑"""
        return self.base_operation_service.add_column(column_name, position)

    def insert_column(self, column_index, column_name=""):
        """在指定位置插入新列 - Service层业务逻辑"""
        return self.base_operation_service.insert_column(column_index, column_name)

    def move_column(self, from_index, to_index):
        """移动列 - Service层业务逻辑"""
        return self.base_operation_service.move_column(from_index, to_index)

    def remove_column(self, column_index):
        """删除指定列 - Service层业务逻辑"""
        return self.base_operation_service.remove_column(column_index)

    def add_row(self, row_data=None):
        """添加新行 - Service层业务逻辑"""
        return self.base_operation_service.add_row(row_data)

    def insert_row(self, row_index, row_data=None):
        """在指定位置插入新行 - Service层业务逻辑"""
        return self.base_operation_service.insert_row(row_index, row_data)

    def remove_row(self, row_index):
        """删除指定行 - Service层业务逻辑"""
        return self.base_operation_service.remove_row(row_index)

    def move_row(self, from_index, to_index):
        """移动行 - Service层业务逻辑"""
        return self.base_operation_service.move_row(from_index, to_index)

    def copy_row(self, row_index):
        """复制行 - Service层业务逻辑"""
        return self.base_operation_service.copy_row(row_index)

    def paste_row(self, row_index, row_data):
        """粘贴行 - Service层业务逻辑"""
        return self.base_operation_service.paste_row(row_index, row_data)

    def copy_column(self, col_index):
        """复制列 - Service层业务逻辑"""
        return self.base_operation_service.copy_column(col_index)

    def paste_column(self, col_index, column_data):
        """粘贴列 - Service层业务逻辑"""
        return self.base_operation_service.paste_column(col_index, column_data)

    def get_cell_value(self, row_index, col_index):
        """获取单元格值 - Service层数据访问"""
        return self.base_operation_service.get_cell_value(row_index, col_index)

    def set_cell_value(self, row_index, col_index, value):
        """设置单元格值 - Service层数据修改"""
        return self.base_operation_service.set_cell_value(row_index, col_index, value)

    def find_by_content(self, search_text):
        """通过内容查找单元格 - Service层查询功能"""
        return self.base_operation_service.find_by_content(search_text)

    def merge_or_split_cells(self, table_widget):
        """合并或拆分单元格 - Service层业务逻辑"""
        return self.formatting_service.merge_or_split_cells(table_widget)
        
    def can_undo_cell_operation(self):
        """检查是否可以撤销单元格操作"""
        return self.formatting_service.can_undo_cell_operation()
        
    def can_redo_cell_operation(self):
        """检查是否可以重做单元格操作"""
        return self.formatting_service.can_redo_cell_operation()
        
    def undo_cell_operation(self):
        """撤销单元格操作"""
        return self.formatting_service.undo_cell_operation()
        
    def redo_cell_operation(self):
        """重做单元格操作"""
        return self.formatting_service.redo_cell_operation()
        
    def get_undo_cell_operation_text(self):
        """获取撤销单元格操作的文本描述"""
        return self.formatting_service.get_undo_cell_operation_text()
        
    def get_redo_cell_operation_text(self):
        """获取重做单元格操作的文本描述"""
        return self.formatting_service.get_redo_cell_operation_text()

    def initialize_matrix(self):
        """初始化Matrix - Service层业务逻辑"""
        return self.initializer.initialize_matrix()

    def export_to_excel(self, file_path, export_type="matrix_excel"):
        """导出到Excel - Service层持久化功能"""
        # 在导出前强制同步数据模型，确保使用最新数据
        self._sync_table_to_model()
        
        # 添加调试信息
        try:
            rows = self.data_model.rows
            headers = self.data_model.headers
            logger.debug(f"导出前数据概况 - 表头数量: {len(headers)}, 行数: {len(rows)}")
            if headers:
                logger.debug(f"表头内容: {headers}")
            if rows:
                logger.debug(f"导出前第一行数据: {rows[0][:5] if len(rows[0]) > 5 else rows[0]}")  # 只显示前5个元素
                logger.debug(f"导出前前3行:")
                for i, row in enumerate(rows[:3]):
                    logger.debug(f"  第{i+1}行: {row}")
                if len(rows) > 3:
                    logger.debug(f"  ... (还有{len(rows)-3}行)")
        except Exception as e:
            logger.error(f"获取导出前数据信息时出错: {e}")
        # 使用导出控制器执行导出
        return self.export_controller.export_by_type(file_path, export_type)

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """从Spec导入数据 - Service层持久化功能"""
        logger.debug(f"MatrixService.import_from_spec 被调用，参数: file_path={file_path}, page_number={page_number}, keyword={keyword}")
        result = self.spec_processing_service.import_from_spec(file_path, page_number, keyword)
        # 更新last_imported_spec_path引用
        self.last_imported_spec_path = self.spec_processing_service.last_imported_spec_path
        logger.debug(f"MatrixService.import_from_spec 完成，返回结果: {result}")
        return result
            
    def update_standard_versions(self):
        """
        更新测试方法的标准版本号
        
        Returns:
            dict: 更新结果，包含是否成功更新以及更新详情
        """
        result = self.spec_processing_service.update_standard_versions()
        if result["success"]:
            # 更新提取的数据
            self._parse_and_structure_matrix_data()
        return result
            
    def extract_test_methods_from_spec(self):
        """
        从已导入的规格书中提取测试方法标准并填充到Matrix中
        
        Returns:
            bool: 是否成功提取并填充测试方法
        """
        # 更新last_imported_spec_path引用
        self.spec_processing_service.last_imported_spec_path = self.last_imported_spec_path
        return self.spec_processing_service.extract_test_methods_from_spec()

    def _process_rows(self):
        """
        处理行数据，类似于VBA中的ProcessRows函数
        合并单元格内容并处理行数据
        """
        self.spec_processing_service._process_rows()
            
    def _check_duplicate_values(self):
        """
        检查重复值，从第1列到最后一列，从第1行到倒数第二行
        类似于VBA中的CheckDuplicateValues函数
        """
        self.spec_processing_service._check_duplicate_values()
            
    def _parse_and_structure_matrix_data(self):
        """
        解析Matrix原始数据并构造成结构化数据
        """
        # 解析Matrix原始数据并构造成结构化数据
        self.data_structure_service.parse_and_structure_matrix_data()
        
    def set_ltr_data(self, ltr_data):
        """
        设置LTR数据
        
        Args:
            ltr_data: LTR申请单数据
        """
        # 将LTR数据设置到导出控制器中
        self.export_controller.set_ltr_data(ltr_data)
        
    def _sync_table_to_model(self):
        """
        同步表格数据到模型 - Service层数据同步
        """
        # 更新导出控制器中的数据模型
        self.export_controller.update_data_model(self.data_model)
