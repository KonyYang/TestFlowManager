# src/features/matrix/controller/matrix_controller.py
from src.features.matrix.service.matrix_service import MatrixService
from src.features.matrix.service.export.controller.export_controller import ExportController
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from src.core.logger import logger
from src.core.project_context import ProjectContext, get_current_project_context
import os


class MatrixController:
    """Matrix核心控制器
    
    负责Matrix功能的核心操作，包括数据导入/导出、显示控制、单元格操作等。
    这是Matrix功能的主要控制器，直接处理用户的交互和业务逻辑。"""

    def __init__(self, parent=None):
        self.parent = parent
        # 当前仍使用共享 MatrixService，后续可切换为显式注入。
        self.service = MatrixService.shared()
        # 初始化导出控制器
        self.export_controller = ExportController(self.service.data_model, parent)
        # 初始化LTR集成服务
        self.ltr_integration_service = None
        # 初始化parent_view属性
        self.parent_view = parent
        self.project_context = None

    def activate_matrix_workspace(self):
        """激活主窗口中的 Matrix 工作区。"""
        try:
            if (
                self.parent_view
                and hasattr(self.parent_view, "activate_matrix_workspace")
                and hasattr(self.parent_view, "has_matrix_workspace")
                and self.parent_view.has_matrix_workspace()
            ):
                activated = self.parent_view.activate_matrix_workspace()
                if activated:
                    logger.info("Activated Matrix workspace in main window")
                    return True

            logger.warning("Matrix workspace unavailable in current parent view")
            return False
        except Exception as e:
            logger.error(f"Error showing matrix dialog: {e}", exc_info=True)
            raise

    def get_matrix_data(self):
        """获取Matrix数据 - Controller层数据提供"""
        return self.service.data_model

    def get_matrix_service(self):
        """兼容下游仍需显式 service 对象的场景。"""
        return self.service

    def sync_table_to_model(self):
        """同步表格数据到模型。"""
        self.service._sync_table_to_model()

    def initialize_matrix(self):
        """初始化 Matrix 数据结构。"""
        return self.service.initialize_matrix()

    def extract_test_methods_from_spec(self):
        """从规格书中提取测试方法。"""
        return self.service.extract_test_methods_from_spec()

    def update_standard_versions(self):
        """更新标准版本号。"""
        return self.service.update_standard_versions()

    def get_undo_cell_operation_text(self):
        return self.service.get_undo_cell_operation_text()

    def get_redo_cell_operation_text(self):
        return self.service.get_redo_cell_operation_text()

    def add_row(self):
        self.service.add_row()

    def insert_row(self, row):
        self.service.insert_row(row)

    def remove_row(self, row):
        self.service.remove_row(row)

    def move_row(self, row, new_position):
        return self.service.move_row(row, new_position)

    def copy_row(self, row):
        return self.service.copy_row(row)

    def paste_row(self, row, copied_row_data):
        return self.service.paste_row(row, copied_row_data)

    def add_column(self):
        self.service.add_column()

    def insert_column(self, col):
        self.service.insert_column(col)

    def remove_column(self, col):
        self.service.remove_column(col)

    def move_column(self, col, new_position):
        return self.service.move_column(col, new_position)

    def copy_column(self, col):
        return self.service.copy_column(col)

    def paste_column(self, col, copied_col_data):
        return self.service.paste_column(col, copied_col_data)

    def set_cell_value(self, row, col, value):
        return self.service.set_cell_value(row, col, value)

    def export_to_excel(self, file_path, export_type="matrix_excel"):
        """导出Matrix数据到Excel文件
        
        Args:
            file_path (str): 导出文件路径
            export_type (str): 导出类型，默认为"matrix_excel"
            
        Returns:
            bool: 是否导出成功
        """
        # 在导出前确保数据是最新的
        self.service._sync_table_to_model()
        # 更新提取的数据
        self.service._parse_and_structure_matrix_data()
        return self.service.export_to_excel(file_path, export_type)

    def import_from_excel(self, file_path):
        """从Excel导入数据 - Controller层业务流程"""
        return self.service.import_from_excel(file_path)

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """从规格书文件导入数据到Matrix
        
        Args:
            file_path (str): 规格书文件路径
            page_number (int, optional): 指定页码
            keyword (str, optional): 关键词筛选
            
        Returns:
            bool: 是否导入成功
        """
        return self.service.import_from_spec(file_path, page_number, keyword)
        
    def merge_or_split_cells(self, table_widget):
        """合并或拆分单元格 - Controller层业务流程"""
        return self.service.merge_or_split_cells(table_widget)
        
    def can_undo_cell_operation(self):
        """检查是否可以撤销单元格操作 - Controller层业务流程"""
        return self.service.can_undo_cell_operation()
        
    def can_redo_cell_operation(self):
        """检查是否可以重做单元格操作 - Controller层业务流程"""
        return self.service.can_redo_cell_operation()
        
    def undo_cell_operation(self):
        """撤销单元格操作 - Controller层业务流程"""
        return self.service.undo_cell_operation()
        
    def redo_cell_operation(self):
        """重做单元格操作 - Controller层业务流程"""
        return self.service.redo_cell_operation()

    def show_test_group_selector(self):
        """显示测试组选择器 - Controller层协调"""
        # 这个方法可以直接通过View层调用对话框，不需要额外的业务逻辑
        pass
        
    def set_ltr_integration_service(self, ltr_integration_service):
        """
        设置LTR项目集成服务
        
        Args:
            ltr_integration_service: LTR项目集成服务实例
        """
        # 只在服务实例发生变化时才进行设置
        if self.ltr_integration_service != ltr_integration_service:
            logger.debug("MatrixController: Setting LTR integration service")
            self.ltr_integration_service = ltr_integration_service
        else:
            logger.debug("MatrixController: LTR integration service unchanged, skipping update")

    def set_ltr_data(self, ltr_data):
        """设置 LTR 数据到 Matrix 服务。"""
        self.service.set_ltr_data(ltr_data)

    def set_project_context(self, project_context: ProjectContext):
        self.project_context = project_context
        self.export_controller.set_project_context(project_context)

    def get_project_context(self):
        return self.project_context or get_current_project_context()
        
    def initialize_with_ltr_data(self):
        """
        使用LTR项目数据初始化Matrix
        
        Returns:
            bool: 是否成功初始化
        """
        if not self.ltr_integration_service or not self.ltr_integration_service.is_project_loaded():
            return False
            
        # 获取LTR数据
        ltr_data = self.ltr_integration_service.get_ltr_data()
        if not ltr_data:
            return False
            
        # 初始化Matrix
        self.service.initialize_matrix()
        
        # 可以在这里根据LTR数据预填充Matrix的一些字段
        # 例如设置测试项目类型等信息
        test_info = self.ltr_integration_service.get_test_info()
        # 这里可以根据需要进行预填充操作
        
        return True
        
    def set_ltr_number(self, ltr_number):
        """
        设置LTR编号
        
        Args:
            ltr_number (str): LTR编号
        """
        self.ltr_number = ltr_number

    def auto_export_matrix_data_on_shutdown(self):
        """
        在应用程序关闭时自动导出Matrix数据
        
        自动将当前Matrix数据导出到项目目录下的matrix.xlsx文件中，
        如果没有获取到有效项目目录，则不执行保存操作
        """
        try:
            # 获取当前项目路径
            project_context = self.get_project_context()
            current_project = project_context.project_path if project_context else None
            
            logger.info(f"开始自动导出Matrix数据，当前项目路径: {current_project}")
            
            # 如果没有项目路径，则直接返回，不执行保存操作
            if not current_project or not os.path.exists(current_project):
                logger.debug("没有获取到有效的项目目录，跳过Matrix数据自动保存")
                return True
                
            # 根据路径层级判断保存位置
            # 将路径按分隔符分割，计算目录层级数
            path_parts = current_project.replace('/', '\\').split('\\')
            path_parts = [part for part in path_parts if part]  # 移除空字符串
            
            logger.info(f"路径层级分析: {path_parts}, 层级数: {len(path_parts)}")
            
            # 如果路径有4层（D:\TestFlowManager\Projects\DL-2025-12-046\DL-2025-12-046），取父目录
            # 如果路径有3层（D:\TestFlowManager\Projects\DL-2025-12-046），直接使用当前目录
            if project_context and project_context.matrix_file_path and len(path_parts) != 5:
                matrix_file_path = project_context.matrix_file_path
                logger.info(f"使用ProjectContext中的matrix文件路径: {matrix_file_path}")
            elif len(path_parts) == 5:
                # 4层路径，取父目录
                matrix_file_path = os.path.join(os.path.dirname(current_project), "matrix.xlsx")
                logger.info(f"检测到4层路径结构，将文件保存到父目录: {matrix_file_path}")
            else:
                # 3层或其它情况，直接在当前项目目录下保存
                matrix_file_path = os.path.join(current_project, "matrix.xlsx")
                logger.info(f"检测到{len(path_parts)}层路径结构，将文件保存到当前目录: {matrix_file_path}")
            
            # 同步表格数据到模型
            if self.parent and hasattr(self.parent, 'sync_to_model'):
                self.parent.sync_to_model()
            
            # 更新导出控制器的数据模型
            self.export_controller.update_data_model(self.service.data_model)
            
            # 执行导出操作
            success = self.export_controller.export_by_type(matrix_file_path, "matrix_excel")
            
            if success:
                logger.info(f"成功自动导出Matrix数据到: {matrix_file_path}")
                return True
            else:
                logger.error(f"自动导出Matrix数据失败: {matrix_file_path}")
                return False
                
        except Exception as e:
            logger.error(f"自动导出Matrix数据时出错: {e}", exc_info=True)
            return False

    def handle_export_matrix_to_excel(self):
        """
        处理导出Matrix到Excel事件
        
        显示文件保存对话框并导出当前Matrix数据到Excel文件
        
        Returns:
            bool: 是否导出成功
        """
        try:
            # 同步表格数据到模型
            if self.parent and hasattr(self.parent, 'sync_to_model'):
                self.parent.sync_to_model()
            
            # 获取当前项目路径作为默认保存路径
            project_context = self.get_project_context()
            current_project = project_context.project_path if project_context else None
            
            # 构造默认文件名
            if project_context and project_context.matrix_file_path and os.path.exists(current_project):
                default_filename = project_context.matrix_file_path
            elif current_project and os.path.exists(current_project):
                default_filename = os.path.join(current_project, "matrix.xlsx")
            else:
                default_filename = "matrix.xlsx"
                
            # 弹出文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent if self.parent else None,
                "导出窗口矩阵",
                default_filename,
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                # 更新导出控制器的数据模型
                self.export_controller.update_data_model(self.service.data_model)
                
                # 执行导出操作
                success = self.export_controller.export_by_type(file_path, "matrix_excel")
                
                if success:
                    return True
                else:
                    # 检查文件是否被占用
                    try:
                        # 尝试以独占模式打开文件
                        with open(file_path, 'r+b') as f:
                            pass
                        # 如果能打开，说明是其他问题
                        QMessageBox.warning(
                            self.parent if self.parent else None,
                            "错误",
                            "导出失败，请检查文件路径或权限"
                        )
                    except PermissionError:
                        # 文件被其他程序占用
                        QMessageBox.warning(
                            self.parent if self.parent else None,
                            "错误",
                            "导出失败，文件已被其他程序占用（可能已在Excel中打开），请关闭文件后重试"
                        )
                    except FileNotFoundError:
                        # 文件不存在，应该是其他问题
                        QMessageBox.warning(
                            self.parent if self.parent else None,
                            "错误",
                            "导出失败，请检查文件路径是否正确"
                        )
                    except Exception:
                        # 其他未知错误
                        QMessageBox.warning(
                            self.parent if self.parent else None,
                            "错误",
                            "导出失败，发生未知错误"
                        )
                    
            return False
        except Exception as e:
            from src.core.logger import logger
            logger.error(f"导出窗口矩阵时出错: {e}", exc_info=True)
            QMessageBox.warning(
                self.parent if self.parent else None,
                "错误",
                f"导出过程中发生异常: {str(e)}"
            )
            return False

    def handle_export_llcr(self):
        """
        处理导出LLCR事件
        
        Returns:
            bool: 是否导出成功
        """
        try:
            # 同步表格数据到模型
            if self.parent and hasattr(self.parent, 'sync_to_model'):
                self.parent.sync_to_model()
            
            # 更新导出控制器的数据模型
            self.export_controller.update_data_model(self.service.data_model)
            
            # 执行LLCR导出操作
            success = self.export_controller.export_by_type(None, "llcr")
            
            return success
        except Exception as e:
            logger.error(f"导出LLCR时出错: {e}", exc_info=True)
            QMessageBox.warning(
                self.parent if self.parent else None,
                "错误",
                f"导出LLCR过程中发生异常: {str(e)}"
            )
            return False

    def handle_export_cr(self):
        """
        处理导出CR事件
        
        Returns:
            bool: 是否导出成功
        """
        try:
            # 同步表格数据到模型
            if self.parent and hasattr(self.parent, 'sync_to_model'):
                self.parent.sync_to_model()
            
            # 更新导出控制器的数据模型
            self.export_controller.update_data_model(self.service.data_model)
            
            # 执行CR导出操作
            success = self.export_controller.export_by_type(None, "cr")
            
            return success
        except Exception as e:
            logger.error(f"导出CR时出错: {e}", exc_info=True)
            QMessageBox.warning(
                self.parent if self.parent else None,
                "错误",
                f"导出CR过程中发生异常: {str(e)}"
            )
            return False
