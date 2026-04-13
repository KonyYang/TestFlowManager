"""
数据缓存管理器 - 缓存 Matrix/LTR/导出结果等业务数据
"""
import logging
from typing import Optional, Any
from .base_cache import BaseCache

logger = logging.getLogger(__name__)


class DataCacheManager:
    """
    数据缓存管理器
    
    缓存内容:
    - Matrix 数据
    - LTR 申请数据
    - 导出结果文件路径
    - 配置数据
    """
    
    def __init__(self, max_size: int = 500, ttl: int = 1800):
        """
        初始化数据缓存管理器
        
        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间（秒）
        """
        self._matrix_cache = BaseCache(
            max_size=max_size, 
            ttl=ttl,
            name="matrix_data"
        )
        self._ltr_cache = BaseCache(
            max_size=max_size, 
            ttl=ttl,
            name="ltr_data"
        )
        self._export_cache = BaseCache(
            max_size=max_size // 2, 
            ttl=ttl * 2,
            name="export_results"
        )
        self._config_cache = BaseCache(
            max_size=100, 
            ttl=3600,
            name="config_data"
        )
    
    # Matrix 缓存
    def get_matrix_data(self, matrix_id: str) -> Optional[dict]:
        """获取 Matrix 数据"""
        return self._matrix_cache.get(f"matrix:{matrix_id}")
    
    def put_matrix_data(self, matrix_id: str, data: dict):
        """缓存 Matrix 数据"""
        self._matrix_cache.put(f"matrix:{matrix_id}", data)
        logger.debug(f"Cached matrix data: {matrix_id}")
    
    def clear_matrix(self, matrix_id: str = None):
        """
        清除 Matrix 缓存
        
        Args:
            matrix_id: 如果指定，只清除该 Matrix 的缓存；否则清空所有
        """
        if matrix_id:
            self._matrix_cache.remove(f"matrix:{matrix_id}")
        else:
            self._matrix_cache.clear()
    
    # LTR 缓存
    def get_ltr_data(self, ltr_number: str) -> Optional[dict]:
        """获取 LTR 数据"""
        return self._ltr_cache.get(f"ltr:{ltr_number}")
    
    def put_ltr_data(self, ltr_number: str, data: dict):
        """缓存 LTR 数据"""
        self._ltr_cache.put(f"ltr:{ltr_number}", data)
        logger.debug(f"Cached LTR data: {ltr_number}")
    
    def clear_ltr(self, ltr_number: str = None):
        """清除 LTR 缓存"""
        if ltr_number:
            self._ltr_cache.remove(f"ltr:{ltr_number}")
        else:
            self._ltr_cache.clear()
    
    # 导出结果缓存
    def get_export_result(
        self, 
        matrix_id: str, 
        fmt: str, 
        **options
    ) -> Optional[str]:
        """获取导出结果文件路径"""
        key = f"export:{matrix_id}:{fmt}:{hash(str(options))}"
        return self._export_cache.get(key)
    
    def put_export_result(
        self, 
        matrix_id: str, 
        fmt: str, 
        output_path: str, 
        **options
    ):
        """缓存导出结果"""
        key = f"export:{matrix_id}:{fmt}:{hash(str(options))}"
        self._export_cache.put(key, output_path)
        logger.debug(f"Cached export result: {matrix_id} -> {output_path}")
    
    def clear_export(self):
        """清空导出结果缓存"""
        self._export_cache.clear()
    
    # 配置缓存
    def get_config(self, key: str) -> Optional[Any]:
        """获取配置数据"""
        return self._config_cache.get(key)
    
    def put_config(self, key: str, value: Any):
        """缓存配置数据"""
        self._config_cache.put(key, value)
    
    def clear_config(self):
        """清空配置缓存"""
        self._config_cache.clear()
    
    def stats(self) -> dict:
        """获取所有缓存统计"""
        return {
            'matrix_cache': self._matrix_cache.stats(),
            'ltr_cache': self._ltr_cache.stats(),
            'export_cache': self._export_cache.stats(),
            'config_cache': self._config_cache.stats(),
        }
    
    def clear(self):
        """清空所有数据缓存"""
        self._matrix_cache.clear()
        self._ltr_cache.clear()
        self._export_cache.clear()
        self._config_cache.clear()
