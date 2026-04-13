"""
缓存基类 - 提供通用缓存功能

特性:
- 线程安全
- LRU 淘汰策略
- TTL 过期机制
- 容量限制
- 统计信息
"""
import time
import threading
from typing import Any, Optional, Dict
from dataclasses import dataclass, field
from collections import OrderedDict


@dataclass
class CacheEntry:
    """缓存条目"""
    data: Any
    key: str
    timestamp: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCache:
    """
    基础缓存类
    
    支持 LRU 淘汰和 TTL 过期，线程安全
    """
    
    def __init__(
        self, 
        max_size: int = 1000, 
        ttl: int = 3600,
        name: str = "unnamed"
    ):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间（秒），0 表示永不过期
            name: 缓存名称（用于日志和统计）
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._name = name
        self._lock = threading.RLock()
        
        # 统计信息
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                self._miss_count += 1
                return None
            
            # 检查 TTL
            if self._ttl > 0 and time.time() - entry.timestamp > self._ttl:
                del self._cache[key]
                self._miss_count += 1
                return None
            
            # 更新访问信息（LRU）
            entry.last_access = time.time()
            entry.access_count += 1
            self._cache.move_to_end(key)  # 移到末尾（最近使用）
            
            self._hit_count += 1
            return entry.data
    
    def put(self, key: str, data: Any, size_bytes: int = 0, **metadata) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 缓存数据
            size_bytes: 数据大小（字节），0 表示自动估算
            **metadata: 元数据
            
        Returns:
            是否成功
        """
        with self._lock:
            # 如果已满，淘汰 LRU
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_lru()
            
            # 创建新条目
            entry = CacheEntry(
                data=data,
                key=key,
                size_bytes=size_bytes or self._estimate_size(data),
                metadata=metadata
            )
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
            return True
    
    def remove(self, key: str) -> bool:
        """
        删除缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> int:
        """
        清空缓存
        
        Returns:
            清除的条目数
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计的字典
        """
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (
                self._hit_count / total_requests 
                if total_requests > 0 
                else 0.0
            )
            
            total_size = sum(e.size_bytes for e in self._cache.values())
            
            return {
                'name': self._name,
                'size': len(self._cache),
                'max_size': self._max_size,
                'total_size_mb': total_size / (1024 * 1024),
                'hit_count': self._hit_count,
                'miss_count': self._miss_count,
                'hit_rate': hit_rate,
                'eviction_count': self._eviction_count,
                'ttl': self._ttl,
            }
    
    def _evict_lru(self):
        """淘汰最近最少使用的条目"""
        if self._cache:
            # OrderedDict 的第一个元素是最久未使用的
            oldest_key, oldest_entry = next(iter(self._cache.items()))
            del self._cache[oldest_key]
            self._eviction_count += 1
    
    def _estimate_size(self, data: Any) -> int:
        """
        估算数据大小（字节）
        
        Args:
            data: 数据对象
            
        Returns:
            估算的字节数
        """
        import sys
        try:
            return sys.getsizeof(data)
        except Exception:
            return 0
