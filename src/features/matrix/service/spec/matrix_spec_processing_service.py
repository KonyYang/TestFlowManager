from src.features.matrix.model.matrix_data import MatrixData
from src.features.matrix.service.template.template_filler import TemplateFiller
from src.features.matrix.service.processing.matrix_test_method_manager import MatrixTestMethodManager
from src.core.logger import logger


class MatrixSpecProcessingService:
    """Matrix规格书处理服务 - 处理规格书相关功能"""

    def __init__(self, data_model: MatrixData, template_filler: TemplateFiller):
        self.data_model = data_model
        self.data_processor = MatrixTestMethodManager(data_model, template_filler)
        self.last_imported_spec_path = None

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """从Spec导入数据 - Service层持久化功能"""
        try:
            logger.info(f"开始从Spec导入数据: {file_path}")
            
            # 保存导入的规格书文件路径
            self.last_imported_spec_path = file_path
            
            # 实现Spec文件导入逻辑
            # 调用spec_extractor来处理不同格式的文件
            from src.features.matrix.service.spec.spec_extractor import SpecExtractor
            extractor = SpecExtractor()
            # 传递页码和关键字参数
            data_result = extractor.extract_from_document(file_path, page_number, keyword)
            
            # 如果成功提取数据，则更新数据模型
            if data_result is not None:
                # 处理不同的返回格式
                if isinstance(data_result, dict) and 'data' in data_result:
                    # 包含合并单元格信息的格式
                    data = data_result['data']
                    merged_cells = data_result.get('merged_cells', [])
                else:
                    # 简单数据格式
                    data = data_result
                    merged_cells = []
                
                # 清空现有数据
                self.data_model.headers = []
                self.data_model.rows = []
                
                # 设置表头（使用字母标识，而不是使用第一行数据作为表头）
                if len(data) > 0:
                    for i in range(len(data[0])):  # 根据数据列数创建表头
                        self.data_model.headers.append(self.data_model._column_index_to_letter(i))
                    logger.info(f"设置表头，列数: {len(self.data_model.headers)}")
                
                # 设置数据行（所有原始数据行都作为数据行）
                if len(data) > 0:
                    self.data_model.rows = data  # 数据行就是所有提取的数据
                    logger.info(f"设置数据行，行数: {len(self.data_model.rows)}")
                
                # 确保有默认列数
                while len(self.data_model.headers) < 8:
                    self.data_model.headers.append(self.data_model._column_index_to_letter(len(self.data_model.headers)))
                
                # 确保有默认行
                if len(self.data_model.rows) == 0:
                    # 添加默认行
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    logger.info("添加默认行数据")

                # 保存合并单元格信息（如果需要）
                # 注意：这部分可能需要额外处理，取决于具体需求

                logger.info("Spec数据导入完成")
                return True
            else:
                logger.warning("未能从Spec文档提取数据，保持原有数据不变")
                return False
        except Exception as e:
            logger.error(f"导入Spec失败: {e}")
            return False
            
    def update_standard_versions(self):
        """
        更新测试方法的标准版本号
        
        Returns:
            dict: 更新结果，包含是否成功更新以及更新详情
        """
        result = self.data_processor.update_standard_versions()
        return result
            
    def extract_test_methods_from_spec(self):
        """
        从已导入的规格书中提取测试方法标准并填充到Matrix中
        
        Returns:
            bool: 是否成功提取并填充测试方法
        """
        return self.data_processor.extract_test_methods_from_spec(self.last_imported_spec_path)

    def _process_rows(self):
        """
        处理行数据，类似于VBA中的ProcessRows函数
        合并单元格内容并处理行数据
        """
        self.data_processor._process_rows()
            
    def _check_duplicate_values(self):
        """
        检查重复值，从第1列到最后一列，从第1行到倒数第二行
        类似于VBA中的CheckDuplicateValues函数
        """
        self.data_processor._check_duplicate_values()