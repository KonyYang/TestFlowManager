"""
Document Parser模块初始化文件
"""

from .controller.document_parser_controller import DocumentParserController
from .service.document_parser_service import DocumentParserService
from .service.body_content_service import BodyContentService
from .view.body_content_dialog import BodyContentDialog

__all__ = [
    'DocumentParserController',
    'DocumentParserService',
    'BodyContentService',
    'BodyContentDialog'
]