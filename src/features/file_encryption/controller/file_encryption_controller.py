# src/features/file_encryption/controller/file_encryption_controller.py
"""
文件加密控制器模块 - 使用标准 threading 模块
处理用户交互和业务逻辑之间的协调
"""

import threading
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QObject
from src.core.logger import logger
from src.features.file_encryption.service.file_encryption_service import (
    SignalEmitter,
    start_encryption_thread
)


class FileEncryptionController(QObject):
    """文件加密控制器类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.emitter = None
        self.thread = None
        # 保持对 emitter 的引用，防止被垃圾回收
        self._emitter_refs = []
    
    def show_folder_selection(self):
        """显示文件夹选择对话框"""
        folder_path = QFileDialog.getExistingDirectory(
            self.parent,
            "请选择项目文件夹中的 'Test results' 文件夹",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder_path:
            logger.info(f"用户选择了文件夹：{folder_path}")
        
        return folder_path
    
    def start_encryption_task(self, folder_path: str):
        """启动加密任务（使用标准 threading 模块）"""
        try:
            logger.info(f"开始加密任务：{folder_path}")
            
            # 创建信号发射器
            logger.debug("[1] 创建 SignalEmitter 实例...")
            self.emitter = SignalEmitter()
            # 保持引用，防止被垃圾回收
            self._emitter_refs.append(self.emitter)
            logger.debug("✅ SignalEmitter 实例创建成功")
            
            # 连接信号
            logger.debug("[2] 连接信号...")
            self.emitter.started_signal.connect(self._on_encryption_started)
            logger.debug("  ✅ started_signal 已连接")
            
            self.emitter.finished_signal.connect(self._on_encryption_finished)
            logger.debug("  ✅ finished_signal 已连接")
            
            self.emitter.error_signal.connect(self._on_encryption_error)
            logger.debug("  ✅ error_signal 已连接")
            
            # 创建并启动线程
            logger.debug("\n[3] 创建 threading.Thread 实例...")
            self.thread = threading.Thread(target=start_encryption_thread, args=(folder_path, self.emitter))
            # self.thread.daemon = True  # 设置为守护线程
            self.thread.start()
            logger.debug("✅ 线程启动成功！")
            
            logger.debug("加密工作线程已启动")
            
        except Exception as e:
            logger.error(f"启动加密任务时出错：{e}", exc_info=True)
            if self.parent:
                QMessageBox.critical(
                    self.parent,
                    "错误",
                    f"启动加密任务失败：{str(e)}"
                )
    
    def _on_encryption_started(self):
        """加密开始时的回调"""
        logger.info("加密任务开始执行...")
    
    def _on_encryption_finished(self, stats: dict):
        """加密完成时的回调"""
        logger.info("加密任务完成")
        
        total = stats.get('total', 0)
        excel_count = stats.get('excel', 0)
        word_count = stats.get('word', 0)
        success = stats.get('success', 0)
        failed = stats.get('failed', 0)
        
        message = (
            f"成功处理 {success} 个文件\n\n"
            f"Excel 文件：{excel_count}\n"
            f"Word 文件：{word_count}\n"
            f"成功：{success}\n"
            f"失败：{failed}"
        )
        
        try:
            if self.parent:
                # 使用无父窗口的消息框，避免父窗口状态问题
                if failed > 0:
                    QMessageBox.warning(
                        None,  # 不使用父窗口
                        "加密完成（部分失败）",
                        message
                    )
                else:
                    QMessageBox.information(
                        None,  # 不使用父窗口
                        "加密完成",
                        message
                    )
            
            # 通过 parent 更新状态栏 (调用 MainWindowUi 的_update_status 方法)
            if self.parent and hasattr(self.parent, '_update_status'):
                self.parent._update_status()
        except Exception as e:
            logger.error(f"显示加密完成消息框时出错：{e}", exc_info=True)
        finally:
            # 清理 emitter 引用
            if self.emitter in self._emitter_refs:
                self._emitter_refs.remove(self.emitter)
    
    def _on_encryption_error(self, error_msg: str):
        """加密发生错误时的回调"""
        logger.error(f"加密过程发生错误：{error_msg}")
        
        try:
            if self.parent:
                # 使用无父窗口的消息框，避免父窗口状态问题
                QMessageBox.critical(
                    None,  # 不使用父窗口
                    "加密失败",
                    error_msg
                )
            
            # 通过 parent 更新状态栏 (调用 MainWindowUi 的_update_status 方法)
            if self.parent and hasattr(self.parent, '_update_status'):
                self.parent._update_status()
        except Exception as e:
            logger.error(f"显示加密错误消息框时出错：{e}", exc_info=True)
        finally:
            # 清理 emitter 引用
            if self.emitter in self._emitter_refs:
                self._emitter_refs.remove(self.emitter)
