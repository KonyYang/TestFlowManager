"""
缓存系统单元测试

注意：此测试不依赖任何项目 fixture，可以独立运行
"""
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import time
import pytest
import tempfile


class TestBaseCache:
    """测试 BaseCache"""
    
    def test_basic_get_put(self):
        """测试基本的 get/put"""
        from src.core.cache.base_cache import BaseCache
        
        cache = BaseCache(max_size=10, ttl=3600)
        
        # 设置缓存
        assert cache.put("key1", "value1") is True
        
        # 获取缓存
        assert cache.get("key1") == "value1"
        
        # 不存在的键
        assert cache.get("nonexistent") is None
    
    def test_ttl_expiration(self):
        """测试 TTL 过期"""
        from src.core.cache.base_cache import BaseCache
        
        cache = BaseCache(max_size=10, ttl=1)  # 1秒过期
        
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # 等待过期
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_lru_eviction(self):
        """测试 LRU 淘汰"""
        from src.core.cache.base_cache import BaseCache
        
        cache = BaseCache(max_size=3, ttl=3600)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # 访问 key1，使其成为最近使用
        cache.get("key1")
        
        # 添加新条目，应该淘汰 key2（最久未使用）
        cache.put("key4", "value4")
        
        assert cache.get("key1") == "value1"  # 仍存在
        assert cache.get("key2") is None      # 被淘汰
        assert cache.get("key3") == "value3"  # 仍存在
        assert cache.get("key4") == "value4"  # 新增
    
    def test_stats(self):
        """测试统计信息"""
        from src.core.cache.base_cache import BaseCache
        
        cache = BaseCache(max_size=10, ttl=3600, name="test_cache")
        
        cache.put("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        
        stats = cache.stats()
        
        assert stats['name'] == "test_cache"
        assert stats['size'] == 1
        assert stats['hit_count'] == 1
        assert stats['miss_count'] == 1
        assert stats['hit_rate'] == 0.5
    
    def test_clear(self):
        """测试清空缓存"""
        from src.core.cache.base_cache import BaseCache
        
        cache = BaseCache(max_size=10, ttl=3600)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        count = cache.clear()
        
        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestFileBasedCache:
    """测试 FileBasedCache"""
    
    def test_file_based_caching(self):
        """测试文件感知缓存"""
        from src.core.cache.file_based_cache import FileBasedCache
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            cache = FileBasedCache(max_size=10, ttl=3600)
            
            # 首次缓存
            cache.put(temp_path, "cached_data")
            assert cache.get(temp_path) == "cached_data"
            
            # 修改文件
            time.sleep(0.1)
            with open(temp_path, 'w') as f:
                f.write("modified content")
            
            # 缓存应自动失效
            assert cache.get(temp_path) is None
            
        finally:
            Path(temp_path).unlink()
    
    def test_invalidate_by_file(self):
        """测试按文件失效"""
        from src.core.cache.file_based_cache import FileBasedCache
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test")
            temp_path = f.name
        
        try:
            cache = FileBasedCache(max_size=10, ttl=3600)
            
            cache.put(temp_path, "data1", "subkey1")
            cache.put(temp_path, "data2", "subkey2")
            
            count = cache.invalidate_by_file(temp_path)
            
            assert count == 2
            assert cache.get(temp_path, "subkey1") is None
            assert cache.get(temp_path, "subkey2") is None
            
        finally:
            Path(temp_path).unlink()


class TestDocumentCacheManager:
    """测试 DocumentCacheManager"""
    
    def test_word_content_cache(self):
        """测试 Word 内容缓存"""
        from src.core.cache.document_cache_manager import DocumentCacheManager
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.docx') as f:
            f.write("dummy")
            temp_file = f.name
        
        try:
            manager = DocumentCacheManager(max_size=10, ttl=3600)
            
            # 缓存和获取
            manager.put_word_content(temp_file, "document content")
            assert manager.get_word_content(temp_file) == "document content"
            
            # 清除
            manager.clear(temp_file)
            assert manager.get_word_content(temp_file) is None
        finally:
            Path(temp_file).unlink()
    
    def test_excel_data_cache(self):
        """测试 Excel 数据缓存"""
        from src.core.cache.document_cache_manager import DocumentCacheManager
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlsx') as f:
            f.write("dummy")
            temp_file = f.name
        
        try:
            manager = DocumentCacheManager(max_size=10, ttl=3600)
            
            data = {"Sheet1": [[1, 2], [3, 4]]}
            manager.put_excel_data(temp_file, data, "Sheet1")
            
            cached = manager.get_excel_data(temp_file, "Sheet1")
            assert cached == data
        finally:
            Path(temp_file).unlink()
    
    def test_stats(self):
        """测试统计"""
        from src.core.cache.document_cache_manager import DocumentCacheManager
        
        manager = DocumentCacheManager(max_size=10, ttl=3600)
        stats = manager.stats()
        
        assert 'content_cache' in stats
        assert 'metadata_cache' in stats


class TestDataCacheManager:
    """测试 DataCacheManager"""
    
    def test_matrix_cache(self):
        """测试 Matrix 缓存"""
        from src.core.cache.data_cache_manager import DataCacheManager
        
        manager = DataCacheManager(max_size=10, ttl=3600)
        
        matrix_data = {"rows": 10, "cols": 5}
        manager.put_matrix_data("matrix001", matrix_data)
        
        cached = manager.get_matrix_data("matrix001")
        assert cached == matrix_data
        
        # 清除
        manager.clear_matrix("matrix001")
        assert manager.get_matrix_data("matrix001") is None
    
    def test_ltr_cache(self):
        """测试 LTR 缓存"""
        from src.core.cache.data_cache_manager import DataCacheManager
        
        manager = DataCacheManager(max_size=10, ttl=3600)
        
        ltr_data = {"dl_number": "DL-001", "status": "pending"}
        manager.put_ltr_data("LTR-001", ltr_data)
        
        cached = manager.get_ltr_data("LTR-001")
        assert cached == ltr_data
    
    def test_export_result_cache(self):
        """测试导出结果缓存"""
        from src.core.cache.data_cache_manager import DataCacheManager
        
        manager = DataCacheManager(max_size=10, ttl=3600)
        
        output_path = "output/test.xlsx"
        manager.put_export_result("matrix001", "xlsx", output_path)
        
        cached = manager.get_export_result("matrix001", "xlsx")
        assert cached == output_path
    
    def test_config_cache(self):
        """测试配置缓存"""
        from src.core.cache.data_cache_manager import DataCacheManager
        
        manager = DataCacheManager(max_size=10, ttl=3600)
        
        manager.put_config("app.setting", "value1")
        assert manager.get_config("app.setting") == "value1"
        
        manager.clear_config()
        assert manager.get_config("app.setting") is None
    
    def test_global_stats(self):
        """测试全局统计"""
        from src.core.cache.data_cache_manager import DataCacheManager
        
        manager = DataCacheManager(max_size=10, ttl=3600)
        stats = manager.stats()
        
        assert 'matrix_cache' in stats
        assert 'ltr_cache' in stats
        assert 'export_cache' in stats
        assert 'config_cache' in stats


class TestCacheManagerIntegration:
    """测试 CacheManager 集成"""
    
    def test_unified_access(self):
        """测试统一访问入口"""
        from src.core.cache import cache_manager
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.docx') as f:
            f.write("dummy")
            temp_file = f.name
        
        try:
            # 文档缓存
            cache_manager.document.put_word_content(temp_file, "content")
            assert cache_manager.document.get_word_content(temp_file) == "content"
            
            # 数据缓存
            cache_manager.data.put_config("test.key", "value")
            assert cache_manager.data.get_config("test.key") == "value"
            
            # 统计
            stats = cache_manager.get_stats()
            assert 'document' in stats
            assert 'data' in stats
        finally:
            Path(temp_file).unlink()
    
    def test_clear_all(self):
        """测试清空所有缓存"""
        from src.core.cache import cache_manager
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.docx') as f:
            f.write("dummy")
            temp_file = f.name
        
        try:
            cache_manager.document.put_word_content(temp_file, "content")
            cache_manager.data.put_config("test.key", "value")
            
            cache_manager.clear_all()
            
            assert cache_manager.document.get_word_content(temp_file) is None
            assert cache_manager.data.get_config("test.key") is None
        finally:
            Path(temp_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
