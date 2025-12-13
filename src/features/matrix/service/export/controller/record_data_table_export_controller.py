from src.features.matrix.service.export.service.llcr_cr_export_service import LLCRCRExportService
from src.features.matrix.service.export.view.llcr_cr_record_parameters_dialog import LLCR_CR_RecordParametersDialog
from src.core.logger import logger
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
import os


class RecordDataTableExportController:
    """记录数据表格导出控制器 - Controller层"""

    def __init__(self, data_model, parent=None):
        self.data_model = data_model
        self.parent = parent
        self.llcr_export_service = LLCRCRExportService(data_model)
        self.cr_export_service = LLCRCRExportService(data_model)  # 使用LLCRCRExportService替代CRExportService
        # 设置Matrix数据结构到导出服务中
        self._set_matrix_data_structure()

    def _set_matrix_data_structure(self):
        """设置Matrix数据结构到导出服务中"""
        # 参考test_record_controller.py中的方式获取Matrix数据
        matrix_data_structure = None
        
        # 尝试从data_model获取Matrix数据
        if hasattr(self.data_model, 'rows'):
            # data_model是一个包含rows属性的对象（如MatrixService）
            matrix_data = self.data_model.rows
            logger.debug(f"从data_model.rows获取到Matrix数据，共 {len(matrix_data)} 行")
            
            # 创建MatrixDataStructure实例来解析数据
            from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
            matrix_data_structure = MatrixDataStructure()
            
            # 尝试获取DL编号和项目数据文件路径
            dl_number = "DL-UNKNOWN"
            project_data_file_path = None
            
            # 从data_model获取项目数据文件路径
            if hasattr(self.data_model, 'project_data_file_path') and self.data_model.project_data_file_path:
                project_data_file_path = self.data_model.project_data_file_path
                logger.debug(f"从data_model获取到项目数据文件路径: {project_data_file_path}")
                
                # 从项目数据文件中提取DL编号
                if os.path.exists(project_data_file_path):
                    try:
                        import json
                        with open(project_data_file_path, 'r', encoding='utf-8') as f:
                            project_data = json.load(f)
                            dl_number = project_data.get("DL", dl_number)
                            logger.debug(f"从项目数据文件中提取到DL编号: {dl_number}")
                    except Exception as e:
                        logger.error(f"读取项目数据文件时出错: {e}")
            
            matrix_data_structure.dl_number = dl_number
            matrix_data_structure.project_data_file_path = project_data_file_path
            logger.debug(f"设置DL编号: {dl_number}")
            logger.debug(f"设置项目数据文件路径: {project_data_file_path}")
            
            # 更新MatrixDataStructure中的数据
            warnings = matrix_data_structure.parse_matrix_to_structure(matrix_data)
            if warnings:
                logger.warning(f"Matrix数据验证警告: {warnings}")
        # 方式1: data_model本身就是MatrixDataStructure实例
        elif hasattr(self.data_model, 'group_steps') and hasattr(self.data_model, 'get_all_groups'):
            matrix_data_structure = self.data_model
            logger.debug("直接使用data_model作为MatrixDataStructure")
        # 方式2: data_model是MatrixService实例，包含data_structure属性
        elif hasattr(self.data_model, 'data_structure'):
            matrix_data_structure = self.data_model.data_structure
            logger.debug("使用MatrixService中的data_structure")
        # 方式3: data_model是ExportDataModel实例，包含原始数据模型
        elif hasattr(self.data_model, 'data_model') and hasattr(self.data_model.data_model, 'data_structure'):
            matrix_data_structure = self.data_model.data_model.data_structure
            logger.debug("使用ExportDataModel中的data_structure")
        
        # 设置MatrixDataStructure到导出服务
        if matrix_data_structure:
            self.llcr_export_service.set_matrix_data(matrix_data_structure)
            self.cr_export_service.set_matrix_data(matrix_data_structure)
            logger.debug("成功设置MatrixDataStructure到导出服务")
            
            # 打印Matrix结构信息（仅关键信息）
            groups = matrix_data_structure.get_all_groups()
            logger.debug(f"Matrix数据包含 {len(groups)} 个组别: {groups}")
        else:
            logger.warning("无法找到MatrixDataStructure对象")

    def export_llcr(self):
        """
        导出LLCR记录数据表格
        """
        try:
            logger.debug("开始导出LLCR记录数据表格")
            # 从Matrix数据中提取测试类别字典
            test_category_dict = self._extract_test_categories_from_matrix()
            logger.debug(f"从Matrix数据中提取的测试类别字典: {test_category_dict}")
            
            # 显示参数输入对话框
            dialog = LLCR_CR_RecordParametersDialog(self.parent, "LLCR", test_category_dict=test_category_dict)
            if dialog.exec_() != QDialog.Accepted:
                logger.debug("用户取消了LLCR导出操作")
                return True  # 用户取消操作，不算错误
                
            # 获取用户输入的参数
            params = dialog.get_parameters()
            logger.debug(f"获取到的用户参数: {params}")
            point_array = params["point_array"]
            sample_count = params["sample_count"]
            is_delta_r_checked = params["is_delta_r_checked"]
            
            # 设置默认文件路径和文件名
            default_dir = "D:\\outfile"
            default_filename = "test llcr.xlsx"
            
            # 确保默认目录存在
            if not os.path.exists(default_dir):
                os.makedirs(default_dir)
            
            # 构建默认完整路径
            default_path = os.path.join(default_dir, default_filename)
            
            # 获取保存文件路径，预设默认路径和文件名
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, 
                "保存LLCR记录数据表格", 
                default_path, 
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                logger.debug("用户取消了文件保存操作")
                return True  # 用户取消操作，不算错误
                
            # 确保文件扩展名正确
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            
            # 使用SmartPointParser解析输入的字符串，获取分类字典
            from src.utils.smart_point_parser import SmartPointParser
            parser = SmartPointParser()
            point_text = dialog.point_input.toPlainText().strip()
            parsed_result = parser.parse(point_text)
            category_dict = parsed_result['categories']
            logger.debug(f"解析后的类别字典: {category_dict}")
            
            # 检查是否有重复的工作表名称
            if self._has_duplicate_sheet_names(category_dict):
                QMessageBox.warning(self.parent, "警告", "检测到重复的工作表名称，请修改输入以确保每个分组有唯一的工作表名称。")
                return False
            
            # 执行导出
            logger.debug("开始调用llcr_export_service.export_llcr_to_excel方法")
            success = self.llcr_export_service.export_llcr_to_excel(
                file_path, 
                sample_count=sample_count, 
                point_array=point_array, 
                is_delta_r_checked=is_delta_r_checked,
                test_category_dict=category_dict if category_dict else None
            )
            logger.debug(f"LLCR导出完成，结果: {success}")
            
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
            logger.debug("开始导出CR记录数据表格")
            # 从Matrix数据中提取测试类别字典
            test_category_dict = self._extract_test_categories_from_matrix()
            logger.debug(f"从Matrix数据中提取的测试类别字典: {test_category_dict}")
            
            # 显示参数输入对话框
            dialog = LLCR_CR_RecordParametersDialog(self.parent, "CR", test_category_dict=test_category_dict)
            if dialog.exec_() != QDialog.Accepted:
                logger.debug("用户取消了CR导出操作")
                return True  # 用户取消操作，不算错误
                
            # 获取用户输入的参数
            params = dialog.get_parameters()
            logger.debug(f"获取到的用户参数: {params}")
            point_array = params["point_array"]
            sample_count = params["sample_count"]
            cr_current_value = params["cr_current_value"]
            
            # 设置默认文件路径和文件名
            default_dir = "D:\\outfile"
            default_filename = "test cr.xlsx"
            
            # 确保默认目录存在
            if not os.path.exists(default_dir):
                os.makedirs(default_dir)
            
            # 构建默认完整路径
            default_path = os.path.join(default_dir, default_filename)
            
            # 获取保存文件路径，预设默认路径和文件名
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, 
                "保存CR记录数据表格", 
                default_path, 
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                logger.debug("用户取消了文件保存操作")
                return True  # 用户取消操作，不算错误
                
            # 确保文件扩展名正确
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            
            # 使用SmartPointParser解析输入的字符串，获取分类字典
            from src.utils.smart_point_parser import SmartPointParser
            parser = SmartPointParser()
            point_text = dialog.point_input.toPlainText().strip()
            parsed_result = parser.parse(point_text)
            category_dict = parsed_result['categories']
            logger.debug(f"解析后的类别字典: {category_dict}")
            
            # 检查是否有重复的工作表名称
            if self._has_duplicate_sheet_names(category_dict):
                QMessageBox.warning(self.parent, "警告", "检测到重复的工作表名称，请修改输入以确保每个分组有唯一的工作表名称。")
                return False
            
            # 执行导出 - 使用LLCRExportService的export_to_excel方法，传递cr_current_value参数
            logger.debug("开始调用cr_export_service.export_cr_to_excel方法")
            success = self.cr_export_service.export_cr_to_excel(
                file_path, 
                sample_count=sample_count, 
                point_array=point_array, 
                cr_current_value=cr_current_value,  # 保留CR特有的参数
                test_category_dict=category_dict if category_dict else None  # 添加分类字典参数
            )
            logger.debug(f"CR导出完成，结果: {success}")
            
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
            # 获取MatrixDataStructure对象
            matrix_data_structure = None
            if hasattr(self.data_model, 'group_steps') and hasattr(self.data_model, 'get_all_groups'):
                matrix_data_structure = self.data_model
            elif hasattr(self.data_model, 'data_structure'):
                matrix_data_structure = self.data_model.data_structure
            elif hasattr(self.data_model, 'data_model') and hasattr(self.data_model.data_model, 'data_structure'):
                matrix_data_structure = self.data_model.data_model.data_structure
            
            # 如果找到了MatrixDataStructure对象，则使用它提取数据
            if matrix_data_structure:
                test_category_dict = {}
                for group_name in matrix_data_structure.get_all_groups():
                    steps = matrix_data_structure.get_group_steps(group_name)
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

    def _has_duplicate_sheet_names(self, category_dict):
        """
        检查是否有重复的工作表名称
        
        Args:
            category_dict: 类别字典
            
        Returns:
            bool: 如果有重复的工作表名称返回True，否则返回False
        """
        if not category_dict:
            return False
            
        sheet_names = list(category_dict.keys())
        # 检查是否有重复的名称（考虑Excel工作表名称长度限制31个字符）
        trimmed_names = [name[:31] for name in sheet_names]
        return len(trimmed_names) != len(set(trimmed_names))

    def update_data_model(self, data_model):
        """
        更新数据模型

        Args:
            data_model: 新的数据模型
        """
        self.data_model = data_model
        # 重新创建导出服务实例以确保使用最新的数据
        self.llcr_export_service = LLCRCRExportService(data_model)
        self.cr_export_service = LLCRCRExportService(data_model)  # 使用LLCRCRExportService替代CRExportService
        # 设置Matrix数据结构到导出服务中
        self._set_matrix_data_structure()