"""
验证异常模块
定义与数据验证相关的异常类
"""


class ValidationError(Exception):
    """
    验证异常类
    当数据验证失败时抛出
    """

    def __init__(self, message: str, field: str = None):
        """
        初始化验证异常

        Args:
            message: 异常消息
            field: 相关字段名（可选）
        """
        super().__init__(message)
        self.message = message
        self.field = field

    def __str__(self):
        if self.field:
            return f"Validation error in field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class RequiredFieldError(ValidationError):
    """
    必填字段异常类
    当必填字段缺失时抛出
    """

    def __init__(self, field: str):
        """
        初始化必填字段异常

        Args:
            field: 缺失的字段名
        """
        super().__init__(f"Required field '{field}' is missing", field)
        self.field = field


class FormatValidationError(ValidationError):
    """
    格式验证异常类
    当字段格式不符合要求时抛出
    """

    def __init__(self, field: str, expected_format: str):
        """
        初始化格式验证异常

        Args:
            field: 格式错误的字段名
            expected_format: 期望的格式
        """
        super().__init__(
            f"Field '{field}' format is invalid. Expected format: {expected_format}",
            field
        )
        self.expected_format = expected_format
