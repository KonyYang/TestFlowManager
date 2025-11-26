# src/features/test_record_generator/controller/test_record_controller.py
"""
Test Record生成控制器
控制Test Record生成功能的业务流程
"""

from src.features.test_record_generator.service.test_record_service import TestRecordService
from src.features.test_record_generator.view.test_record_dialog import TestRecordDialog
from src.core.logger import logger


class TestRecordController:
    """
    Test Record生成控制器
    """

    def __init__(self, matrix_service=None):
        self.service = TestRecordService()
        self.matrix_service = matrix_service  # 关联的Matrix服务

    def generate_test_record(self, parent=None):
        """
        生成Test Record文档
        
        Args:
            parent: 父窗口
            
        Returns:
            是否成功生成
        """
        try:
            # 显示对话框
            dialog = TestRecordDialog(parent)
            if dialog.exec_() == TestRecordDialog.Accepted:
                output_path = dialog.get_output_path()
                if output_path:
                    # 获取Matrix数据
                    if self.matrix_service:
                        matrix_data = self.matrix_service.data_model.rows
                                    
                        # 先提取测试数据
                        extracted_data = self.service.extract_test_data(matrix_data)
                        logger.info(f"提取的测试数据: {extracted_data}")
                                    
                        # 调用服务生成文档
                        success = self.service.generate_test_record(matrix_data, output_path)
                        return success
                    else:
                        logger.error("Matrix service not available")
                        return False
                else:
                    logger.warning("Output path not specified")
                    QMessageBox.warning(parent, "警告", "请选择输出路径")
                    return False
            else:
                # 用户取消操作
                return False
                
        except Exception as e:
            logger.error(f"Error in test record generation controller: {e}")
            return False