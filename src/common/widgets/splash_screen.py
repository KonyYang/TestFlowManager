"""
启动进度窗口模块
提供应用程序启动时的进度提示界面
"""
import os
from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor
from src.core.logger import logger


class SplashScreen(QSplashScreen):
    """
    启动进度窗口类
    显示应用程序启动进度和状态信息
    """
    
    def __init__(self):
        """初始化启动进度窗口"""
        # 创建透明的启动画面
        super().__init__()
        
        self.progress_steps = [
            "正在初始化应用程序...",
            "正在加载配置文件...",
            "正在创建主窗口...",
            "正在初始化控制器...",
            "正在加载界面组件...",
            "正在准备Matrix编辑器...",
            "正在初始化报告系统...",
            "即将完成启动..."
        ]
        
        self.current_step = 0
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        try:
            # 设置窗口属性
            self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            
            # 创建主部件
            self.main_widget = QWidget()
            self.main_widget.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 255, 255, 230);
                    border: 2px solid #4A90E2;
                    border-radius: 15px;
                }
            """)
            
            layout = QVBoxLayout()
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(20)
            
            # 标题标签
            self.title_label = QLabel("TestFlow Manager")
            title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
            self.title_label.setFont(title_font)
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setStyleSheet("color: #2C3E50; padding: 10px;")
            layout.addWidget(self.title_label)
            
            # 状态标签
            self.status_label = QLabel("正在启动应用程序...")
            status_font = QFont("Microsoft YaHei", 10)
            self.status_label.setFont(status_font)
            self.status_label.setAlignment(Qt.AlignCenter)
            self.status_label.setStyleSheet("color: #34495E; padding: 5px;")
            layout.addWidget(self.status_label)
            
            # 进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self.progress_steps) - 1)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #BDC3C7;
                    border-radius: 10px;
                    text-align: center;
                    color: #2C3E50;
                    font-weight: bold;
                    background-color: #ECF0F1;
                }
                QProgressBar::chunk {
                    background-color: #4A90E2;
                    border-radius: 8px;
                }
            """)
            layout.addWidget(self.progress_bar)
            
            # 版本信息
            self.version_label = QLabel("版本 1.0.0")
            version_font = QFont("Microsoft YaHei", 8)
            self.version_label.setFont(version_font)
            self.version_label.setAlignment(Qt.AlignCenter)
            self.version_label.setStyleSheet("color: #7F8C8D; padding: 5px;")
            layout.addWidget(self.version_label)
            
            self.main_widget.setLayout(layout)
            
            # 设置窗口大小和位置
            self.main_widget.setFixedSize(400, 200)
            screen = self.screen().availableGeometry()
            self.main_widget.move(
                (screen.width() - self.main_widget.width()) // 2,
                (screen.height() - self.main_widget.height()) // 2
            )
            
            logger.info("启动进度窗口UI初始化完成")
            
        except Exception as e:
            logger.error(f"启动进度窗口UI初始化失败: {e}")
    
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        self.main_widget.show()
        logger.debug("启动进度窗口已显示")
    
    def hideEvent(self, event):
        """窗口隐藏事件"""
        super().hideEvent(event)
        self.main_widget.hide()
        logger.debug("启动进度窗口已隐藏")
    
    def update_progress(self, step_index=None, message=None):
        """
        更新进度
        
        Args:
            step_index: 步骤索引
            message: 自定义消息
        """
        try:
            if step_index is not None:
                self.current_step = step_index
            
            if message is not None:
                display_message = message
            elif self.current_step < len(self.progress_steps):
                display_message = self.progress_steps[self.current_step]
            else:
                display_message = "启动完成"
            
            # 更新状态标签
            self.status_label.setText(display_message)
            
            # 更新进度条
            self.progress_bar.setValue(self.current_step)
            self.progress_bar.setFormat(f"{self.current_step + 1}/{len(self.progress_steps)}")
            
            # 强制刷新界面
            self.main_widget.repaint()
            
            logger.debug(f"进度更新: {self.current_step + 1}/{len(self.progress_steps)} - {display_message}")
            
        except Exception as e:
            logger.error(f"更新进度时出错: {e}")
    
    def next_step(self, message=None):
        """
        进入下一步
        
        Args:
            message: 自定义消息
        """
        self.current_step += 1
        self.update_progress(message=message)
    
    def finish_startup(self):
        """完成启动过程"""
        try:
            # 显示完成消息
            self.update_progress(len(self.progress_steps) - 1, "启动完成，正在显示主窗口...")
            
            # 短暂延迟后关闭
            QTimer.singleShot(500, self.close)
            logger.info("启动进度窗口准备关闭")
            
        except Exception as e:
            logger.error(f"完成启动时出错: {e}")
            self.close()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            self.main_widget.close()
            super().closeEvent(event)
            logger.debug("启动进度窗口已关闭")
        except Exception as e:
            logger.error(f"关闭启动进度窗口时出错: {e}")
            event.accept()


# 便捷函数
def create_splash_screen():
    """
    创建启动进度窗口实例
    
    Returns:
        SplashScreen: 启动进度窗口实例
    """
    try:
        splash = SplashScreen()
        logger.info("启动进度窗口创建成功")
        return splash
    except Exception as e:
        logger.error(f"创建启动进度窗口失败: {e}")
        return None


def show_startup_progress(splash_screen, main_window_callback):
    """
    显示启动进度并逐步初始化应用程序
    
    Args:
        splash_screen: 启动进度窗口实例
        main_window_callback: 创建主窗口的回调函数
    """
    try:
        if not splash_screen:
            logger.warning("启动进度窗口无效，直接启动主窗口")
            main_window = main_window_callback()
            main_window.show()
            return
        
        # 显示启动进度窗口
        splash_screen.show()
        splash_screen.raise_()
        splash_screen.activateWindow()
        
        def init_step(step_num, message, callback):
            """初始化步骤"""
            splash_screen.update_progress(step_num, message)
            QTimer.singleShot(100, callback)  # 短暂延迟以显示进度
        
        def step1():
            """步骤1: 初始化基本配置"""
            init_step(1, "正在加载配置文件...", step2)
        
        def step2():
            """步骤2: 创建主窗口"""
            init_step(2, "正在创建主窗口...", step3)
        
        def step3():
            """步骤3: 初始化控制器"""
            init_step(3, "正在初始化控制器...", step4)
        
        def step4():
            """步骤4: 加载界面组件"""
            init_step(4, "正在加载界面组件...", step5)
        
        def step5():
            """步骤5: 准备Matrix编辑器"""
            init_step(5, "正在准备Matrix编辑器...", step6)
        
        def step6():
            """步骤6: 初始化报告系统"""
            init_step(6, "正在初始化报告系统...", step7)
        
        def step7():
            """步骤7: 完成启动"""
            try:
                splash_screen.update_progress(7, "即将完成启动...")
                
                # 创建主窗口
                main_window = main_window_callback()
                
                # 短暂延迟后显示主窗口并关闭启动画面
                def show_main_window():
                    try:
                        main_window.show()
                        main_window.raise_()
                        main_window.activateWindow()
                        splash_screen.finish_startup()
                        logger.info("主窗口显示完成")
                    except Exception as e:
                        logger.error(f"显示主窗口时出错: {e}")
                        splash_screen.close()
                
                QTimer.singleShot(300, show_main_window)
                
            except Exception as e:
                logger.error(f"最后启动步骤出错: {e}")
                splash_screen.close()
        
        # 开始启动流程
        QTimer.singleShot(100, step1)
        
    except Exception as e:
        logger.error(f"显示启动进度时出错: {e}")
        # 如果出错，直接启动主窗口
        try:
            main_window = main_window_callback()
            main_window.show()
        except Exception as inner_e:
            logger.error(f"备用启动方式也失败: {inner_e}")