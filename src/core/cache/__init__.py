"""
缓存模块 - 统一的缓存管理入口

用法:
    from src.core.cache import cache_manager
    
    # 文档缓存
    content = cache_manager.document.get_word_content("doc.docx")
    if content is None:
        content = parse_word("doc.docx")
        cache_manager.document.put_word_content("doc.docx", content)
    
    # 数据缓存
    matrix_data = cache_manager.data.get_matrix_data("matrix001")
    
    # 查看统计
    stats = cache_manager.get_stats()
"""
from .document_cache_manager import DocumentCacheManager
from .data_cache_manager import DataCacheManager


class CacheManager:
    """
    统一缓存管理器
    
    提供文档和数据两级缓存，自动管理生命周期
    """
    
    def __init__(self):
        self.document = DocumentCacheManager(max_size=100, ttl=3600)
        self.data = DataCacheManager(max_size=500, ttl=1800)
    
    def get_stats(self) -> dict:
        """获取所有缓存统计"""
        return {
            'document': self.document.stats(),
            'data': self.data.stats(),
        }
    
    def clear_all(self):
        """清空所有缓存"""
        self.document.clear()
        self.data.clear()


# 全局单例
cache_manager = CacheManager()