from src.features.matrix.model.matrix_data import MatrixData
from src.features.matrix.service.matrix_cell_service import MatrixCellService
from src.features.matrix.service.matrix_initializer import MatrixInitializer
from src.features.matrix.service.base.matrix_base_operation_service import MatrixBaseOperationService
from src.features.matrix.service.base.matrix_formatting_service import MatrixFormattingService
from src.features.matrix.service.export.controller.export_controller import ExportController
from src.features.matrix.service.export.model.export_data_model import ExportDataModel
from src.features.matrix.service.spec.matrix_spec_processing_service import MatrixSpecProcessingService
from src.features.matrix.service.processing.matrix_data_structure_service import MatrixDataStructureService
from src.features.matrix.service.matrix_import_service import MatrixImportService
from src.core.logger import logger


class MatrixService:
    """Matrix服务层 - Service层"""

    _shared_instance = None

    @classmethod
    def shared(cls) -> "MatrixService":
        """显式获取当前共享 MatrixService 实例。"""
        if cls._shared_instance is None:
            cls._shared_instance = cls()
        return cls._shared_instance

    @classmethod
    def create_isolated(cls) -> "MatrixService":
        """创建独立的 MatrixService 实例，不复用共享单例。"""
        return cls()

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
        self.import_service = MatrixImportService(
            data_model=self.data_model,
            spec_processing_service=self.spec_processing_service,
        )
        
        # 标记为已初始化
        self._initialized = True

    @property
    def last_imported_spec_path(self):
        """
        最近导入的规格书文件路径 - 兼容性属性

        实际数据存储在 spec_processing_service 中，此属性仅为兼容性提供访问
        """
        return self.spec_processing_service.last_imported_spec_path

    @last_imported_spec_path.setter
    def last_imported_spec_path(self, value):
        """
        设置最近导入的规格书文件路径 - 兼容性属性

        实际数据存储在 spec_processing_service 中
        """
        self.spec_processing_service.last_imported_spec_path = value

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

    def import_from_excel(self, file_path):
        """从 Excel 导入 Matrix 数据。"""
        return self.import_service.import_from_excel(file_path)



