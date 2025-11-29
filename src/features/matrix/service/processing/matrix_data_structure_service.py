from src.features.matrix.model.matrix_data import MatrixData
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from src.core.logger import logger


class MatrixDataStructureService:
    """Matrix数据结构服务 - 处理数据结构化等相关功能"""

    def __init__(self, data_model: MatrixData, data_structure: MatrixDataStructure):
        self.data_model = data_model
        self.data_structure = data_structure

    def update_extracted_data(self):
        """
        更新提取的数据到统一数据结构中
        """
        try:
            logger.debug("开始更新提取的数据")
            # 使用Matrix数据更新数据结构
            warnings = self.data_structure.update_from_matrix(self.data_model.rows)
            
            # 记录警告信息
            if warnings:
                for warning in warnings:
                    logger.warning(warning)
                    
            logger.debug("提取的数据更新完成")
            return warnings
        except Exception as e:
            logger.error(f"更新提取数据时出错: {e}", exc_info=True)
            return []