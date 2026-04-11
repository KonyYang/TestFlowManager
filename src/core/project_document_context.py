import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.logger import logger
from src.core.project_context import ProjectContext, resolve_project_data_file_path


@dataclass(frozen=True)
class ProjectDocumentContext:
    """面向文档生成链路的项目输入快照。"""

    project_context: Optional[ProjectContext]
    project_data_file_path: Optional[str]
    dl_number: str
    project_data: Dict[str, Any]

    @classmethod
    def from_project_context(
        cls,
        project_context: Optional[ProjectContext],
        *,
        default_dl_number: str = "DL-UNKNOWN",
    ) -> "ProjectDocumentContext":
        project_data_file_path = resolve_project_data_file_path(project_context)
        project_data = cls._load_project_data(project_data_file_path)

        dl_number = (
            project_data.get("DL")
            or (project_context.dl_number if project_context else None)
            or (os.path.basename(project_context.project_path) if project_context else None)
            or default_dl_number
        )

        return cls(
            project_context=project_context,
            project_data_file_path=project_data_file_path,
            dl_number=dl_number,
            project_data=project_data,
        )

    @staticmethod
    def _load_project_data(project_data_file_path: Optional[str]) -> Dict[str, Any]:
        if not project_data_file_path or not os.path.exists(project_data_file_path):
            return {}

        try:
            with open(project_data_file_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            logger.error("读取项目数据文件失败: %s", exc)
            return {}

    def get_submitted_material_dir(self, *, create: bool = False) -> Optional[str]:
        project_context = self.project_context
        if not project_context or not os.path.exists(project_context.project_path):
            return None

        project_root_dir = Path(project_context.project_path)
        dl_subfolder_path = None

        try:
            for item in sorted(project_root_dir.iterdir(), key=lambda p: p.name):
                if item.is_dir() and item.name.startswith(self.dl_number):
                    dl_subfolder_path = item
                    break
        except Exception as exc:
            logger.error("查找项目子目录失败: %s", exc)
            return None

        target_root = dl_subfolder_path or project_root_dir
        submitted_material_dir = target_root / "Submitted Material"

        if create:
            try:
                submitted_material_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                logger.error("创建 Submitted Material 目录失败: %s", exc)
                return str(target_root)

        if submitted_material_dir.exists():
            return str(submitted_material_dir)

        return str(target_root)

    def get_project_workspace_dir(self, *, create: bool = False) -> Optional[str]:
        workspace_dir = self.get_submitted_material_dir(create=create)
        if not workspace_dir:
            return None

        workspace_path = Path(workspace_dir)
        if workspace_path.name == "Submitted Material":
            return str(workspace_path.parent)
        return str(workspace_path)

    def get_test_results_dir(self, *, create: bool = False) -> Optional[str]:
        workspace_dir = self.get_project_workspace_dir(create=create)
        if not workspace_dir:
            return None

        test_results_dir = Path(workspace_dir) / "Test results"
        if create:
            try:
                test_results_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                logger.error(f"创建 Test results 目录失败: {exc}")
                return str(Path(workspace_dir))

        return str(test_results_dir)

    def build_submitted_material_output_path(self, filename: str, *, create_dir: bool = False) -> Optional[str]:
        submitted_material_dir = self.get_submitted_material_dir(create=create_dir)
        if not submitted_material_dir:
            return None
        return str(Path(submitted_material_dir) / filename)

    def get_field(self, key: str, default: Any = "") -> Any:
        return self.project_data.get(key, default)

    def apply_to_matrix_data_structure(self, matrix_data_structure) -> None:
        matrix_data_structure.dl_number = self.dl_number
        matrix_data_structure.project_data_file_path = self.project_data_file_path
