"""
轻量级数据缓存模块
用于缓存频繁访问的数据,避免重复读取文件
"""
import time
from typing import Any, Optional
from src.core.logger import logger


class DataCache:
    """
    轻量级内存缓存
    
    使用场景:
    - Matrix数据缓存
    - 配置文件缓存
    - LTR文件数据缓存
    """
    
    _cache = {}
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据,如果不存在或已过期则返回None
        """
        if key not in cls._cache:
            return None
        
        cache_entry = cls._cache[key]
        
        # 检查是否过期
        if cache_entry['expires'] and time.time() > cache_entry['expires']:
            logger.debug(f"缓存过期: {key}")
            del cls._cache[key]
            return None
        
        logger.debug(f"缓存命中: {key}")
        return cache_entry['value']
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: int = 300) -> None:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间(秒),默认5分钟,0表示永不过期
        """
        expires = time.time() + ttl if ttl > 0 else None
        cls._cache[key] = {
            'value': value,
            'expires': expires,
            'created_at': time.time()
        }
        logger.debug(f"缓存设置: {key} (TTL={ttl}s)")
    
    @classmethod
    def is_valid(cls, key: str) -> bool:
        """
        检查缓存是否有效
        
        Args:
            key: 缓存键
            
        Returns:
            True如果缓存存在且未过期
        """
        if key not in cls._cache:
            return False
        
        cache_entry = cls._cache[key]
        
        # 永不过期
        if cache_entry['expires'] is None:
            return True
        
        # 检查是否过期
        return time.time() <= cache_entry['expires']
    
    @classmethod
    def invalidate(cls, key: str) -> bool:
        """
        使缓存失效
        
        Args:
            key: 缓存键
            
        Returns:
            True如果成功删除
        """
        if key in cls._cache:
            del cls._cache[key]
            logger.debug(f"缓存失效: {key}")
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """清空所有缓存"""
        cls._cache.clear()
        logger.info("所有缓存已清空")
    
    @classmethod
    def get_stats(cls) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计的字典
        """
        total = len(cls._cache)
        expired = sum(
            1 for entry in cls._cache.values()
            if entry['expires'] and time.time() > entry['expires']
        )
        active = total - expired
        
        return {
            'total': total,
            'active': active,
            'expired': expired
        }


# 便捷函数
def cache_get(key: str) -> Optional[Any]:
    """获取缓存的便捷函数"""
    return DataCache.get(key)


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """设置缓存的便捷函数"""
    DataCache.set(key, value, ttl)


def cache_invalidate(key: str) -> None:
    """使缓存失效的便捷函数"""
    DataCache.invalidate(key)
