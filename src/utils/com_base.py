"""
COM应用程序管理基类
提供Word和Excel COM操作的通用基础功能
"""

import threading
from abc import ABC, abstractmethod
from typing import Optional, Any
import pythoncom
from src.core.logger import logger


class COMApplicationManager(ABC):
    """
    COM应用程序管理器基类
    提供共享实例管理、引用计数、线程安全和健康检查
    """
    
    def __init__(self, app_name: str):
        """
        初始化COM应用程序管理器
        
        Args:
            app_name: 应用程序名称（如 "Word" 或 "Excel"）
        """
        self._app_name = app_name
        self._shared_app: Optional[Any] = None
        self._instance_count = 0
        self._initialized = False
        self._lock = threading.Lock()
        
    @abstractmethod
    def _create_application(self) -> Any:
        """
        创建COM应用程序实例
        
        Returns:
            COM应用程序对象
        """
        pass
        
    @abstractmethod
    def _is_application_responsive(self, app: Any) -> bool:
        """
        检查应用程序是否响应
        
        Args:
            app: COM应用程序对象
            
        Returns:
            如果应用程序响应返回True，否则返回False
        """
        pass
        
    @abstractmethod
    def _close_documents(self, app: Any) -> None:
        """
        关闭所有打开的文档
        
        Args:
            app: COM应用程序对象
        """
        pass
        
    def get_shared_app(self) -> Optional[Any]:
        """
        获取共享的COM应用程序实例
        
        Returns:
            COM应用程序对象或None（如果初始化失败）
        """
        with self._lock:
            # 检查应用程序是否仍然可用
            if self._shared_app is not None:
                try:
                    if not self._is_application_responsive(self._shared_app):
                        self._shared_app = None
                        self._instance_count = 0
                        self._initialized = False
                        logger.debug(f"Previous {self._app_name} application instance was not responsive, will create a new one")
                except Exception as e:
                    logger.debug(f"Error checking {self._app_name} application responsiveness: {e}")
                    self._shared_app = None
                    self._instance_count = 0
                    self._initialized = False

            if self._shared_app is None:
                try:
                    # 确保COM库已初始化
                    if not self._initialized:
                        pythoncom.CoInitialize()
                        self._initialized = True
                        
                    self._shared_app = self._create_application()
                    logger.debug(f"Created new shared {self._app_name} application instance")
                except Exception as e:
                    logger.error(f"Failed to initialize {self._app_name} application: {e}")
                    return None

        self._instance_count += 1
        logger.debug(f"{self._app_name} instance count increased to {self._instance_count}")
        return self._shared_app
        
    def release_app(self) -> None:
        """释放COM应用程序实例"""
        with self._lock:
            self._instance_count -= 1
            logger.debug(f"{self._app_name} instance count decreased to {self._instance_count}")

        # 当实例计数为0时，关闭文档但保持应用运行以提高性能
        if self._instance_count <= 0 and self._shared_app:
            try:
                self._close_documents(self._shared_app)
                logger.debug(f"Closed all documents but kept {self._app_name} application running")
            except Exception as e:
                logger.error(f"Error while closing {self._app_name} documents: {e}")
                
    def cleanup_resources(self) -> None:
        """彻底清理COM资源，在应用退出时调用"""
        if self._shared_app:
            with self._lock:
                try:
                    if self._is_application_responsive(self._shared_app):
                        self._close_documents(self._shared_app)
                        self._shared_app.Quit()
                        logger.debug(f"{self._app_name} application quit successfully")
                except Exception as e:
                    logger.error(f"Error while cleaning up {self._app_name} resources: {e}")
                finally:
                    self._shared_app = None

            # 反初始化COM
            if self._initialized:
                try:
                    pythoncom.CoUninitialize()
                    self._initialized = False
                except Exception as e:
                    logger.debug(f"Error while uninitializing COM for {self._app_name}: {e}")
                    
    def get_instance_count(self) -> int:
        """
        获取当前实例计数
        
        Returns:
            实例计数
        """
        with self._lock:
            return self._instance_count
