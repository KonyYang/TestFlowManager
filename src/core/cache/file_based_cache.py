"""
文件感知缓存 - 自动检测文件变更并失效

特性:
- 基于文件修改时间自动失效
- 支持按文件路径和子键缓存
- 继承 BaseCache 的 LRU + TTL 功能
"""
import os
import time
from typing import Optional, Any
from .base_cache import BaseCache


class FileBasedCache(BaseCache):
    """
    文件感知缓存
    
    当文件被修改时，相关缓存条目自动失效
    """
    
    def get(self, file_path: str, key: str = None) -> Optional[Any]:
        """
        获取文件缓存
        
        Args:
            file_path: 文件路径
            key: 可选的子键（用于同一文件的多个缓存项）
            
        Returns:
            缓存的数据，如果不存在、已过期或文件已修改则返回 None
        """
        cache_key = self._build_key(file_path, key)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            if not entry:
                self._miss_count += 1
                return None
            
            # 检查文件是否被修改
            if self._is_file_modified(file_path, entry.metadata.get('file_mtime')):
                del self._cache[cache_key]
                self._miss_count += 1
                return None
            
            # 正常的 TTL 检查
            if self._ttl > 0 and time.time() - entry.timestamp > self._ttl:
                del self._cache[cache_key]
                self._miss_count += 1
                return None
            
            # 更新访问信息
            entry.last_access = time.time()
            entry.access_count += 1
            self._cache.move_to_end(cache_key)
            
            self._hit_count += 1
            return entry.data
    
    def put(
        self, 
        file_path: str, 
        data: Any, 
        key: str = None, 
        **metadata
    ) -> bool:
        """
        设置文件缓存
        
        Args:
            file_path: 文件路径
            data: 缓存数据
            key: 可选的子键
            **metadata: 额外元数据
            
        Returns:
            是否成功
        """
        cache_key = self._build_key(file_path, key)
        
        # 自动记录文件修改时间
        file_mtime = self._get_file_mtime(file_path)
        metadata['file_path'] = file_path
        metadata['file_mtime'] = file_mtime
        
        return super().put(cache_key, data, **metadata)
    
    def invalidate_by_file(self, file_path: str) -> int:
        """
        使指定文件的所有缓存失效
        
        Args:
            file_path: 文件路径
            
        Returns:
            失效的条目数
        """
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.metadata.get('file_path') == file_path
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            return len(keys_to_remove)
    
    @staticmethod
    def _build_key(file_path: str, key: str = None) -> str:
        """构建缓存键"""
        return f"{file_path}:{key}" if key else file_path
    
    @staticmethod
    def _is_file_modified(file_path: str, cached_mtime: Optional[float]) -> bool:
        """
        检查文件是否被修改
        
        Args:
            file_path: 文件路径
            cached_mtime: 缓存的修改时间
            
        Returns:
            True 如果文件已被修改
        """
        if not cached_mtime:
            return True
        
        current_mtime = FileBasedCache._get_file_mtime(file_path)
        return current_mtime != cached_mtime
    
    @staticmethod
    def _get_file_mtime(file_path: str) -> Optional[float]:
        """
        获取文件修改时间
        
        Args:
            file_path: 文件路径
            
        Returns:
            修改时间戳，如果文件不存在则返回 None
        """
        try:
            return os.path.getmtime(file_path)
        except (OSError, FileNotFoundError):
            return None
