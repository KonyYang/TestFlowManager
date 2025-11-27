"""
主应用程序入口
负责启动和管理整个应用程序
"""

import sys
import os
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

        # 创建主窗口
        main_window = MainWindow()
        
        # 显示主窗口
        main_window.show()
        
        # 运行应用程序
        exit_code = app.exec_()
        
        # 应用程序退出前清理Word资源
        word_utils.cleanup_word_resources()
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()