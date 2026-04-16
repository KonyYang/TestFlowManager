# src/shell/main_window/components/startup_profiler.py
"""
启动性能分析器模块
统一管理应用启动过程中的性能监控和日志记录
"""
import time
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, field

from src.core.logger import logger


@dataclass
class PhaseRecord:
    """阶段性能记录"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    message: str = ""
    
    @property
    def duration(self) -> float:
        """计算耗时（秒）"""
        if self.end_time is not None:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.end_time is not None


class StartupProfiler:
    """
    启动性能分析器 - 统一管理应用启动性能监控
    
    职责：
    - 记录每个初始化阶段的开始和结束时间
    - 自动计算各阶段耗时
    - 提供进度通知回调
    - 生成性能报告
    
    使用示例：
        profiler = StartupProfiler(splash_screen=splash)
        
        with profiler.phase("初始化UI", "正在初始化基础界面..."):
            self._setup_basic_ui()
        
        with profiler.phase("初始化控制器", "正在初始化控制器..."):
            self._initialize_controllers()
        
        profiler.log_summary()
    """
    
    def __init__(
        self,
        splash_screen=None,
        progress_signal=None,
        log_level: str = "info",
    ):
        """
        初始化性能分析器
        
        Args:
            splash_screen: 启动画面（可选），用于更新进度
            progress_signal: Qt 信号（可选），用于发送进度事件
            log_level: 日志级别（默认：info）
        """
        self.splash_screen = splash_screen
        self.progress_signal = progress_signal
        self.log_level = log_level
        
        self._start_time: Optional[float] = None
        self._phases: List[PhaseRecord] = []
        self._current_phase: Optional[PhaseRecord] = None
    
    def start(self) -> None:
        """开始性能监控"""
        self._start_time = time.time()
        logger.info("[性能] 开始启动性能监控")
    
    def phase(self, name: str, message: str = "") -> 'PhaseContext':
        """
        创建性能监控阶段（上下文管理器）
        
        Args:
            name: 阶段名称
            message: 进度消息
            
        Returns:
            PhaseContext: 上下文管理器
        """
        return PhaseContext(self, name, message)
    
    def _begin_phase(self, name: str, message: str) -> None:
        """开始一个阶段（内部方法）"""
        # 结束当前阶段（如果有）
        if self._current_phase is not None and not self._current_phase.is_completed:
            self._end_current_phase()
        
        # 创建新阶段
        self._current_phase = PhaseRecord(
            name=name,
            start_time=time.time(),
            message=message,
        )
        self._phases.append(self._current_phase)
        
        # 通知进度
        phase_index = len(self._phases) - 1
        self._notify_progress(phase_index, message)
        
        logger.debug(f"[性能] 开始阶段: {name}")
    
    def _end_current_phase(self) -> None:
        """结束当前阶段（内部方法）"""
        if self._current_phase is not None:
            self._current_phase.end_time = time.time()
            duration = self._current_phase.duration
            logger.info(f"[性能] {self._current_phase.name}耗时: {duration:.3f}秒")
            self._current_phase = None
    
    def _notify_progress(self, step: int, message: str) -> None:
        """通知进度"""
        # 更新启动画面
        if self.splash_screen:
            self.splash_screen.update_progress(step, message)
        
        # 发送 Qt 信号
        if self.progress_signal:
            self.progress_signal.emit(step, message)
    
    def log_summary(self) -> Dict[str, float]:
        """
        记录性能摘要
        
        Returns:
            包含各阶段耗时的字典
        """
        # 确保所有阶段都已结束
        if self._current_phase is not None:
            self._end_current_phase()
        
        if self._start_time is None:
            logger.warning("[性能] 未启动性能监控")
            return {}
        
        total_time = time.time() - self._start_time
        
        logger.info("=" * 60)
        logger.info("[性能] 启动性能报告")
        logger.info("=" * 60)
        
        phase_times = {}
        for phase in self._phases:
            phase_times[phase.name] = phase.duration
            logger.info(f"  {phase.name:<20s}: {phase.duration:.3f}秒")
        
        logger.info("-" * 60)
        logger.info(f"  {'总耗时':<20s}: {total_time:.3f}秒")
        logger.info("=" * 60)
        
        return phase_times
    
    def get_phase_times(self) -> Dict[str, float]:
        """
        获取各阶段耗时
        
        Returns:
            阶段名称 -> 耗时（秒）的字典
        """
        return {phase.name: phase.duration for phase in self._phases}
    
    def get_total_time(self) -> float:
        """
        获取总耗时
        
        Returns:
            总耗时（秒）
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time


class PhaseContext:
    """
    阶段上下文管理器
    
    用于 with 语句，自动管理阶段的开始和结束
    """
    
    def __init__(self, profiler: StartupProfiler, name: str, message: str):
        self.profiler = profiler
        self.name = name
        self.message = message
    
    def __enter__(self):
        self.profiler._begin_phase(self.name, self.message)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.profiler._end_current_phase()
        # 不抑制异常
        return False
