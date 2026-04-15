"""
应用关闭时的清理注册表

各模块在初始化时注册自己的清理函数，
应用关闭时统一按优先级执行。
"""
from typing import Callable, List, Tuple
from src.core.logger import logger


class ShutdownRegistry:
    """
    应用关闭时的清理注册表
    
    使用示例:
        registry = ShutdownRegistry()
        registry.register("MyModule.cleanup", my_cleanup_fn, priority=50)
        registry.execute_all()
    """
    
    def __init__(self):
        self._hooks: List[Tuple[str, Callable, int]] = []
        self._executed = False
    
    def register(self, name: str, cleanup_fn: Callable, priority: int = 100) -> None:
        """
        注册清理钩子
        
        Args:
            name: 钩子名称（用于日志和调试）
            cleanup_fn: 清理函数（无参数，无返回值）
            priority: 优先级（数字越小越先执行，默认 100）
        
        Example:
            >>> registry.register("EventBindingManager.unbind", manager.unbind_all, priority=10)
        """
        self._hooks.append((name, cleanup_fn, priority))
        self._hooks.sort(key=lambda x: x[2])
        logger.debug(f"Registered shutdown hook: {name} (priority={priority})")
    
    def unregister(self, name: str) -> bool:
        """
        注销清理钩子
        
        Args:
            name: 钩子名称
        
        Returns:
            是否成功注销
        """
        original_count = len(self._hooks)
        self._hooks = [(n, fn, p) for n, fn, p in self._hooks if n != name]
        removed = original_count - len(self._hooks) > 0
        
        if removed:
            logger.debug(f"Unregistered shutdown hook: {name}")
        
        return removed
    
    def execute_all(self) -> dict:
        """
        执行所有注册的清理钩子
        
        Returns:
            执行结果字典，包含成功和失败的钩子列表
        
        Example:
            >>> result = registry.execute_all()
            >>> print(f"Success: {len(result['success'])}, Failed: {len(result['failed'])}")
        """
        if self._executed:
            logger.warning("ShutdownRegistry.execute_all() called multiple times")
        
        results = {
            "success": [],
            "failed": []
        }
        
        logger.info(f"Executing {len(self._hooks)} shutdown hooks...")
        
        for name, cleanup_fn, priority in self._hooks:
            try:
                logger.debug(f"Executing shutdown hook: {name} (priority={priority})")
                cleanup_fn()
                results["success"].append(name)
                logger.debug(f"Shutdown hook completed: {name}")
            except Exception as e:
                results["failed"].append({
                    "name": name,
                    "error": str(e),
                    "priority": priority
                })
                logger.error(f"Shutdown hook failed: {name} - {type(e).__name__}: {e}")
        
        self._executed = True
        
        success_count = len(results["success"])
        failed_count = len(results["failed"])
        logger.info(
            f"Shutdown hooks execution completed: "
            f"{success_count} succeeded, {failed_count} failed"
        )
        
        if results["failed"]:
            logger.warning(
                f"Failed hooks: {[f['name'] for f in results['failed']]}"
            )
        
        return results
    
    def clear(self) -> None:
        """清空所有钩子（主要用于测试）"""
        self._hooks.clear()
        self._executed = False
        logger.debug("ShutdownRegistry cleared")
    
    def get_registered_hooks(self) -> List[Tuple[str, int]]:
        """
        获取已注册的钩子列表（用于调试）
        
        Returns:
            钩子名称和优先级的列表
        """
        return [(name, priority) for name, _, priority in self._hooks]
    
    @property
    def hook_count(self) -> int:
        """已注册的钩子数量"""
        return len(self._hooks)
    
    @property
    def has_executed(self) -> bool:
        """是否已执行过"""
        return self._executed


# 全局单例实例
shutdown_registry = ShutdownRegistry()
