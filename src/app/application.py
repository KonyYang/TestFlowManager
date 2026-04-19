# src/app/application.py
"""
主应用程序入口
负责启动和管理整个应用程序

启动性能优化记录：
- 移除模块级 word_utils 导入（避免启动时加载 COM 库）
- 移除 initialize_numpy()（NumPy 改为按需导入）
- MainWindowController 非核心组件延迟初始化
- Spec 改用 onedir 模式（避免运行时解压归档）
"""

import sys
import os
import time
import logging

# ========== 启动计时开始 ==========
_START_TIME = time.perf_counter()

# 添加项目根目录到 Python 路径（仅在开发模式下需要）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.app.composition.main_window_assembler import assemble_main_window
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.core.path_utils import get_resource_path, get_executable_dir
import src

def create_main_window(splash_screen=None):
    """创建主窗口的工厂函数

    Args:
        splash_screen: 启动进度窗口实例
    """
    try:
        logger.info("开始创建主窗口...")
        main_window = assemble_main_window(splash_screen)

        # 设置应用程序图标（兼容开发和打包模式）
        icon_path = get_resource_path("resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            main_window.setWindowIcon(QIcon(icon_path))

        logger.info("主窗口创建完成")
        return main_window
    except Exception as e:
        logger.error(f"创建主窗口时出错: {e}")
        raise

def main():
    """主函数"""
    _t_main = time.perf_counter()
    logger.info(f"[启动耗时] 模块导入完成: {_t_main - _START_TIME:.3f}s")
    
    try:
        # 设置应用程序属性
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setApplicationName("TestFlowManager")
        app.setApplicationVersion(src.__version__)
        
        _t_qt = time.perf_counter()
        logger.info(f"[启动耗时] PyQt5 初始化: {_t_qt - _t_main:.3f}s")
        
        # 设置应用程序图标（兼容开发和打包模式）
        icon_path = get_resource_path("resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # 记录应用程序启动信息
        logger.info("TestFlowManager应用程序启动")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"应用程序路径: {os.path.abspath(__file__)}")
        
        # 记录系统相关信息
        logger.info(f"操作系统: {os.name}")
        if hasattr(os, 'uname'):
            logger.info(f"系统信息: {os.uname()}")

        # 直接启动主窗口（启动已优化至<0.1秒，无需进度提示）
        logger.info("直接启动主窗口")
        _t_create = time.perf_counter()
        main_window = create_main_window(None)
        logger.info(f"[启动耗时] 主窗口创建: {time.perf_counter() - _t_create:.3f}s")
        main_window.show()
        _t_show = time.perf_counter()
        logger.info(f"[启动耗时] 主窗口显示: {_t_show - _t_create:.3f}s")
        logger.info(f"[启动耗时] 总耗时(到显示): {_t_show - _START_TIME:.3f}s")
        logger.info("主窗口已显示")
        
        # 运行应用程序
        logger.info("进入应用程序主循环")
        exit_code = app.exec_()
        logger.info(f"应用程序主循环结束，退出码: {exit_code}")
        
        # 应用程序退出前执行清理（通过 shutdown_registry）
        logger.info("执行应用程序清理...")
        
        # 注册全局 COM 清理钩子（如果在主窗口关闭时未执行）
        from src.core.shutdown_registry import shutdown_registry
        
        def _release_all_com_objects():
            """释放所有 COM 对象"""
            try:
                from src.utils import word_utils, excel_utils
                word_utils.release_word_app()
                excel_utils.release_excel_app()
                logger.info("COM objects released successfully")
            except Exception as e:
                logger.error(f"Failed to release COM objects: {e}")
        
        # 动态注册 COM 清理（确保在 application 层执行）
        if shutdown_registry.hook_count == 0:
            # 如果 shutdown_registry 为空（主窗口未正常加载），手动执行清理
            logger.warning("ShutdownRegistry is empty, executing fallback cleanup")
            _release_all_com_objects()
        elif not shutdown_registry.has_executed:
            # 执行所有注册的清理钩子（仅当未被执行过）
            shutdown_registry.execute_all()
        else:
            logger.debug("Shutdown hooks already executed by MainWindowController")
        
        logger.info("应用程序清理完成")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
