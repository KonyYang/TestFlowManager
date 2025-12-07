# src/features/matrix/view/managers/import_export_manager.py
import os
from src.core.logger import logger
from src.core.state_manager import state_manager
from src.features.matrix.service.document_parsers.excel_parser import ExcelParser


class ImportExportManager:
    """导入/导出管理器 - 处理Matrix视图的导入和导出操作"""
    
    def __init__(self, view, controller):
        self.view = view
        self.controller = controller

    def auto_import_matrix_from_project(self):
        """
        从项目文件夹自动导入matrix.xlsx文件
        """
        try:
            logger.debug("尝试从项目文件夹自动导入matrix.xlsx")
            
            # 获取当前项目路径
            current_project = state_manager.get_state("current_project")
            if not current_project:
                logger.debug("没有当前项目，跳过自动导入")
                return
                
            # 构造matrix.xlsx文件路径
            matrix_file_path = os.path.join(current_project, "matrix.xlsx")
            
            # 检查文件是否存在
            if os.path.exists(matrix_file_path):
                logger.info(f"发现项目中的matrix.xlsx文件: {matrix_file_path}")
                
                # 导入文件
                parser = ExcelParser()
                result = parser.parse(matrix_file_path)
                
                if result and 'data' in result and result['data']:
                    # 更新数据模型
                    self.controller.data_model.rows = result['data']
                    if 'headers' in result and result['headers']:
                        self.controller.data_model.headers = result['headers']
                    else:
                        # 如果没有提供表头，使用默认的字母标识
                        self.controller.data_model.headers = [self.controller.data_model._column_index_to_letter(i) 
                                                        for i in range(len(result['data'][0]) if result['data'] else 7)]
                    
                    # 更新合并单元格信息
                    if 'merged_cells' in result:
                        self.controller.data_model.merged_cells_info = result['merged_cells']
                        
                    # 更新表格显示
                    self.view._update_table()
                    logger.info("成功自动导入项目中的matrix.xlsx文件")
                else:
                    logger.warning("matrix.xlsx文件中没有有效数据")
            else:
                logger.debug(f"项目中没有matrix.xlsx文件: {matrix_file_path}")
        except Exception as e:
            logger.error(f"自动导入matrix.xlsx文件时出错: {e}")