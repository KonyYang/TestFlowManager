"""
应用程序入口模块
负责初始化和启动应用程序
"""

import sys
from PyQt5.QtWidgets import QApplication
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.managers.window_manager import WindowManager
from PyQt5.QtCore import Qt

class TestFlowApplication:
    """
    TestFlow Manager 应用程序主类
    负责应用程序的初始化、运行和关闭
    """

    def __init__(self):
        self.app = None
        self.window_manager = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        初始化应用程序

        Returns:
            初始化是否成功
        """
        try:
            logger.info("Initializing TestFlow Manager application")

            # 👇 关键：启用高 DPI 支持（必须在 QApplication 前设置）
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            # 创建Qt应用程序实例
            self.app = QApplication(sys.argv)

            # 初始化窗口管理器
            self.window_manager = WindowManager()

            # 加载配置
            app_name = config_manager.get("app.name", "TestFlowManager")
            self.app.setApplicationName(app_name)

            version = config_manager.get("app.version", "1.0.0")
            self.app.setApplicationVersion(version)

            # 加载路径配置
            config_manager.load_paths_config()

            logger.info("Application initialized successfully")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            return False

    def run(self) -> int:
        """
        运行应用程序

        Returns:
            应用程序退出码
        """
        if not self._initialized:
            logger.error("Application not initialized")
            return -1

        try:
            logger.info("Starting TestFlow Manager application")

            # 显示主窗口
            self.window_manager.show_main_window()

            # 运行应用程序主循环
            exit_code = self.app.exec_()

            logger.info("Application exited")
            return exit_code

        except Exception as e:
            logger.error(f"Error while running application: {e}")
            return -1

    def shutdown(self) -> None:
        """关闭应用程序"""
        logger.info("Shutting down TestFlow Manager application")

        # 保存配置
        config_manager.save_config()

        # 关闭所有窗口
        if self.window_manager:
            self.window_manager.close_all_windows()


def main():
    """应用程序入口点"""
    # 创建应用程序实例
    app_instance = TestFlowApplication()

    # 初始化应用程序
    if not app_instance.initialize():
        sys.exit(1)

    # 运行应用程序
    exit_code = app_instance.run()

    # 关闭应用程序
    app_instance.shutdown()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
