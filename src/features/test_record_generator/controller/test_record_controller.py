# src/features/test_record_generator/controller/test_record_controller.py
"""
Test Record生成控制器
控制Test Record生成功能的业务流程
"""

from src.features.test_record_generator.service.test_record_service import TestRecordService
from src.core.logger import logger
from src.core.output_paths import OutputPathResolver
from src.core.project_context import ProjectContext, get_current_project_context
from src.core.project_document_context import ProjectDocumentContext
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from PyQt5.QtWidgets import QMessageBox, QFileDialog
import os


class TestRecordController:
    """
    Test Record生成控制器
    """

    def __init__(self, matrix_service=None, matrix_controller=None, project_context: ProjectContext = None):
        self.service = TestRecordService()
        self.matrix_service = matrix_service  # 关联的Matrix服务
        self.matrix_controller = matrix_controller
        self.project_context = project_context

    def set_project_context(self, project_context: ProjectContext) -> None:
        self.project_context = project_context

    def _get_project_context(self) -> ProjectContext:
        if self.project_context:
            return self.project_context

        if self.matrix_controller:
            matrix_project_context = self.matrix_controller.get_project_context()
            if matrix_project_context:
                return matrix_project_context

        if self.matrix_service and hasattr(self.matrix_service, "project_context"):
            matrix_project_context = getattr(self.matrix_service, "project_context", None)
            if matrix_project_context:
                return matrix_project_context

        return get_current_project_context()

    def _get_default_output_path(self, document_context: ProjectDocumentContext):
        """
        根据项目上下文生成默认输出路径
        
        Args:
            document_context: 文档生成上下文
            
        Returns:
            默认输出路径
        """
        try:
            output_filename = f"{document_context.dl_number} Test Record.docx"
            output_path = OutputPathResolver.build_submitted_material_output_path(
                self._get_project_context(),
                output_filename,
                create_dir=True,
            )
            if output_path:
                logger.debug(f"构造的默认输出路径: {output_path}")
                return os.path.normpath(output_path)

            return OutputPathResolver.build_default_output_path("testrecord.docx")
        except Exception as e:
            logger.error(f"生成默认输出路径时出错: {e}")
            return OutputPathResolver.build_default_output_path("testrecord.docx")

    def generate_test_record(self, parent=None):
        """
        生成Test Record文档
        
        Args:
            parent: 父窗口
            
        Returns:
            是否成功生成
        """
        try:
            document_context = ProjectDocumentContext.from_project_context(
                self._get_project_context()
            )
            output_path = self._get_default_output_path(document_context)

            logger.debug(f"默认输出路径: {output_path}")

            default_dir = os.path.dirname(output_path)
            if not os.path.exists(default_dir):
                msg_box = QMessageBox(parent)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("路径问题")
                msg_box.setText(
                    f"无法找到正确的项目文件夹，无法自动保存Test Record文档。\n\n"
                    f"默认路径: {output_path}\n\n请手动选择保存位置。"
                )
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = msg_box.exec_()

                if result == QMessageBox.Cancel:
                    logger.info("用户取消了Test Record生成操作")
                    return False

                output_path, _ = QFileDialog.getSaveFileName(
                    parent,
                    "保存Test Record文档",
                    f"{document_context.dl_number} Test Record.docx",
                    "Word文档 (*.docx)"
                )

                if not output_path:
                    logger.info("用户未选择保存路径，取消Test Record生成操作")
                    return False

            output_path = os.path.normpath(output_path)
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 获取Matrix数据
            if self.matrix_controller:
                matrix_data = self.matrix_controller.get_matrix_rows()
                logger.debug(f"获取到Matrix数据，共 {len(matrix_data)} 行")
                matrix_structure, warnings = self.matrix_controller.create_matrix_data_structure(
                    self._get_project_context()
                )
            elif self.matrix_service:
                matrix_data = self.matrix_service.data_model.rows
                logger.debug(f"获取到Matrix数据，共 {len(matrix_data)} 行")
                
                # 创建MatrixDataStructure实例来解析数据
                matrix_structure = MatrixDataStructure()

                document_context = ProjectDocumentContext.from_project_context(
                    self._get_project_context()
                )
                matrix_structure.dl_number = document_context.dl_number
                matrix_structure.project_data_file_path = document_context.project_data_file_path
                logger.debug(f"设置DL编号: {document_context.dl_number}")
                logger.debug(f"设置项目数据文件路径: {document_context.project_data_file_path}")
                warnings = matrix_structure.parse_matrix_to_structure(matrix_data)
                
            else:
                logger.error("Matrix controller/service not available")
                return False

            group_count = len(matrix_structure.group_steps)
            logger.debug(f"解析完成，共找到 {group_count} 个组别")

            if warnings:
                warning_text = "\n".join(warnings)
                logger.warning(f"Matrix数据验证警告:\n{warning_text}")

                if parent:
                    msg_box = QMessageBox(parent)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("数据验证警告")
                    msg_box.setText(f"发现以下数据问题：\n\n{warning_text}")
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.exec_()

                    logger.debug("用户已确认警告信息，返回Matrix编辑界面")
                    return False

            logger.debug("Matrix数据结构已更新")

            logger.debug("开始调用Test Record服务生成文档")
            success = self.service.generate_test_record_with_structure(matrix_structure, output_path)

            if success:
                logger.info("Test Record文档生成成功")
                if parent:
                    QMessageBox.information(parent, "成功", f"Test Record文档已成功生成并保存到:\n{output_path}")
            else:
                logger.error("Test Record文档生成失败")

            return success
                
        except Exception as e:
            logger.error(f"Error in test record generation controller: {e}")
            return False
