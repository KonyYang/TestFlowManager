"""项目态输出目录与全局兜底目录解析。"""

from pathlib import Path
from typing import Optional

from src.core.project_context import ProjectContext
from src.core.project_document_context import ProjectDocumentContext


DEFAULT_OUTPUT_DIR = str(Path(r"D:\OutFile"))


class OutputPathResolver:
    """统一解析项目态输出目录与全局兜底目录。"""

    @staticmethod
    def get_default_output_dir() -> str:
        return DEFAULT_OUTPUT_DIR

    @staticmethod
    def build_default_output_path(filename: str) -> str:
        return str(Path(DEFAULT_OUTPUT_DIR) / filename)

    @staticmethod
    def get_document_context(
        project_context: Optional[ProjectContext],
    ) -> ProjectDocumentContext:
        return ProjectDocumentContext.from_project_context(project_context)

    @classmethod
    def resolve_submitted_material_dir(
        cls,
        project_context: Optional[ProjectContext],
        *,
        create: bool = False,
    ) -> str:
        document_context = cls.get_document_context(project_context)
        return (
            document_context.get_submitted_material_dir(create=create)
            or cls.get_default_output_dir()
        )

    @classmethod
    def resolve_test_results_dir(
        cls,
        project_context: Optional[ProjectContext],
        *,
        create: bool = False,
    ) -> str:
        document_context = cls.get_document_context(project_context)
        return (
            document_context.get_test_results_dir(create=create)
            or cls.get_default_output_dir()
        )

    @classmethod
    def resolve_project_workspace_dir(
        cls,
        project_context: Optional[ProjectContext],
        *,
        create: bool = False,
    ) -> str:
        document_context = cls.get_document_context(project_context)
        return (
            document_context.get_project_workspace_dir(create=create)
            or (project_context.project_path if project_context else None)
            or cls.get_default_output_dir()
        )

    @classmethod
    def build_submitted_material_output_path(
        cls,
        project_context: Optional[ProjectContext],
        filename: str,
        *,
        create_dir: bool = False,
    ) -> str:
        document_context = cls.get_document_context(project_context)
        return (
            document_context.build_submitted_material_output_path(
                filename,
                create_dir=create_dir,
            )
            or cls.build_default_output_path(filename)
        )
