"""
主应用程序入口
负责启动和管理整个应用程序
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from src.features.main_window.view.main_window_ui import MainWindow
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.utils import word_utils


def main():
    """主函数"""
    try:
        # 设置应用程序属性
        app = QApplication(sys.argv)
        app.setApplicationName("TestFlowManager")
        app.setApplicationVersion("1.0.0")

        # 记录应用程序启动信息
        logger.info("TestFlowManager应用程序启动")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"应用程序路径: {os.path.abspath(__file__)}")
        
        # 记录系统相关信息
        logger.info(f"操作系统: {os.name}")
        if hasattr(os, 'uname'):
            logger.info(f"系统信息: {os.uname()}")

        # 创建主窗口
        main_window = MainWindow()
        logger.info("主窗口已创建")
        
        # 显示主窗口
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
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()