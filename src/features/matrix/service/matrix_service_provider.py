from src.features.matrix.service.matrix_service import MatrixService


class _MatrixServiceAccessor:
    """默认的 MatrixService 访问器。"""

    def __init__(self, service_factory=None):
        self._service_factory = service_factory or MatrixService.shared

    def get_service(self):
        return self._service_factory()

    def set_service_factory(self, service_factory):
        self._service_factory = service_factory

    def reset_service_factory(self):
        self._service_factory = MatrixService.shared


class MatrixServiceProvider:
    """提供 MatrixService 的访问入口，便于后续切换为显式注入。"""

    _provider = _MatrixServiceAccessor()

    @staticmethod
    def get_service():
        return MatrixServiceProvider._provider.get_service()

    @staticmethod
    def set_service_factory(service_factory):
        MatrixServiceProvider._provider.set_service_factory(service_factory)

    @staticmethod
    def reset_service_factory():
        MatrixServiceProvider._provider.reset_service_factory()

    @staticmethod
    def set_provider(provider):
        MatrixServiceProvider._provider = provider

    @staticmethod
    def reset_provider():
        MatrixServiceProvider._provider = _MatrixServiceAccessor()
