from typing import Optional

from src.features.matrix.service.matrix_session_registry import MatrixSessionRegistry

from src.features.matrix.controller.matrix_controller import MatrixController
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController
from src.features.matrix.service.matrix_application_service import MatrixApplicationService
from src.features.matrix.service.matrix_session_components import MatrixSessionComponents

class MatrixSessionFactory:
    """Assembles Matrix session components."""

    @staticmethod
    def create(
        parent_view=None,
        mode: str = "shared",
        *,
        session_id: Optional[str] = None,
        registry: Optional[MatrixSessionRegistry] = None,
    ) -> MatrixSessionComponents:
        matrix_service = MatrixSessionFactory._create_matrix_service(
            mode=mode,
            session_id=session_id,
            registry=registry,
        )
        application_service = MatrixApplicationService(matrix_service)
        matrix_controller = MatrixController(
            parent=parent_view,
            matrix_service=matrix_service,
            application_service=application_service,
        )
        matrix_project_controller = MatrixProjectController(
            parent_view=parent_view,
            matrix_controller=matrix_controller,
        )
        return MatrixSessionComponents(
            matrix_controller=matrix_controller,
            matrix_project_controller=matrix_project_controller,
        )

    @staticmethod
    def _create_matrix_service(
        mode: str,
        *,
        session_id: Optional[str] = None,
        registry: Optional[MatrixSessionRegistry] = None,
    ):
        if mode not in ("shared", "isolated"):
            raise ValueError(f"Unsupported Matrix session mode: {mode}")

        active_registry = registry or MatrixSessionRegistry(initial_mode=mode)
        if registry is not None:
            active_registry.set_mode(mode, session_id=session_id)
        return active_registry.get_service(session_id=session_id)
