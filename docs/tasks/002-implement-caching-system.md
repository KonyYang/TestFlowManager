# 任务计划：实现文档/数据缓存系统

> **任务编号**: TASK-002
> **任务名称**: 实现文档/数据缓存系统
> **优先级**: P0（紧急）
> **预计耗时**: 24 小时（3 个工作日）
> **风险等级**: 中（需处理缓存一致性）
> **预期性能提升**: 70-90%（重复操作）
> **创建日期**: 2026-04-07

---

## 📋 任务概述

### 目标
实现多级缓存系统，缓存文档解析结果、Matrix 数据、配置数据等，大幅提升重复操作的性能。

### 背景问题
当前系统存在严重的重复计算问题：
- Word文档多次解析（2-5秒/次）
- Matrix数据重复导出（3-8秒/次）
- 配置频繁读取文件系统（I/O开销）
- 缺乏缓存机制导致用户体验差

### 缓存需求矩阵

| 数据类型 | 访问频率 | 加载成本 | 优先级 | 预期提升 |
|----------|----------|----------|--------|----------|
| Word文档解析 | 高 | 2-5秒 | P0 | 80-95% |
| Matrix导出结果 | 高 | 3-8秒 | P0 | 75-90% |
| 配置数据 | 中 | 50-100ms | P1 | 60-80% |
| LTR数据 | 中 | 100-200ms | P1 | 70-85% |

---

## 🏗️ 缓存架构设计

### 核心组件

```
┌─────────────────────────────────────┐
│      CacheManager (统一入口)        │
├──────────┬──────────┬─────────────┤
│ DocCache │ DataCache│ ConfigCache │
└──────────┴──────────┴─────────────┘
     ↓           ↓            ↓
┌─────────────────────────────────────┐
│      BaseCache (LRU/TTL/Size)       │
└─────────────────────────────────────┘
```

---

## 📅 实施步骤

### 第一阶段：缓存基础设施（8小时）

#### 任务 1.1：创建缓存基类

**文件**: `src/core/cache/base_cache.py`

```python
"""
缓存基类 - 提供通用缓存功能
"""

import time
import threading
from typing import Any, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum


class CachePolicy(Enum):
    LRU = "lru"
    TTL = "ttl"


@dataclass
class CacheEntry:
    data: Any
    key: str
    timestamp: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                self._miss_count += 1
                return None
            
            if self._ttl > 0 and time.time() - entry.timestamp > self._ttl:
                del self._cache[key]
                self._miss_count += 1
                return None
            
            entry.last_access = time.time()
            entry.access_count += 1
            self._hit_count += 1
            return entry.data
    
    def put(self, key: str, data: Any, **metadata) -> bool:
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_lru()
            
            self._cache[key] = CacheEntry(data=data, key=key, metadata=metadata)
            return True
    
    def remove(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> int:
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hit_count': self._hit_count,
                'miss_count': self._miss_count,
                'hit_rate': hit_rate,
            }
    
    def _evict_lru(self):
        if self._cache:
            lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_access)
            del self._cache[lru_key]


class FileBasedCache(BaseCache):
    def get(self, file_path: str, key: str = None) -> Optional[Any]:
        cache_key = f"{file_path}:{key}" if key else file_path
        
        with self._lock:
            entry = self._cache.get(cache_key)
            if not entry:
                self._miss_count += 1
                return None
            
            if self._is_file_modified(file_path, entry.metadata.get('file_mtime')):
                del self._cache[cache_key]
                self._miss_count += 1
                return None
            
            entry.last_access = time.time()
            entry.access_count += 1
            self._hit_count += 1
            return entry.data
    
    def put(self, file_path: str, data: Any, key: str = None, **metadata):
        cache_key = f"{file_path}:{key}" if key else file_path
        metadata['file_path'] = file_path
        metadata['file_mtime'] = self._get_file_mtime(file_path)
        return super().put(cache_key, data, **metadata)
    
    def _is_file_modified(self, file_path: str, cached_mtime: float) -> bool:
        if not cached_mtime:
            return True
        return self._get_file_mtime(file_path) != cached_mtime
    
    @staticmethod
    def _get_file_mtime(file_path: str) -> Optional[float]:
        try:
            return os.path.getmtime(file_path)
        except (OSError, FileNotFoundError):
            return None
```

**验收标准**: 支持 LRU 淘汰、TTL 过期、文件变更检测，线程安全

---

#### 任务 1.2：创建文档缓存管理器

**文件**: `src/core/cache/document_cache_manager.py`

```python
"""
文档缓存管理器
"""

import logging
from .base_cache import FileBasedCache

logger = logging.getLogger(__name__)


class DocumentCacheManager:
    def __init__(self, max_size=100, ttl=3600):
        self._content_cache = FileBasedCache(max_size=max_size, ttl=ttl)
        self._metadata_cache = FileBasedCache(max_size=max_size, ttl=ttl)
    
    def get_word_content(self, file_path: str) -> Optional[str]:
        return self._content_cache.get(file_path, "word_content")
    
    def put_word_content(self, file_path: str, content: str):
        self._content_cache.put(file_path, content, "word_content")
        logger.debug(f"Cached Word content: {file_path}")
    
    def get_word_tables(self, file_path: str) -> Optional[list]:
        return self._content_cache.get(file_path, "word_tables")
    
    def put_word_tables(self, file_path: str, tables: list):
        self._content_cache.put(file_path, tables, "word_tables")
    
    def get_excel_data(self, file_path: str, sheet: str = None) -> Optional[dict]:
        key = f"excel:{sheet}" if sheet else "excel"
        return self._content_cache.get(file_path, key)
    
    def put_excel_data(self, file_path: str, data: dict, sheet: str = None):
        key = f"excel:{sheet}" if sheet else "excel"
        self._content_cache.put(file_path, data, key)
    
    def clear(self, file_path: str = None):
        if file_path:
            self._content_cache.remove(file_path)
            self._metadata_cache.remove(file_path)
        else:
            self._content_cache.clear()
            self._metadata_cache.clear()
    
    def stats(self):
        return {
            'content_cache': self._content_cache.stats(),
            'metadata_cache': self._metadata_cache.stats()
        }
```

**验收标准**: 支持 Word/Excel/PDF 缓存，提供统计信息

---

#### 任务 1.3：创建数据缓存管理器

**文件**: `src/core/cache/data_cache_manager.py`

```python
"""
数据缓存管理器
"""

import logging
from .base_cache import BaseCache

logger = logging.getLogger(__name__)


class DataCacheManager:
    def __init__(self, max_size=500, ttl=1800):
        self._matrix_cache = BaseCache(max_size=max_size, ttl=ttl)
        self._ltr_cache = BaseCache(max_size=max_size, ttl=ttl)
        self._export_cache = BaseCache(max_size=max_size//2, ttl=ttl*2)
    
    def get_matrix_data(self, matrix_id: str) -> Optional[dict]:
        return self._matrix_cache.get(f"matrix:{matrix_id}")
    
    def put_matrix_data(self, matrix_id: str, data: dict):
        self._matrix_cache.put(f"matrix:{matrix_id}", data)
    
    def get_export_result(self, matrix_id: str, fmt: str, **options) -> Optional[str]:
        key = f"export:{matrix_id}:{fmt}:{hash(str(options))}"
        return self._export_cache.get(key)
    
    def put_export_result(self, matrix_id: str, fmt: str, output_path: str, **options):
        key = f"export:{matrix_id}:{fmt}:{hash(str(options))}"
        self._export_cache.put(key, output_path)
    
    def clear_matrix(self, matrix_id: str = None):
        if matrix_id:
            self._matrix_cache.remove(f"matrix:{matrix_id}")
        else:
            self._matrix_cache.clear()
    
    def stats(self):
        return {
            'matrix_cache': self._matrix_cache.stats(),
            'export_cache': self._export_cache.stats()
        }
```

**验收标准**: 支持 Matrix/LTR/导出结果缓存，提供细粒度清除

---

### 第二阶段：集成到现有服务（12小时）

#### 任务 2.1：集成到 Word 工具

**文件**: `src/utils/word_utils.py`

```python
from src.core.cache.document_cache_manager import DocumentCacheManager

document_cache = DocumentCacheManager(max_size=100, ttl=3600)

class WordUtils:
    def __init__(self):
        self._cache_enabled = True
    
    def get_document_content(self, file_path: str, use_cache=True) -> str:
        if self._cache_enabled and use_cache:
            cached = document_cache.get_word_content(file_path)
            if cached is not None:
                return cached
        
        content = self._read_from_word(file_path)
        
        if self._cache_enabled and use_cache:
            document_cache.put_word_content(file_path, content)
        
        return content
    
    def _read_from_word(self, file_path: str) -> str:
        // 实际 Word 读取逻辑
        pass
```

**性能提升**: 2-5秒 → 0.1-0.3秒（缓存命中）

---

#### 任务 2.2：集成到 Matrix 服务

**文件**: `src/features/matrix/service/matrix_service.py`

```python
from src.core.cache.data_cache_manager import DataCacheManager

data_cache = DataCacheManager(max_size=500, ttl=1800)

class MatrixService(BaseService):
    def __init__(self):
        super().__init__("MatrixService")
        self._cache_enabled = True
    
    def load_matrix_data(self, file_path: str, use_cache=True) -> dict:
        matrix_id = os.path.basename(file_path)
        
        if self._cache_enabled and use_cache:
            cached = data_cache.get_matrix_data(matrix_id)
            if cached is not None:
                return cached
        
        data = self._read_matrix_file(file_path)
        
        if self._cache_enabled and use_cache:
            data_cache.put_matrix_data(matrix_id, data)
        
        return data
    
    def export_matrix(self, matrix_id: str, fmt: str, output_path: str, use_cache=True) -> bool:
        if self._cache_enabled and use_cache:
            cached_path = data_cache.get_export_result(matrix_id, fmt)
            if cached_path and os.path.exists(cached_path):
                import shutil
                shutil.copy2(cached_path, output_path)
                return True
        
        success = self._perform_export(matrix_id, fmt, output_path)
        
        if self._cache_enabled and use_cache and success:
            data_cache.put_export_result(matrix_id, fmt, output_path)
        
        return success
```

**性能提升**: 导出 3-8秒 → 0.2-0.5秒（缓存命中）

---

### 第三阶段：缓存失效机制（4小时）

#### 任务 3.1：文件监听自动失效

**文件**: `src/core/cache/file_watcher.py`

```python
import os
import time
import threading

class FileWatcher:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self._watched = {}
        self._running = False
    
    def watch(self, file_path: str):
        self._watched[file_path] = os.path.getmtime(file_path)
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    
    def _loop(self):
        while self._running:
            for file_path, old_mtime in list(self._watched.items()):
                try:
                    current_mtime = os.path.getmtime(file_path)
                    if current_mtime != old_mtime:
                        self.cache_manager.document.clear(file_path)
                        self._watched[file_path] = current_mtime
                except FileNotFoundError:
                    del self._watched[file_path]
            time.sleep(5)
```

---

### 第四阶段：性能基准测试（4小时）

#### 任务 4.1：创建性能测试

**文件**: `tests/test_cache_performance.py`

```python
import time
import pytest

class TestCachePerformance:
    def test_word_cache_performance(self):
        from src.utils.word_utils import WordUtils
        
        word_utils = WordUtils()
        test_file = "tests/data/test.docx"
        
        // 第一次调用（无缓存）
        start = time.perf_counter()
        content1 = word_utils.get_document_content(test_file)
        duration1 = time.perf_counter() - start
        
        // 第二次调用（有缓存）
        start = time.perf_counter()
        content2 = word_utils.get_document_content(test_file)
        duration2 = time.perf_counter() - start
        
        assert content1 == content2
        assert duration2 < duration1 * 0.2
        
        print(f"Word cache: {duration1:.3f}s → {duration2:.3f}s")
    
    def test_matrix_export_performance(self):
        from src.features.matrix.service.matrix_service import MatrixService
        
        service = MatrixService()
        
        // 第一次导出
        start = time.perf_counter()
        service.export_matrix("test", "LLCRCR", "/tmp/test1.xlsx")
        duration1 = time.perf_counter() - start
        
        // 第二次导出（使用缓存）
        start = time.perf_counter()
        service.export_matrix("test", "LLCRCR", "/tmp/test2.xlsx")
        duration2 = time.perf_counter() - start
        
        assert duration2 < duration1 * 0.1
        
        print(f"Export cache: {duration1:.3f}s → {duration2:.3f}s")
```

**验收标准**: 缓存命中率 > 85%，性能提升 > 70%

---

## 📊 预期效果

### 性能提升

| 操作 | 修复前 | 修复后 | 提升 |
|------|--------|--------|------|
| Word 文档解析 | 2-5s | 0.1-0.3s | 90-95% |
| Matrix 导出 | 3-8s | 0.2-0.5s | 85-90% |
| 配置读取 | 50ms | <1ms | 95%+ |
| 数据加载 | 100ms | 5ms | 90% |

### 缓存指标

- 缓存命中率：> 85%
- 内存占用增加：< 200MB
- TTL自动失效：支持
- 文件变更自动清除：支持

---

## 🎯 成功标准

- [ ] Word文档解析时间 < 0.3秒（缓存命中）
- [ ] Matrix导出时间 < 0.5秒（缓存命中）
- [ ] 缓存命中率 > 85%
- [ ] 所有缓存自动失效机制正常
- [ ] 内存占用增加 < 200MB
- [ ] 通过所有性能基准测试

---

## ⚠️ 风险与对策

| 风险 | 对策 |
|------|------|
| 缓存数据不一致 | 文件监听自动清除 + TTL过期 |
| 内存占用过高 | 限制缓存大小 + LRU淘汰 |
| 缓存击穿 | 互斥锁保护 + 预热机制 |
| 缓存雪崩 | 随机TTL偏移 + 限流 |

---

## 📝 使用示例

### 基础使用

```python
from src.core.cache import cache_manager

// 自动缓存
data = cache_manager.data.get_matrix_data("matrix001")
if data is None:
    data = load_from_file()
    cache_manager.data.put_matrix_data("matrix001", data)

// 清除缓存
cache_manager.data.clear_matrix("matrix001")

// 获取统计
stats = cache_manager.get_stats()
print(f"命中率: {stats['document']['hit_rate']:.2%}")
```

### Word工具集成

```python
from src.utils.word_utils import WordUtils

word_utils = WordUtils()

// 第一次：从Word读取（慢）
content = word_utils.get_document_content("doc.docx")

// 第二次：从缓存读取（快）
content = word_utils.get_document_content("doc.docx")

// 强制刷新
content = word_utils.get_document_content("doc.docx", use_cache=False)
```

### Matrix服务集成

```python
from src.features.matrix.service.matrix_service import MatrixService

service = MatrixService()

// 导出（自动缓存结果文件）
service.export_matrix("test", "LLCRCR", "output1.xlsx")

// 再次导出（复制缓存文件，极快）
service.export_matrix("test", "LLCRCR", "output2.xlsx")
```

---

**任务文档完成**: 2026-04-07  
**预计完成时间**: 2026-04-10  
**验收标准**: 所有性能指标达标
