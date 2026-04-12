# src/features/step_record_generator/controller/step_record_controller.py
"""
Controller for generating Step Record documents.
"""

import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from src.core.logger import logger
from src.core.output_paths import OutputPathResolver
from src.core.project_context import ProjectContext
from src.core.project_document_context import ProjectDocumentContext
from src.features.step_record_generator.service.step_record_service import StepRecordService
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure


class StepRecordController:
    def __init__(self, matrix_controller=None, project_context: ProjectContext = None):
        self.service = StepRecordService()
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

        return None

    def _get_default_output_path(self, document_context: ProjectDocumentContext):
        try:
            output_filename = f"{document_context.dl_number} Step Record.docx"
            output_path = OutputPathResolver.build_submitted_material_output_path(
                self._get_project_context(),
                output_filename,
                create_dir=True,
            )
            if output_path:
                logger.debug(f"Constructed default output path: {output_path}")
                return os.path.normpath(output_path)

            return OutputPathResolver.build_default_output_path("steprecord.docx")
        except Exception as e:
            logger.error(f"Failed to construct default output path: {e}")
            return OutputPathResolver.build_default_output_path("steprecord.docx")

    def generate_step_record(self, parent=None):
        try:
            document_context = ProjectDocumentContext.from_project_context(
                self._get_project_context()
            )
            output_path = self._get_default_output_path(document_context)

            logger.debug(f"Default output path: {output_path}")

            default_dir = os.path.dirname(output_path)
            if not os.path.exists(default_dir):
                msg_box = QMessageBox(parent)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("路径问题")
                msg_box.setText(
                    f"无法找到正确的项目文件夹，无法自动保存Step Record文档。\n\n"
                    f"默认路径: {output_path}\n\n请手动选择保存位置。"
                )
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = msg_box.exec_()

                if result == QMessageBox.Cancel:
                    logger.info("User cancelled Step Record generation")
                    return False

                output_path, _ = QFileDialog.getSaveFileName(
                    parent,
                    "保存Step Record文档",
                    f"{document_context.dl_number} Step Record.docx",
                    "Word文档 (*.docx)",
                )

                if not output_path:
                    logger.info("User did not choose a save path, cancelled")
                    return False

            output_path = os.path.normpath(output_path)
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if not self.matrix_controller:
                logger.error("Matrix controller is not available")
                return False

            matrix_data = self.matrix_controller.get_matrix_rows()
            logger.debug(f"Loaded matrix rows count: {len(matrix_data)}")
            
            # 构建 MatrixDataStructure
            matrix_structure = MatrixDataStructure()
            warnings = matrix_structure.parse_matrix_to_structure(matrix_data)

            group_count = len(matrix_structure.group_steps)
            logger.debug(f"Matrix parsed. Group count: {group_count}")

            if warnings:
                warning_text = "\n".join(warnings)
                logger.warning(f"Matrix data validation warnings:\n{warning_text}")

                if parent:
                    msg_box = QMessageBox(parent)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("数据验证警告")
                    msg_box.setText(f"发现以下数据问题：\n\n{warning_text}")
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.exec_()

                    logger.debug("User acknowledged warnings; return to matrix editor")
                    return False

            logger.debug("Generating Step Record document via service")
            success = self.service.generate_step_record_with_structure(
                matrix_structure,
                output_path,
            )

            if success:
                logger.info("Step Record generated successfully")
                if parent:
                    QMessageBox.information(
                        parent,
                        "成功",
                        f"Step Record文档已成功生成并保存到:\n{output_path}",
                    )
            else:
                logger.error("Step Record generation failed")

            return success
        except Exception as e:
            logger.error(f"Error in step record generation controller: {e}")
            return False
