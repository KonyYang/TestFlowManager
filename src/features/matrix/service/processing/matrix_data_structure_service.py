from src.features.matrix.model.matrix_data import MatrixData
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from src.core.logger import logger


class MatrixDataStructureService:
    """Matrix数据结构服务 - 处理数据结构化等相关功能"""

    def __init__(self, data_model: MatrixData, data_structure: MatrixDataStructure):
        self.data_model = data_model
        self.data_structure = data_structure

    def parse_and_structure_matrix_data(self):
        """
        解析Matrix原始数据并构造成结构化数据
        """
        try:
            logger.debug("开始结构化Matrix数据")
            # Matrix数据结构化
            warnings = self.data_structure.parse_matrix_to_structure(self.data_model.rows)
            
            # 记录警告信息
            if warnings:
                for warning in warnings:
                    logger.warning(warning)
                    
            logger.debug("Matrix数据完成结构化")
            return warnings
        except Exception as e:
            logger.error(f"Matrix数据结构化时出错: {e}", exc_info=True)
            return []