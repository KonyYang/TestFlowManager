from dataclasses import dataclass

from src.features.matrix.controller.matrix_controller import MatrixController
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController


@dataclass(frozen=True)
class MatrixSessionComponents:
    matrix_controller: MatrixController
    matrix_project_controller: MatrixProjectController
