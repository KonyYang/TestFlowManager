from src.features.matrix.service.export.service.llcr_export_service import LLCRExportService
from src.features.matrix.service.export.service.cr_export_service import CRExportService
from src.features.matrix.service.export.view.record_data_table_parameters_dialog import RecordDataTableParametersDialog
from src.core.logger import logger
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
import os


class RecordDataTableExportController:
    """记录数据表格导出控制器 - Controller层"""

    def __init__(self, data_model, parent=None):
        self.data_model = data_model
        self.parent = parent
        self.llcr_export_service = LLCRExportService(data_model)
        self.cr_export_service = CRExportService(data_model)

    def export_llcr(self):
        """
        导出LLCR记录数据表格
        """
        try:
            # 从Matrix数据中提取测试类别字典
            test_category_dict = self._extract_test_categories_from_matrix()
            
            # 显示参数输入对话框
            dialog = RecordDataTableParametersDialog(self.parent, "LLCR", test_category_dict=test_category_dict)
            if dialog.exec_() != QDialog.Accepted:
                return True  # 用户取消操作，不算错误
                
            # 获取用户输入的参数
            params = dialog.get_parameters()
            point_array = params["point_array"]
            sample_count = params["sample_count"]
            is_delta_r_checked = params["is_delta_r_checked"]
            
            # 获取保存文件路径
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, 
                "保存LLCR记录数据表格", 
                "", 
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return True  # 用户取消操作，不算错误
                
            # 确保文件扩展名正确
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            
            # 执行导出
            success = self.llcr_export_service.export_to_excel(
                file_path, 
                sample_count=sample_count, 
                point_array=point_array, 
                is_delta_r_checked=is_delta_r_checked
            )
            
            if success:
                QMessageBox.information(self.parent, "成功", f"LLCR记录数据表格已成功导出到:\n{file_path}")
                return True
            else:
                QMessageBox.critical(self.parent, "错误", "导出LLCR记录数据表格失败")
                return False
                
        except Exception as e:
            logger.error(f"导出LLCR记录数据表格时出错: {e}", exc_info=True)
            QMessageBox.critical(self.parent, "错误", f"导出LLCR记录数据表格时发生错误:\n{str(e)}")
            return False

    def export_cr(self):
        """
        导出CR记录数据表格
        """
        try:
            # 从Matrix数据中提取测试类别字典
            test_category_dict = self._extract_test_categories_from_matrix()
            
            # 显示参数输入对话框
            dialog = RecordDataTableParametersDialog(self.parent, "CR", test_category_dict=test_category_dict)
            if dialog.exec_() != QDialog.Accepted:
                return True  # 用户取消操作，不算错误
                
            # 获取用户输入的参数
            params = dialog.get_parameters()
            point_array = params["point_array"]
            sample_count = params["sample_count"]
            cr_current_value = params["cr_current_value"]
            
            # 获取保存文件路径
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, 
                "保存CR记录数据表格", 
                "", 
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return True  # 用户取消操作，不算错误
                
            # 确保文件扩展名正确
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            
            # 执行导出
            success = self.cr_export_service.export_to_excel(
                file_path, 
                sample_count=sample_count, 
                point_array=point_array, 
                cr_current_value=cr_current_value
            )
            
            if success:
                QMessageBox.information(self.parent, "成功", f"CR记录数据表格已成功导出到:\n{file_path}")
                return True
            else:
                QMessageBox.critical(self.parent, "错误", "导出CR记录数据表格失败")
                return False
                
        except Exception as e:
            logger.error(f"导出CR记录数据表格时出错: {e}", exc_info=True)
            QMessageBox.critical(self.parent, "错误", f"导出CR记录数据表格时发生错误:\n{str(e)}")
            return False

    def _extract_test_categories_from_matrix(self):
        """
        从Matrix数据中提取测试类别字典
        
        Returns:
            dict: 测试类别字典，键为类别名称，值为点位数组
        """
        try:
            # 如果数据模型有获取测试类别和点位的方法，则使用它
            # 这里我们假设MatrixDataStructure有相应的方法
            if hasattr(self.data_model, 'group_steps'):
                test_category_dict = {}
                for group_name, steps in self.data_model.group_steps.items():
                    # 从步骤中提取唯一的测试点位
                    points = list(set([step.get("Test", "") for step in steps]))
                    # 过滤掉空字符串
                    points = [point for point in points if point]
                    test_category_dict[group_name] = points
                return test_category_dict
            
            # 如果没有找到合适的结构，返回空字典
            return {}
        except Exception as e:
            logger.error(f"从Matrix数据中提取测试类别时出错: {e}", exc_info=True)
            # 出错时返回空字典，让对话框使用默认点位
            return {}

    def update_data_model(self, data_model):
        """
        更新数据模型

        Args:
            data_model: 新的数据模型
        """
        self.data_model = data_model
        # 重新创建导出服务实例以确保使用最新的数据
        self.llcr_export_service = LLCRExportService(data_model)
        self.cr_export_service = CRExportService(data_model)