import sys
import os
from PyQt5.QtWidgets import QApplication

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.matrix.view.matrix_dialog import MatrixDialog

def test_matrix_gui():
    """测试Matrix GUI的表头样式"""
    app = QApplication(sys.argv)
    
    # 创建Matrix对话框
    dialog = MatrixDialog()
    dialog.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_matrix_gui()