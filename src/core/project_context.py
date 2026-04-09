from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ProjectContext:
    project_path: str
    dl_number: Optional[str] = None
    application_data_path: Optional[str] = None
    matrix_file_path: Optional[str] = None

    @classmethod
    def from_project_path(cls, project_path: str, dl_number: Optional[str] = None) -> "ProjectContext":
        project_dir = Path(project_path)
        application_data_path = project_dir / "application_data"
        matrix_file_path = project_dir / "matrix.xlsx"

        return cls(
            project_path=str(project_dir),
            dl_number=dl_number,
            application_data_path=str(application_data_path),
            matrix_file_path=str(matrix_file_path),
        )

    @classmethod
    def from_event_data(cls, data: Mapping[str, Any]) -> Optional["ProjectContext"]:
        if not data:
            return None

        project_context = data.get("project_context")
        if isinstance(project_context, cls):
            return project_context

        project_path = data.get("project_path")
        if not project_path:
            return None

        return cls.from_project_path(project_path, data.get("dl_number"))

    def to_event_data(self) -> Mapping[str, Any]:
        return {
            "project_context": self,
            "project_path": self.project_path,
            "dl_number": self.dl_number,
        }


def get_current_project_context() -> Optional[ProjectContext]:
    from src.core.state_manager import state_manager

    project_context = state_manager.get_state("current_project_context")
    if isinstance(project_context, ProjectContext):
        return project_context
    return None


def get_current_project_path() -> Optional[str]:
    project_context = get_current_project_context()
    if not project_context:
        return None
    return project_context.project_path


def resolve_project_data_file_path(project_context: Optional[ProjectContext]) -> Optional[str]:
    if not project_context:
        return None

    candidate_paths = []
    if project_context.application_data_path:
        application_data_path = Path(project_context.application_data_path)
        candidate_paths.append(application_data_path)
        if not application_data_path.suffix:
            candidate_paths.append(application_data_path.with_suffix(".json"))

    candidate_paths.append(Path(project_context.project_path) / "application_data.json")

    seen_paths = set()
    for candidate_path in candidate_paths:
        candidate_str = str(candidate_path)
        if candidate_str in seen_paths:
            continue
        seen_paths.add(candidate_str)
        if candidate_path.exists():
            return candidate_str

    return str(candidate_paths[0]) if candidate_paths else None


def get_current_project_data_file_path() -> Optional[str]:
    return resolve_project_data_file_path(get_current_project_context())
