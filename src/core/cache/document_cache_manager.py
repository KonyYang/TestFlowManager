"""
文档缓存管理器 - 缓存 Word/Excel/PDF 解析结果
"""
import logging
from typing import Optional
from .file_based_cache import FileBasedCache

logger = logging.getLogger(__name__)


class DocumentCacheManager:
    """
    文档缓存管理器
    
    缓存内容:
    - Word 文档文本
    - Word 表格数据
    - Excel 工作表数据
    - PDF 文本内容
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        初始化文档缓存管理器
        
        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间（秒）
        """
        self._content_cache = FileBasedCache(
            max_size=max_size, 
            ttl=ttl,
            name="document_content"
        )
        self._metadata_cache = FileBasedCache(
            max_size=max_size, 
            ttl=ttl,
            name="document_metadata"
        )
    
    # Word 文档缓存
    def get_word_content(self, file_path: str) -> Optional[str]:
        """获取 Word 文档文本内容"""
        return self._content_cache.get(file_path, "word_content")
    
    def put_word_content(self, file_path: str, content: str):
        """缓存 Word 文档文本内容"""
        self._content_cache.put(file_path, content, "word_content")
        logger.debug(f"Cached Word content: {file_path}")
    
    def get_word_tables(self, file_path: str) -> Optional[list]:
        """获取 Word 文档表格数据"""
        return self._content_cache.get(file_path, "word_tables")
    
    def put_word_tables(self, file_path: str, tables: list):
        """缓存 Word 文档表格数据"""
        self._content_cache.put(file_path, tables, "word_tables")
    
    # Excel 数据缓存
    def get_excel_data(self, file_path: str, sheet: str = None) -> Optional[dict]:
        """获取 Excel 数据"""
        key = f"excel:{sheet}" if sheet else "excel"
        return self._content_cache.get(file_path, key)
    
    def put_excel_data(self, file_path: str, data: dict, sheet: str = None):
        """缓存 Excel 数据"""
        key = f"excel:{sheet}" if sheet else "excel"
        self._content_cache.put(file_path, data, key)
    
    # 清除缓存
    def clear(self, file_path: str = None):
        """
        清除文档缓存
        
        Args:
            file_path: 如果指定，只清除该文件的缓存；否则清空所有
        """
        if file_path:
            self._content_cache.invalidate_by_file(file_path)
            self._metadata_cache.invalidate_by_file(file_path)
        else:
            self._content_cache.clear()
            self._metadata_cache.clear()
    
    def stats(self) -> dict:
        """获取缓存统计"""
        return {
            'content_cache': self._content_cache.stats(),
            'metadata_cache': self._metadata_cache.stats()
        }
