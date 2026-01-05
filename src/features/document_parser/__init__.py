"""
Document Parser模块初始化文件
"""

from .controller.document_parser_controller import DocumentParserController
from .service.document_parser_service import DocumentParserService

__all__ = [
    'DocumentParserController',
    'DocumentParserService',
]