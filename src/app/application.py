# src/app/application.py
"""
主应用程序入口
负责启动和管理整个应用程序
"""

import sys
import os
import logging

# 添加项目根目录到 Python 路径，这样可以正确导入模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.app.composition.main_window_assembler import assemble_main_window
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.utils import word_utils
import src

def initialize_numpy():
    """
    初始化NumPy以防止在PyInstaller打包的应用程序中出现重复初始化错误
    """
    try:
        # 在应用程序启动时设置环境变量，防止NumPy重复初始化
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        os.environ['NUMEXPR_NUM_THREADS'] = '1'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['NPY_DISABLE_CPU_FEATURES'] = '1'
        
        # 尝试预先导入numpy相关模块
        try:
            import numpy
            logger.info(f"NumPy版本: {numpy.__version__}")
        except Exception as e:
            # 这里我们忽略NumPy初始化警告，因为它不影响应用程序的基本功能
            logger.debug(f"NumPy预导入警告（可忽略）: {e}")
            
    except Exception as e:
        logger.warning(f"NumPy初始化处理失败: {e}")

def create_main_window(splash_screen=None):
    """创建主窗口的工厂函数
    
    Args:
        splash_screen: 启动进度窗口实例
    """
    try:
        logger.info("开始创建主窗口...")
        main_window = assemble_main_window(splash_screen)
        
        # 设置应用程序图标
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "app_icon.ico")
        if os.path.exists(icon_path):
            main_window.setWindowIcon(QIcon(icon_path))
            
        logger.info("主窗口创建完成")
        return main_window
    except Exception as e:
        logger.error(f"创建主窗口时出错: {e}")
        raise

def main():
    """主函数"""
    try:
        # 在应用程序启动时初始化NumPy
        initialize_numpy()
        
        # 设置应用程序属性
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setApplicationName("TestFlowManager")
        app.setApplicationVersion(src.__version__)
        
        # 设置应用程序图标
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "app_icon.ico")
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
        main_window = create_main_window(None)
        main_window.show()
        logger.info("主窗口已显示")
        
        # 运行应用程序
        logger.info("进入应用程序主循环")
        exit_code = app.exec_()
        logger.info(f"应用程序主循环结束，退出码: {exit_code}")
        
        # 应用程序退出前清理Word资源
        logger.info("清理Word资源")
        word_utils.cleanup_word_resources()
        logger.info("Word资源清理完成")
        
        # 应用程序退出前清理Excel资源
        logger.info("清理Excel资源")
        try:
            from src.utils import excel_utils
            excel_utils.release_excel_app()
            logger.info("Excel资源清理完成")
        except Exception as e:
            logger.error(f"清理Excel资源时出错: {e}")
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        # 添加额外的错误信息输出到控制台，便于调试
        print(f"严重错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
