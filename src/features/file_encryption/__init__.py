# src/features/file_encryption/__init__.py
"""
文件加密模块
提供批量加密 Word 和 Excel 文件的功能
"""

from .controller.file_encryption_controller import FileEncryptionController
from .service.file_encryption_service import FileEncryptionService, SignalEmitter

__all__ = [
    'FileEncryptionController',
    'FileEncryptionService',
    'SignalEmitter'
]
