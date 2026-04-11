from dataclasses import dataclass
from typing import Optional

from src.features.matrix.controller.matrix_controller import MatrixController
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController
from src.features.matrix.service.matrix_application_service import MatrixApplicationService
from src.features.matrix.service.matrix_service_provider import MatrixServiceProvider
from src.features.matrix.service.matrix_session_registry import MatrixSessionRegistry


@dataclass(frozen=True)
class MatrixSessionComponents:
    matrix_controller: MatrixController
    matrix_project_controller: MatrixProjectController


class MatrixSessionFactory:
    """Assembles Matrix session components."""

    @staticmethod
    def create(
        parent_view=None,
        mode: str = "shared",
        *,
        session_id: Optional[str] = None,
        registry: Optional[MatrixSessionRegistry] = None,
        provider=None,
    ) -> MatrixSessionComponents:
        matrix_service = MatrixSessionFactory._create_matrix_service(
            mode=mode,
            session_id=session_id,
            registry=registry,
            provider=provider,
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
        provider=None,
    ):
        if registry is not None and provider is not None:
            raise ValueError("registry and provider cannot be used at the same time")

        if registry is not None:
            registry.set_mode(mode, session_id=session_id)
            return registry.get_service(session_id=session_id)

        if provider is not None:
            return provider.get_service()

        if mode == "shared":
            return MatrixServiceProvider.get_service()
        if mode == "isolated":
            isolated_registry = MatrixSessionRegistry(initial_mode="isolated")
            return isolated_registry.get_service()
        raise ValueError(f"Unsupported Matrix session mode: {mode}")
