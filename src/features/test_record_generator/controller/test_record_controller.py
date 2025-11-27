# src/features/test_record_generator/controller/test_record_controller.py
"""
Test Record生成控制器
控制Test Record生成功能的业务流程
"""

from src.features.test_record_generator.service.test_record_service import TestRecordService
from src.features.test_record_generator.view.test_record_dialog import TestRecordDialog
from src.core.logger import logger
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from PyQt5.QtWidgets import QMessageBox
import os


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
            # 直接使用固定路径生成Test Record文档
            output_path = r"D:\outfile\testrecord.docx"
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 获取Matrix数据
            if self.matrix_service:
                matrix_data = self.matrix_service.data_model.rows
                logger.info(f"获取到Matrix数据，共 {len(matrix_data)} 行")
                
                # 创建MatrixDataStructure实例来解析数据
                matrix_structure = MatrixDataStructure()
                warnings = matrix_structure.update_from_matrix(matrix_data)
                
                # 记录解析结果
                group_count = len(matrix_structure.group_steps)
                logger.info(f"解析完成，共找到 {group_count} 个组别: {list(matrix_structure.group_steps.keys())}")
                
                # 如果有警告信息，显示给用户并阻止继续
                if warnings:
                    warning_text = "\n".join(warnings)
                    logger.warning(f"Matrix数据验证警告:\n{warning_text}")
                    
                    # 显示警告对话框，只用一个确认按钮
                    if parent:
                        msg_box = QMessageBox(parent)
                        msg_box.setIcon(QMessageBox.Warning)
                        msg_box.setWindowTitle("数据验证警告")
                        msg_box.setText(f"发现以下数据问题：\n\n{warning_text}")
                        msg_box.setStandardButtons(QMessageBox.Ok)
                        msg_box.exec_()
                        
                        logger.info("用户已确认警告信息，返回Matrix编辑界面")
                        return False  # 阻止继续生成Test Record
                
                logger.info("Matrix数据结构已更新")
                logger.debug(f"组别步骤详情: {matrix_structure.group_steps}")
                logger.debug(f"样品数量详情: {matrix_structure.group_sample_sizes}")
                
                # 调用服务生成文档，传入已解析的数据结构
                logger.info("开始调用Test Record服务生成文档")
                success = self.service.generate_test_record_with_structure(matrix_structure, output_path)
                
                if success:
                    logger.info("Test Record文档生成成功")
                else:
                    logger.error("Test Record文档生成失败")
                    
                return success
            else:
                logger.error("Matrix service not available")
                return False
                
        except Exception as e:
            logger.error(f"Error in test record generation controller: {e}")
            return False