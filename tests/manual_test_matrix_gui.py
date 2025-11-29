import sys
import os

# 添加项目根目录到Python路径，确保能正确导入模块和加载配置
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

# 设置工作目录为项目根目录，确保配置文件能被正确加载
os.chdir(project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox

# 确保在导入其他模块之前初始化配置
from src.core.config_manager import config_manager

from src.features.matrix.service.matrix_service import MatrixService
from src.features.matrix.view.matrix_dialog import MatrixDialog
from src.features.matrix.controller.matrix_controller import MatrixController


class ManualTestWindow(QMainWindow):
    """手动测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matrix模块手动测试")
        self.setGeometry(100, 100, 300, 200)

        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建测试按钮
        self.test_matrix_dialog_btn = QPushButton("测试Matrix对话框")
        self.test_matrix_controller_btn = QPushButton("测试Matrix控制器")
        self.test_matrix_service_btn = QPushButton("测试Matrix服务")

        # 连接按钮事件
        self.test_matrix_dialog_btn.clicked.connect(self.test_matrix_dialog)
        self.test_matrix_controller_btn.clicked.connect(self.test_matrix_controller)
        self.test_matrix_service_btn.clicked.connect(self.test_matrix_service)

        # 添加按钮到布局
        layout.addWidget(self.test_matrix_dialog_btn)
        layout.addWidget(self.test_matrix_controller_btn)
        layout.addWidget(self.test_matrix_service_btn)

    def test_matrix_dialog(self):
        """测试Matrix对话框"""
        try:
            service = MatrixService()
            dialog = MatrixDialog(None, service)
            dialog.exec_()
            QMessageBox.information(self, "成功", "Matrix对话框测试完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试Matrix对话框时出错: {str(e)}")
    
    def test_matrix_controller(self):
        """测试Matrix控制器"""
        try:
            controller = MatrixController(None)
            dialog = MatrixDialog(None, controller.service)
            dialog.exec_()
            QMessageBox.information(self, "成功", "Matrix控制器测试完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试Matrix控制器时出错: {str(e)}")
    
    def test_matrix_service(self):
        """测试Matrix服务"""
        try:
            service = MatrixService()
            # 测试添加列
            service.add_column("测试列")
            # 测试添加行
            service.add_row()
            # 测试导入spec方法存在
            has_import_method = hasattr(service, 'import_from_spec')
            # 测试设置选择组功能
            service.set_selected_groups(["Group1"], [{"row": 0, "col": 5}])
            QMessageBox.information(self, "成功", f"Matrix服务测试完成\n导入方法存在: {has_import_method}\n选择组设置: 成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试Matrix服务时出错: {str(e)}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = ManualTestWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()